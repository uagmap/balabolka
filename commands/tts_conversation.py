from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

from services.text_utils import validate_and_send_tts

# Conversation states
TTS_AWAIT_TEXT = 1

# Entry point for /tts command: state machine
async def tts_entry_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	await update.message.reply_text("Отправьте текст по-русски (кириллица), чтобы сгенерировать речь. Можно использовать знак + для обозначения ударения перед гласными. \n\nКоманда /cancel — отмена.")
	return TTS_AWAIT_TEXT

# What to do when text is received
async def tts_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	text = update.message.text or ""
	ok = await validate_and_send_tts(update, context, text)
	if ok:
		#clear user data after completion
		context.user_data.clear()
		return ConversationHandler.END
	return TTS_AWAIT_TEXT

# Conversation fallback on /cancel
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

 