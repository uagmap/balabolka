from __future__ import annotations

from telegram import BotCommand
from telegram.ext import Application


async def set_commands_menu(application: Application) -> None:
	commands = [
		BotCommand("help", "Show help"),
		BotCommand("ping", "Health check"),
		BotCommand("files", "List files in shared folder"),
		BotCommand("tts", "Generate TTS from text"),
		BotCommand("alarm", "Режим установки балаболки"),
	]
	await application.bot.set_my_commands(commands)


