import os
from smbclient import open_file, remove, register_session, listdir, stat as smb_stat

def smb_register_session() -> None:
	"""Register an SMB session to the given path with credentials in .env"""
	server = _extract_server(os.getenv("NETWORK_ALARM_DIR"))
	smb_user = os.getenv("SMB_USERNAME")
	smb_pass = os.getenv("SMB_PASSWORD")
	register_session(server, username=smb_user, password=smb_pass)


def create_file(path: str, data: bytes) -> None:
	with open_file(path, mode="wb") as f:
		f.write(data)


def delete_file(path: str) -> None:
	remove(path)


def list_directory(path: str) -> list[str]:
	"""Return list of entries in a given directory path"""
	return listdir(path)


def file_exists(path: str) -> bool:
	"""Return True if the SMB path exists (file or directory)."""
	try:
		smb_stat(path)
		return True
	except Exception:
		try:
			# try re-register and retry
			smb_register_session() 
			smb_stat(path)
			return True
		except Exception:
			return False


def _extract_server(share: str) -> str:
	s = share.lstrip("/")
	# Now s looks like "server/share"
	parts = s.split("/", 1)
	return parts[0] if parts and parts[0] else ""