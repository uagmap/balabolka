from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(
		"/ping - health check\n"
		"/files - list filenames in the shared directory\n"
		"/tts - start TTS, then send Russian text (use /cancel to exit)\n"
		"/alarm - режим установки балаболки\n"
	)

 