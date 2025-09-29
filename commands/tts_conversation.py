from __future__ import annotations

from telegram import InputFile, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

from services.tts import generate_tts_bytes, is_cyrillic_text


# Conversation states
TTS_AWAIT_TEXT = 1


async def tts_entry_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	await update.message.reply_text("Отправьте текст по-русски (кириллица), чтобы сгенерировать речь. Команда /cancel — отмена.")
	return TTS_AWAIT_TEXT


async def tts_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	text = update.message.text or ""
	if not is_cyrillic_text(text):
		await update.message.reply_text("Поддерживается только кириллица. Отправьте текст на русском или /cancel.")
		return TTS_AWAIT_TEXT
	try:
		wav_bytes = generate_tts_bytes(text)
		filename = "tts.wav"
		await update.message.reply_document(document=InputFile(wav_bytes, filename=filename), caption="Готово")
		return ConversationHandler.END
	except Exception as e:
		await update.message.reply_text(f"Ошибка TTS: {e}")
		return TTS_AWAIT_TEXT


async def tts_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	await update.message.reply_text("Отменено. Возвращаемся в обычный режим.")
	return ConversationHandler.END


def build_conversation_handler() -> ConversationHandler:
	return ConversationHandler(
		entry_points=[CommandHandler("tts", tts_entry_cmd)],
		states={
			TTS_AWAIT_TEXT: [
				MessageHandler(filters.TEXT & (~filters.COMMAND), tts_receive_text),
			],
		},
		fallbacks=[CommandHandler("cancel", tts_cancel_cmd)],
	)

 