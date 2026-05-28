from __future__ import annotations

import asyncio
import contextlib
import os
import time
from typing import Any, Optional

from telegram import Update
from telegram.error import NetworkError
from telegram.ext import Application, ContextTypes, TypeHandler
from telegram.request import HTTPXRequest

from config.env import get_env_bool, get_env_int

_TASK_KEY = "_polling_monitor_task"
_POLLING_REQUEST_STATE = {
	"last_start": 0.0,
	"last_success": 0.0,
	"last_error": "",
	"last_error_at": 0.0,
	"request_count": 0,
}


def _now_monotonic() -> float:
	return time.monotonic()


def _mark_get_updates_start() -> None:
	_POLLING_REQUEST_STATE["last_start"] = _now_monotonic()
	_POLLING_REQUEST_STATE["request_count"] += 1


def _mark_get_updates_success() -> None:
	_POLLING_REQUEST_STATE["last_success"] = _now_monotonic()
	_POLLING_REQUEST_STATE["last_error"] = ""
	_POLLING_REQUEST_STATE["last_error_at"] = 0.0


def _mark_get_updates_error(exc: Exception | str) -> None:
	_POLLING_REQUEST_STATE["last_error"] = str(exc)
	_POLLING_REQUEST_STATE["last_error_at"] = _now_monotonic()


def _seconds_since(value: float) -> Optional[float]:
	if value <= 0:
		return None
	return max(0.0, _now_monotonic() - value)


class MonitoredGetUpdatesRequest(HTTPXRequest):
	async def do_request(
		self,
		url: str,
		method: str,
		request_data=None,
		read_timeout=None,
		write_timeout=None,
		connect_timeout=None,
		pool_timeout=None,
	):
		is_get_updates = "/getUpdates" in url
		if is_get_updates:
			_mark_get_updates_start()

		try:
			status_code, payload = await super().do_request(
				url=url,
				method=method,
				request_data=request_data,
				read_timeout=read_timeout,
				write_timeout=write_timeout,
				connect_timeout=connect_timeout,
				pool_timeout=pool_timeout,
			)
			if is_get_updates:
				if 200 <= status_code < 300:
					_mark_get_updates_success()
				else:
					_mark_get_updates_error(f"getUpdates returned HTTP {status_code}")
			return status_code, payload
		except Exception as exc:
			if is_get_updates:
				_mark_get_updates_error(exc)
			raise


def build_get_updates_request(proxy_url: Optional[str]) -> MonitoredGetUpdatesRequest:
	return MonitoredGetUpdatesRequest(
		connection_pool_size=1,
		proxy=proxy_url,
		connect_timeout=8.0,
		read_timeout=25.0,
		write_timeout=8.0,
		pool_timeout=5.0,
		http_version="1.1",
	)


def apply_get_updates_transport(builder: Any, proxy_url: Optional[str]):
	custom_get_updates_request = False
	if hasattr(builder, "get_updates_request"):
		builder = builder.get_updates_request(build_get_updates_request(proxy_url))
		custom_get_updates_request = True
	elif proxy_url:
		if hasattr(builder, "get_updates_proxy"):
			builder = builder.get_updates_proxy(proxy_url)
		elif hasattr(builder, "get_updates_proxy_url"):
			builder = builder.get_updates_proxy_url(proxy_url)

	if not custom_get_updates_request:
		if hasattr(builder, "get_updates_connect_timeout"):
			builder = builder.get_updates_connect_timeout(8.0)
		if hasattr(builder, "get_updates_read_timeout"):
			builder = builder.get_updates_read_timeout(25.0)
		if hasattr(builder, "get_updates_write_timeout"):
			builder = builder.get_updates_write_timeout(8.0)
		if hasattr(builder, "get_updates_pool_timeout"):
			builder = builder.get_updates_pool_timeout(5.0)
		if hasattr(builder, "get_updates_http_version"):
			builder = builder.get_updates_http_version("1.1")

	return builder


async def observe_update_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	# Lightweight telemetry: helps diagnose "alive but not receiving updates" incidents.
	if update is None:
		return

	command = ""
	message = update.effective_message
	if message and message.text and message.text.startswith("/"):
		command = message.text.split(maxsplit=1)[0]

	if command:
		user = update.effective_user.username if update.effective_user else "unknown"
		print(f"Update observed: command={command} user={user} update_id={update.update_id}")


def attach_update_observer(app: Application) -> None:
	app.add_handler(TypeHandler(Update, observe_update_activity, block=False), group=-1)


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
	stale_seconds = max(30, get_env_int("POLLING_MONITOR_STALE_SECONDS", 120))
	startup_grace_seconds = max(stale_seconds, get_env_int("POLLING_MONITOR_STARTUP_GRACE_SECONDS", 180))
	log_every_cycles = 2
	started_at = _now_monotonic()

	consecutive_failures = 0
	cycle = 0
	print(
		f"POLLING_MONITOR_HEARTBEAT startup interval_seconds={interval_seconds} restart_threshold={restart_threshold} stale_seconds={stale_seconds}"
	)

	while True:
		cycle += 1
		updater = application.updater
		updater_running = bool(updater and updater.running)
		polling_task = getattr(updater, "_Updater__polling_task", None) if updater else None
		polling_alive = bool(updater_running and polling_task and not polling_task.done())
		check_ok = polling_alive
		get_updates_age = _seconds_since(_POLLING_REQUEST_STATE["last_success"])

		if not polling_alive:
			detail = ""
			if polling_task is not None and polling_task.done() and not polling_task.cancelled():
				try:
					task_error = polling_task.exception()
				except Exception as exc:
					task_error = exc
				if task_error is not None:
					detail = f" error={task_error}"
			print(f"Polling monitor: updater polling task not alive.{detail}")

		if get_updates_age is None:
			uptime = _now_monotonic() - started_at
			if uptime > startup_grace_seconds:
				check_ok = False
				print(
					f"Polling monitor: no successful getUpdates request seen for {uptime:.1f}s "
					f"(startup_grace={startup_grace_seconds}s)."
				)
		else:
			if get_updates_age > stale_seconds:
				check_ok = False
				last_error = _POLLING_REQUEST_STATE["last_error"] or "none"
				print(
					f"Polling monitor: getUpdates stale for {get_updates_age:.1f}s "
					f"(threshold={stale_seconds}s), last_error={last_error}"
				)

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
			updates_state = (
				f"get_updates_age={get_updates_age:.1f}s"
				if get_updates_age is not None
				else "get_updates_age=none"
			)
			print(
				f"POLLING_MONITOR_HEARTBEAT cycle={cycle} updater_running={updater_running} polling_alive={polling_alive} "
				f"{updates_state} failed_checks={consecutive_failures}"
			)

		if consecutive_failures >= restart_threshold:
			print(
				"Polling monitor threshold reached, exiting process to trigger container restart."
			)
			os._exit(1)

		await asyncio.sleep(interval_seconds)


async def start_polling_monitor(application: Application) -> None:
	application.bot_data[_TASK_KEY] = asyncio.create_task(
		polling_monitor_loop(application),
		name="polling-monitor",
	)


async def stop_polling_monitor(application: Application) -> None:
	task = application.bot_data.pop(_TASK_KEY, None)
	if task is not None:
		task.cancel()
		with contextlib.suppress(asyncio.CancelledError):
			await task
