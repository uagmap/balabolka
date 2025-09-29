from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text("pong")

 