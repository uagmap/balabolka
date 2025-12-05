import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv as _load_dotenv


def load_env() -> None:
	"""Load environment variables from a .env file if present."""
	_load_dotenv()


def get_env(name: str, default: Optional[str] = None) -> str:
	value = os.getenv(name, default)
	if value is None or value == "":
		raise RuntimeError(f"Missing environment variable: {name}")
	return value


def get_alarm_path() -> Path:
	alarm_dir = get_env("NETWORK_ALARM_DIR")
	return Path(alarm_dir) / "alarm.wav" # Change this to change output file name