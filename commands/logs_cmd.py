# commands to view logs (Admin only)
from __future__ import annotations

import json

from telegram import Update
from telegram.ext import ContextTypes

from services.auth import require_admin
from services.logger import get_logger


@require_admin
async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View logs (admin only command)"""
    logger = get_logger()

    limit  = 50

    if context.args and len(context.args) > 0:
        try:
            limit = int(context.args[0])
            limit = min(limit, 100) #cap at 100
        except ValueError:
            await update.message.reply_text("Неверный формат использования.")
            return

    logs = logger.read_recent_logs(limit)

    if not logs: 
        await update.message.reply_text("Логи пусты.")
        return

    # send as unformatted JSON, one per line
    message = "\n".join(json.dumps(log, ensure_ascii=False) for log in logs)
    await update.message.reply_text(message)
