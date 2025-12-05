import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from telegram import Update
from typing import Optional

# Path to log file
LOG_FILE = Path.cwd() / "logs/activity.log"

class AppLogger:
    def __init__(self, log_file: Path = LOG_FILE):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True) # create subfolder if needed
        self.logger = logging.getLogger("Balabolka")
        self.logger.setLevel(logging.INFO) # all logs in this program are info

        handler = TimedRotatingFileHandler(
            filename=str(self.log_file),
            when="D",       # daily rotation
            interval=1,    # every day
            backupCount=30,  # keep 30 days of logs
            encoding="utf-8",
            utc=False,
        )
        formatter = logging.Formatter(
            fmt="%(asctime)s\t%(levelname)s\t%(message)s",
            datefmt="%Y-%m-%d %H:%M",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _get_username(self, update: Optional[Update]) -> str:
        """Extracts username info from Update."""
        user = update.effective_user if update else None
        return (user.username) if user else "unknown"

    def log_alarm_mounted(self, update: Update, alarm_text: str) -> None:
        """Log when user mounts an alarm"""
        username = self._get_username(update)
        self.logger.info(f"alarm_mounted user={username} text={alarm_text}")

    def log_alarm_disabled(self, update: Update) -> None:
        """Log when user disables an alarm"""
        username = self._get_username(update)
        self.logger.info(f"alarm_disabled user={username}")

    def log_access_denied(self, update: Update, command: str) -> None:
        """Log unauthorized command calls"""
        username = self._get_username(update)
        self.logger.warning(f"access_denied user={username} command={command}")

    def log_exception(self, update: Optional[Update], message: str) -> None:
        """Log custom message"""
        username = self._get_username(update)
        self.logger.error(f"exception user={username} message={message}")

# Global instance of a class
# This keeps only one instance of the class in the entire application
_logger = AppLogger()

def get_logger() -> AppLogger:
    return _logger