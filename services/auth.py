from __future__ import annotations

import json
from pathlib import Path
from typing import Set, Optional
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from config.env import get_env

whitelist_file = Path.cwd() / "whitelist.json"

class AuthManager:
    def __init__(self):
        self.whitelist: Set[str] = set()
        self.admin_username: Optional[str] = None
        self._load_whitelist()

    def _load_whitelist(self) -> None:
        """load whitelist from JSON file"""
        if whitelist_file.exists():
            try:
                with open (whitelist_file, "r") as f:
                    data = json.load(f)
                    self.whitelist = set(data.get('users', []))
            except Exception as e:
                print(f"Error loading whitelist: {e}")
                self.whitelist = set()
        else:
            # Initialize whitelist with admin
            admin = self._get_admin_username()
            if admin:
                admin = admin.lstrip('@').lower()
                self.whitelist = {admin}
                self._save_whitelist()
    
    def _save_whitelist(self) -> None:
        """Save whitelist to JSON"""
        try:
            with open (whitelist_file, "w", encoding='utf-8') as f:
                json.dump({"users": list(self.whitelist)}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving file: {e}")

    def _get_admin_username(self) -> Optional[str]:
        """Get admin username from env."""
        if self.admin_username is None:
            try:
                self.admin_username = get_env("ADMIN_USERNAME")
            except RuntimeError as e:
                print(f"Error: ADMIN_USERNAME is not set in .env")
                return None
        return self.admin_username

    def _is_admin(self, username: Optional[str]) -> bool:
        """Check if user is admin."""
        if username is None:
            return False

        admin = self._get_admin_username()
        
        if admin is None:
            return False

        username = username.lstrip('@').lower()
        admin = admin.lstrip('@').lower()

        return username == admin

    def _add_user(self, username: Optional[str]) -> bool:
        """Add user to whitelist. Return True if successful."""
        username = username.lstrip('@').lower()

        if username in self.whitelist:
            return False

        self.whitelist.add(username)
        self._save_whitelist()
        return True

    def _remove_user(self, username: Optional[str]) -> bool:
        """Remove user from whitelist. Returns True if successfull."""
        if username is None:
            return False
            
        username = username.lstrip('@').lower()

        if username in self.whitelist:
            self.whitelist.discard(username)
            self._save_whitelist()
            return True
        return False


    def _list_users(self) -> list[str]:
        """Return list of whitelisted users"""
        return list(self.whitelist)


    def _is_whitelisted(self, username: Optional[str]) -> bool:
        """Checks if user is in white list"""
        if username is None: 
            return False

        username = username.lstrip('@').lower()
        return username in self.whitelist



# Global instance of a class
# This keeps only one instance of the class in the entire application
_auth_manager = AuthManager()

def _get_auth_manager() -> AuthManager:
    return _auth_manager


# Wrappers
def require_auth(func):
    """Decorator to require user to be in white list"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        auth = _get_auth_manager()
        user = update.effective_user
        username = user.username if user else None

        if not auth._is_whitelisted(username):
            await update.message.reply_text("⛔ Доступ запрещен Ухади")
            return
        
        return await func(update, context, *args, **kwargs)

    return wrapper


def require_admin(func):
    """Decorator to require user to be admin"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        auth = _get_auth_manager()
        user = update.effective_user
        username = user.username if user else None

        if not auth._is_admin(username):
            await update.message.reply_text("⛔ Доступ запрещен Ухади")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper