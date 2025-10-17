from telegram import Update
from telegram.ext import ContextTypes


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text("Используйте /help для команд.")

 