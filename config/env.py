import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv as _load_dotenv


def load_env() -> None:
	"""Load environment variables from config/.env (preferred) or project .env."""
	project_root = Path(__file__).resolve().parent.parent
	config_env = project_root / "config" / ".env"
	root_env = project_root / ".env"

	if config_env.exists():
		_load_dotenv(dotenv_path=config_env)
	elif root_env.exists():
		_load_dotenv(dotenv_path=root_env)
	else:
		# Fallback to default discovery for uncommon run setups.
		_load_dotenv()


def get_env(name: str, default: Optional[str] = None) -> str:
	value = os.getenv(name, default)
	if value is None or value == "":
		raise RuntimeError(f"Missing environment variable: {name}")
	return value


def get_env_optional(name: str, default: Optional[str] = None) -> Optional[str]:
	value = os.getenv(name)
	if value is None or value == "":
		return default
	return value


def get_env_int(name: str, default: int) -> int:
	value = get_env_optional(name)
	if value is None:
		return default
	try:
		return int(value)
	except ValueError:
		print(f"Invalid integer for {name}={value!r}; using default {default}")
		return default


def get_env_float(name: str, default: float) -> float:
	value = get_env_optional(name)
	if value is None:
		return default
	try:
		return float(value)
	except ValueError:
		print(f"Invalid float for {name}={value!r}; using default {default}")
		return default


def get_env_bool(name: str, default: bool) -> bool:
	value = get_env_optional(name)
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


def get_alarm_path() -> Path:
	alarm_dir = get_env("NETWORK_ALARM_DIR")
	return Path(alarm_dir) / "alarm.wav" # Change this to change output file name
