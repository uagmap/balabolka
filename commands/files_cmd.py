from __future__ import annotations

from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config.env import get_env


async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	try:
		share_dir = get_env("NETWORK_ALARM_DIR")
		path = Path(share_dir)
		if not path.exists():
			await update.message.reply_text(f"Path does not exist: {share_dir}")
			return
		items = [p.name for p in path.iterdir()]
		listings = "\n".join(items)
		await update.message.reply_text(listings)
	except Exception as e:
		await update.message.reply_text(f"Error listing files: {e}")


