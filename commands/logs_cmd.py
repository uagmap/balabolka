# commands to view logs (Admin only)
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import os
import tempfile

from services.auth import require_admin
from services.logger import get_logger


@require_admin
async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View logs (admin only command) - combine all daily log files into one and send"""
    logger = get_logger()
    
    # Get the logs directory
    log_dir = logger.log_file.parent
    
    # Find all log files (current + backups) from the past month
    all_log_files = []
    now = datetime.now()
    
    # Check current log file
    if logger.log_file.exists() and logger.log_file.stat().st_size > 0:
        all_log_files.append(logger.log_file)
    
    # Check backup files (format: activity.log.YYYY-MM-DD)
    for i in range(31):  # Check up to 31 days back
        backup_date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        backup_file = log_dir / f"activity.log.{backup_date}"
        if backup_file.exists():
            all_log_files.append(backup_file)
    
    if not all_log_files:
        await update.message.reply_text("Логи пусты.")
        return
    
    # Combine all log files into one temporary file, sorted by date (newest first)
    all_log_files.sort(key=lambda x: x.stat().st_mtime, reverse=False)
    
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.log', delete=False) as temp_file:
        temp_file.write(f"# Combined logs from {len(all_log_files)} files (past 30 days)\n")
        temp_file.write(f"# Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for log_file in all_log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        temp_file.write(f"{'='*50}\n")
                        temp_file.write(f"# File: {log_file.name}\n")
                        temp_file.write(f"{'='*50}\n")
                        temp_file.write(content)
                        temp_file.write("\n\n")
            except Exception as e:
                temp_file.write(f"# Error reading {log_file.name}: {e}\n\n")
        
        temp_filename = temp_file.name
    
    try:
        # Send the combined log file
        await update.message.reply_document(
            document=open(temp_filename, 'rb'), 
            filename=f"activity_logs_{now.strftime('%Y-%m-%d')}.log"
        )
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_filename)
        except:
            pass