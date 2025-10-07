from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from services.auth import _get_auth_manager, require_admin


@require_admin
async def whitelist_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add user to whitelist"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Использование: /whitelist_add @username\n"
            "Или: /whitelist_add username"
        )
        return
    username = context.args[0].lstrip('@').lower()
    auth = _get_auth_manager()

    if auth._add_user(username):
        await update.message.reply_text(f"✅ Пользователь @{username} добавлен в белый список.")
    else:
        await update.message.reply_text(f"ℹ️ Пользователь @{username} уже в белом списке.")


@require_admin
async def whitelist_remove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove user from whitelist"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Использование: /whitelist_remove @username\n"
            "Или: /whitelist_remove username"
        )
        return

    username = context.args[0].lstrip('@').lower()
    auth = _get_auth_manager()

    # Prevent admin from removing themselves
    if auth._is_admin(username):
        await update.message.reply_text("⛔ Нельзя удалить администратора из белого списка.")
        return

    # Remove user from whitelist
    if auth._remove_user(username):
        await update.message.reply_text(f"✅ Пользователь @{username} удален из белого списка.")
    else:
        await update.message.reply_text(f"❌ Пользователь @{username} не найден в белом списке.")


@require_admin
async def whitelist_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all whitelisted users"""
    auth = _get_auth_manager()
    users = auth._list_users()

    await update.message.reply_text(f"Список пользователей:\n\n{users}")

