import os

from config.env import load_env, get_env
from services.smb import smb_register_session
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


def main() -> None:
	load_env()
	smb_register_session()
	token = get_env("API_KEY_TELEGRAM")

	builder = Application.builder().token(token)

	# Optional transport settings.
	base_url = os.getenv("TELEGRAM_BASE_URL")
	base_file_url = os.getenv("TELEGRAM_BASE_FILE_URL")
	proxy_url = os.getenv("TELEGRAM_PROXY_URL")
	updates_proxy_url = os.getenv("TELEGRAM_UPDATES_PROXY_URL") or proxy_url

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

	app = builder.build()
	app.add_handler(CommandHandler("start", start_cmd))
	app.add_handler(CommandHandler("help", help_cmd))
	app.add_handler(CommandHandler("ping", ping_cmd))
	app.add_handler(CommandHandler("files", files_cmd))
	app.add_handler(CommandHandler("whitelist_add", whitelist_add_cmd))
	app.add_handler(CommandHandler("whitelist_remove", whitelist_remove_cmd))
	app.add_handler(CommandHandler("whitelist_list", whitelist_list_cmd))
	app.add_handler(CommandHandler("logs", logs_cmd))
	
	# Conversation for /tts
	app.add_handler(build_conversation_handler())
	
	# Conversation for /alarm
	app.add_handler(build_alarm_conversation_handler())

	# Set menu commands on startup
	app.post_init = set_commands_menu

	app.run_polling()


if __name__ == "__main__":
	main()
