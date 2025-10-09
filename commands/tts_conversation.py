from __future__ import annotations

from telegram import InputFile, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

from services.tts import generate_all_voices, is_cyrillic_text

# Conversation states
TTS_AWAIT_TEXT = 1


async def tts_entry_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	await update.message.reply_text("Отправьте текст по-русски (кириллица), чтобы сгенерировать речь. Можно использовать знак + для обозначения ударения перед гласными. \n\nКоманда /cancel — отмена.")
	return TTS_AWAIT_TEXT


async def tts_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	text = update.message.text or ""
	if not is_cyrillic_text(text):
		await update.message.reply_text("Поддерживается только кириллица. Отправьте текст на русском или /cancel.")
		return TTS_AWAIT_TEXT
	try:
		wav_files = generate_all_voices(text)

		for voice, file in wav_files.items():
			filename = f"tts_{voice}.wav"
			await update.message.reply_document(document=InputFile(file, filename=filename), caption=f"Голос: {voice}")
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

 