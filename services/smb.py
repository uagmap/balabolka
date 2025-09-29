from __future__ import annotations

import os
import subprocess

from config.env import get_env


def connect_smb() -> None:
	smb_user = os.getenv("SMB_USERNAME")
	smb_pass = os.getenv("SMB_PASSWORD")
	if not smb_user or not smb_pass:
		return
	share_root = get_env("NETWORK_ALARM_DIR")

	# build a cmd command to connect to the smb share (net use)
	cmd = [
		"cmd",
		"/c",
		"net",
		"use",
		share_root,
		f"/user:{smb_user}",
		smb_pass,
		"/persistent:no",
	]
	try:
		subprocess.run(cmd, check=False, capture_output=True)
	except Exception:
		pass


