from __future__ import annotations

from config.env import load_env, get_env
from services.smb import connect_smb
from telegram.ext import Application, CommandHandler

from commands.start_cmd import start_cmd
from commands.help_cmd import help_cmd
from commands.ping_cmd import ping_cmd
from commands.files_cmd import files_cmd
from commands.tts_conversation import build_conversation_handler


from menus.commands_menu import set_commands_menu


def main() -> None:
	load_env()
	connect_smb()
	token = get_env("API_KEY_TELEGRAM")

	app = Application.builder().token(token).build()
	app.add_handler(CommandHandler("start", start_cmd))
	app.add_handler(CommandHandler("help", help_cmd))
	app.add_handler(CommandHandler("ping", ping_cmd))
	app.add_handler(CommandHandler("files", files_cmd))

	# Conversation for /tts
	app.add_handler(build_conversation_handler())
	#app.add_handler(CommandHandler("tts_confirm", tts_confirm_cmd))
	#app.add_handler(CommandHandler("tts_cancel", tts_cancel_cmd))

	# Set menu commands on startup
	app.post_init = set_commands_menu

	app.run_polling()


if __name__ == "__main__":
	main()
