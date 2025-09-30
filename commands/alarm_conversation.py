from __future__ import annotations

from pathlib import Path

from telegram import InputFile, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

from config.env import get_env, get_alarm_path
from services.tts import generate_tts_bytes, is_cyrillic_text

# Conversation states
ALARM_CHECK_STATE = 1
ALARM_AWAIT_TEXT = 2
ALARM_VALIDATE = 3

def alarm_exists() -> bool:
	return get_alarm_path().exists()

async def alarm_entry_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Entry point of conversation, handle /alarm command"""
	try: 
		if alarm_exists():
			# alarm already exists, offer to disable
			keyboard = [["Отключить балаболку", "Отмена"]]
			reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
			await update.message.reply_text(
				"⚠️ Балаболка сейчас установлена в сетевой папке.\n\n"
				"Хотите отключить балаболку?", reply_markup=reply_markup
			)
			return ALARM_CHECK_STATE
		else: 
			#no alarm exists, offer to create
			await update.message.reply_text(
				"📢 Создание текста оповещения\n\n"
				"Отправьте полный текст сообщения на русском языке.\n"
				"Используйте знак '+' для обозначения ударения перед гласной (например: оповещ+ение).\n\n"
				"/cancel — отмена."
			)
			return ALARM_AWAIT_TEXT
	except Exception as e:
		await update.message.reply_text(f"Ошибка при проверке балаболки: {e}")
		return ConversationHandler.END



async def alarm_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""What to do on received text body"""
	text = update.message.text or ""
	if not is_cyrillic_text(text):
		await update.message.reply_text("⚠️ Поддерживается только кириллица. Отправьте текст на русском или /cancel для отмены.")
		return ALARM_AWAIT_TEXT
	try: 
		#store user text for re-iteration
		context.user_data['alarm_text'] = text
		#generate TTS file
		wav_bytes = generate_tts_bytes(text)
		context.user_data['alarm_wav'] = wav_bytes.getvalue() #store for mounting later

		#send audiofile to user for validation
		filename = "alarm_test.wav"
		await update.message.reply_document(
			document=InputFile(wav_bytes, filename=filename), 
			caption="🔊 Прослушайте сообщение и утвердите качество оповещения."
		)

		#offer validation options
		keyboard = [["Утвердить", "Изменить текст", "Отмена"]]
		reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
		await update.message.reply_text(
			"Выберите действие:\n"
			"• Утвердить — разместить файл в сетевой папке\n"
			"• Изменить текст — отправить новый текст, изменить ударения\n"
			"• Отмена — отменить операцию",
			reply_markup=reply_markup
		)

		return ALARM_VALIDATE

	except Exception as e:
		await update.message.reply_text(f"Ошибка при генерации TTS файла: {e}")
		return ConversationHandler.END


async def alarm_validate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Validate the alarm audio file"""
	choice = update.message.text or ""

	if choice == "Утвердить":
		#mount the alarm
		try:
			alarm_path = get_alarm_path()
			wav_data = context.user_data['alarm_wav']

			if not wav_data:
				await update.message.reply_text("⚠️ Данные для установки файла не найдены. Отменено.", reply_markup=ReplyKeyboardRemove())
				return ConversationHandler.END

			with alarm_path.open("wb") as f:
				f.write(wav_data)

			await update.message.reply_text(
				f"✅ Балаболка установлена!\n\n"
				"Файл размещен в сетевой папке.\n\n"
				"Отключить балаболку: /alarm",
				reply_markup=ReplyKeyboardRemove()
			)

			#clear user data after completion
			context.user_data.clear()
			return ConversationHandler.END
	
		except Exception as e:
			await update.message.reply_text(f"Ошибка при установке TTS файла: {e}")
			return ConversationHandler.END
		
	elif choice == "Изменить текст":
		#return to await text state
		await update.message.reply_text(
			"Отправьте новый текст сообщения на русском языке.\n"
			"Используйте знак '+' для обозначения ударения перед гласной.",
			reply_markup=ReplyKeyboardRemove()
		)
		return ALARM_AWAIT_TEXT

	else:
		#cancel
		await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
		context.user_data.clear()
		return ConversationHandler.END


async def alarm_disable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Disable the alarm, called by markup keyboard text"""
	text = update.message.text or ""

	if text == "Отключить балаболку":
		try:
			alarm_path = get_alarm_path()
			if alarm_path.exists():
				alarm_path.unlink() #delete this file
				await update.message.reply_text(
					"✅ Балаболка отключена, файл удален из сетевой папки.",
					reply_markup=ReplyKeyboardRemove()
				)
			else:
				await update.message.reply_text(
					"Файл балаболки не найден в сетевой папке :(",
					reply_markup=ReplyKeyboardRemove()
				)

		except Exception as e:
			await update.message.reply_text(f"Ошибка при удалении файла: {e}", reply_markup=ReplyKeyboardRemove())
			return ConversationHandler.END
	else:
		#user chose to cancel or incorrect input
		await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
		return ConversationHandler.END



async def alarm_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Exit the conversation mode on /cancel command"""
	await update.message.reply_text("Выход из режима балаболки", reply_markup=ReplyKeyboardRemove())
	context.user_data.clear()
	return ConversationHandler.END


def build_alarm_conversation_handler() -> ConversationHandler:
	return ConversationHandler(
		entry_points=[CommandHandler("alarm", alarm_entry_cmd)],
		states={
			ALARM_CHECK_STATE: [
				MessageHandler(filters.TEXT & (~filters.COMMAND), alarm_disable),
			],
			ALARM_AWAIT_TEXT: [
				MessageHandler(filters.TEXT & (~filters.COMMAND), alarm_receive_text),
			],
			ALARM_VALIDATE: [
				MessageHandler(filters.TEXT & (~filters.COMMAND), alarm_validate),
			],
		},
		fallbacks=[CommandHandler("cancel", alarm_cancel_cmd)],
	)