from telegram import Update
from telegram.ext import ContextTypes

from config.env import get_env
from services.smb import list_directory, file_exists


async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	try:
		share_dir = get_env("NETWORK_ALARM_DIR")
		if not file_exists(share_dir):
			await update.message.reply_text(f"Path does not exist: {share_dir}")
			return
		items = list_directory(share_dir)
		listings = "\n".join(items)
		await update.message.reply_text(listings)
	except Exception as e:
		await update.message.reply_text(f"Error listing files: {e}")


