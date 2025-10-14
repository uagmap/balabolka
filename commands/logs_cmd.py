# commands to view logs (Admin only)
from telegram import Update
from telegram.ext import ContextTypes

from services.auth import require_admin
from services.logger import get_logger


@require_admin
async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View logs (admin only command)"""
    logger = get_logger()

    if not logger.log_file.exists():
        await update.message.reply_text("Логи пусты.")
        return

    # send the log file directly
    await update.message.reply_document(document=open(logger.log_file, 'rb'), filename="activity.log")