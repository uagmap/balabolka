from __future__ import annotations

import json
from logging import Logger
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from telegram import Update

# Path to log file
LOG_FILE = Path(__file__).parent.parent / "activity.log"

class Logger:
    def __init__(self, log_file: Path = LOG_FILE):
        self.log_file = log_file

        # If file doesn't exist - create one
        if not self.log_file.exists():
            self.log_file.touch()

    def _get_user_info(self, update: Update) -> Dict[str, Any]:
        """Extracts user info from Update."""
        user = update.effective_user
        if user:
            return {
                "username": user.username or "unknown",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        return {"username": "unknown"}

    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Writes a log entry into the file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Failed to write log entry: {e}")  #need to fix this bcuz if bot run on a server then I'll never know there is an error 
            

    def _clean_old_logs(self) -> None:
        """Remove logs entries older than 30 days."""
        try:
            if not self.log_file.exists():
                return

            delta_date = datetime.now() - timedelta(days=30)

            with open(self.log_file, 'r+', encoding='utf-8') as f:
                log_lines = f.readlines()
                f.seek(0)
                f.truncate()

                for line in log_lines:
                    try:
                        log_entry = json.loads(line.strip())
                        log_date = datetime.strptime(log_entry['timestamp'], "%Y-%m-%d %H:%M")
                        if log_date >= delta_date:
                            f.write(line)     #keep entries        

                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        except Exception as e:
            print(f"Failed to clean old logs: {e}")

    def log_alarm_mounted(self, update: Update, alarm_text: str) -> None:
        """Log when user mounts an alarm"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "call": "alarm_mounted",
            "user": self._get_user_info(update)["username"],
            "text": alarm_text
        }
        self._write_log_entry(entry)

    def log_alarm_disabled(self, update: Update) -> None:
        """Log when user disables an alarm"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "call": "alarm_disabled",
            "user": self._get_user_info(update)["username"]
        }
        self._write_log_entry(entry)

    def log_custom(self, action: str, details: Dict[str, any], update: Optional[Update] = None) -> None:
        """Log custom action"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "call": action,
            "user": self._get_user_info(update)["username"],
            "details": details
        }
        self._write_log_entry(entry)

    def read_recent_logs(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Read recent logs, on read - clean old logs"""

        self._clean_old_logs()

        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Take the last N lines (or all if fewer than N)
            recent_lines  = lines[-limit:] if len(lines) > limit else lines
            
            logs = []
            for line in recent_lines:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
            return logs
        except Exception as e:
            print(f"Failed to read logs: {e}")
            return []


# Global instance of a class
# This keeps only one instance of the class in the entire application
_logger = Logger()

def get_logger() -> Logger:
    return _logger