import asyncio
import contextlib
import os
import time

from config.env import (
	load_env,
	get_env,
	get_env_optional,
	get_env_int,
	get_env_bool,
)
from services.smb import smb_register_session
from telegram.error import NetworkError
from telegram.ext import Application, CommandHandler

from commands.start_cmd import start_cmd
from commands.help_cmd import help_cmd
from commands.ping_cmd import ping_cmd
from commands.files_cmd import files_cmd
from commands.tts_conversation import build_conversation_handler
from commands.alarm_conversation import build_alarm_conversation_handler
from commands.whitelist_cmd import whitelist_add_cmd, whitelist_remove_cmd, whitelist_list_cmd
from commands.logs_cmd import logs_cmd

from menus.commands_menu import set_commands_menu


def smb_register_session_with_retry() -> None:
	retry_delay = get_env_int("SMB_RETRY_DELAY_SECONDS", 10)
	max_attempts = get_env_int("SMB_RETRY_MAX_ATTEMPTS", -1)
	attempt = 0

	while True:
		try:
			smb_register_session()
			return
		except Exception as exc:
			attempt += 1
			print(f"SMB session registration failed (attempt {attempt}): {exc}")
			if max_attempts >= 0 and attempt >= max_attempts:
				raise
			time.sleep(retry_delay)


def build_network_error_handler():
	threshold = get_env_int("NETWORK_ERROR_RESTART_THRESHOLD", 8)
	window_seconds = get_env_int("NETWORK_ERROR_RESTART_WINDOW_SECONDS", 120)
	state = {"count": 0, "window_start": 0.0}

	async def _handler(update, context) -> None:
		err = context.error
		if isinstance(err, NetworkError):
			now = time.time()
			if state["window_start"] <= 0 or (now - state["window_start"]) > window_seconds:
				state["window_start"] = now
				state["count"] = 1
			else:
				state["count"] += 1

			print(
				f"NetworkError observed ({state['count']}/{threshold}) within {window_seconds}s window: {err}"
			)

			if state["count"] >= threshold:
				print("NetworkError threshold reached, exiting process to trigger container restart.")
				os._exit(1)

	return _handler


async def polling_monitor_loop(application: Application) -> None:
	enabled = get_env_bool("POLLING_MONITOR_ENABLED", True)
	if not enabled:
		print("POLLING_MONITOR_HEARTBEAT disabled")
		return

	interval_seconds = max(5, get_env_int("POLLING_MONITOR_INTERVAL_SECONDS", 20))
	restart_threshold = max(1, get_env_int("POLLING_MONITOR_RESTART_THRESHOLD", 3))
	log_every_cycles = 2

	consecutive_failures = 0
	cycle = 0
	print(
		f"POLLING_MONITOR_HEARTBEAT startup interval_seconds={interval_seconds} restart_threshold={restart_threshold}"
	)

	while True:
		cycle += 1
		updater = application.updater
		updater_running = bool(updater and updater.running)
		polling_task = getattr(updater, "_Updater__polling_task", None) if updater else None
		polling_alive = bool(updater_running and polling_task and not polling_task.done())
		check_ok = False

		if polling_alive:
			try:
				await application.bot.get_me()
				check_ok = True
			except Exception as exc:
				print(f"Polling monitor: Telegram API check failed: {exc}")
		else:
			detail = ""
			if polling_task is not None and polling_task.done() and not polling_task.cancelled():
				try:
					task_error = polling_task.exception()
				except Exception as exc:
					task_error = exc
				if task_error is not None:
					detail = f" error={task_error}"
			print(f"Polling monitor: updater polling task not alive.{detail}")

		if check_ok:
			if consecutive_failures > 0:
				print(f"Polling monitor recovered after {consecutive_failures} failed checks.")
			consecutive_failures = 0
		else:
			consecutive_failures += 1
			print(
				f"Polling monitor: failed checks {consecutive_failures}/{restart_threshold}"
			)

		if cycle % log_every_cycles == 0:
			print(
				f"POLLING_MONITOR_HEARTBEAT cycle={cycle} updater_running={updater_running} polling_alive={polling_alive} failed_checks={consecutive_failures}"
			)

		if consecutive_failures >= restart_threshold:
			print(
				"Polling monitor threshold reached, exiting process to trigger container restart."
			)
			os._exit(1)

		await asyncio.sleep(interval_seconds)


async def post_init(application: Application) -> None:
	await set_commands_menu(application)
	application.bot_data["_polling_monitor_task"] = asyncio.create_task(
		polling_monitor_loop(application),
		name="polling-monitor",
	)


async def post_stop(application: Application) -> None:
	task = application.bot_data.pop("_polling_monitor_task", None)
	if task is not None:
		task.cancel()
		with contextlib.suppress(asyncio.CancelledError):
			await task


def main() -> None:
	load_env()
	smb_register_session_with_retry()
	token = get_env("API_KEY_TELEGRAM")

	builder = Application.builder().token(token)

	# Optional transport settings.
	base_url = get_env_optional("TELEGRAM_BASE_URL")
	base_file_url = get_env_optional("TELEGRAM_BASE_FILE_URL")
	proxy_url = get_env_optional("TELEGRAM_PROXY_URL")
	updates_proxy_url = get_env_optional("TELEGRAM_UPDATES_PROXY_URL", proxy_url)

	if base_url:
		builder = builder.base_url(base_url)
	if base_file_url:
		builder = builder.base_file_url(base_file_url)

	if proxy_url:
		if hasattr(builder, "proxy"):
			builder = builder.proxy(proxy_url)
		elif hasattr(builder, "proxy_url"):
			builder = builder.proxy_url(proxy_url)

	if updates_proxy_url:
		if hasattr(builder, "get_updates_proxy"):
			builder = builder.get_updates_proxy(updates_proxy_url)
		elif hasattr(builder, "get_updates_proxy_url"):
			builder = builder.get_updates_proxy_url(updates_proxy_url)

	# Stable defaults for long polling through sidecar proxy.
	if hasattr(builder, "get_updates_connect_timeout"):
		builder = builder.get_updates_connect_timeout(8.0)
	if hasattr(builder, "get_updates_read_timeout"):
		builder = builder.get_updates_read_timeout(25.0)
	if hasattr(builder, "get_updates_write_timeout"):
		builder = builder.get_updates_write_timeout(8.0)
	if hasattr(builder, "get_updates_pool_timeout"):
		builder = builder.get_updates_pool_timeout(5.0)

	app = builder.build()
	app.add_handler(CommandHandler("start", start_cmd))
	app.add_handler(CommandHandler("help", help_cmd))
	app.add_handler(CommandHandler("ping", ping_cmd))
	app.add_handler(CommandHandler("files", files_cmd))
	app.add_handler(CommandHandler("whitelist_add", whitelist_add_cmd))
	app.add_handler(CommandHandler("whitelist_remove", whitelist_remove_cmd))
	app.add_handler(CommandHandler("whitelist_list", whitelist_list_cmd))
	app.add_handler(CommandHandler("logs", logs_cmd))
	app.add_error_handler(build_network_error_handler())

	# Conversation for /tts
	app.add_handler(build_conversation_handler())

	# Conversation for /alarm
	app.add_handler(build_alarm_conversation_handler())

	# Set menu commands and start internal polling monitor on startup.
	app.post_init = post_init
	app.post_stop = post_stop

	# Keep retrying bootstrap when network/proxy is temporarily unavailable.
	app.run_polling(
		bootstrap_retries=-1,
		timeout=10,
		poll_interval=0.0,
	)


if __name__ == "__main__":
	main()
