from __future__ import annotations

from pathlib import Path

from telegram import InputFile, InputMediaAudio, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters

from config.env import get_env, get_alarm_path
from services.tts import AVAILABLE_VOICES, generate_all_voices, generate_tts_bytes, is_cyrillic_text
from services.auth import require_auth
from services.logger import get_logger
# Conversation states
ALARM_CHECK_STATE = 1
ALARM_AWAIT_TEXT = 2
ALARM_VALIDATE = 3

def alarm_exists() -> bool:
	return get_alarm_path().exists()

@require_auth
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
		#generate TTS files
		files = generate_all_voices(text)
		context.user_data['alarm_speakers'] = {voice: file.getvalue() for voice, file in files.items()} #store for mounting later

		#send all audiofiles to user for selection and validation
		#TODO: change this to be sent as single message!!!
		"""for voice, file in files.items():
			filename = f"alarm_{voice}.wav"
			await update.message.reply_document(
				document=InputFile(file, filename=filename), 
				caption=f"Голос: {voice}"
			)"""

		media_group = [InputMediaAudio(file, filename=f"{voice}.wav") for voice, file in files.items()]
		await update.message.reply_media_group(media=media_group)

		#offer validation options
		keyboard = [
			['aidar', 'baya', 'kseniya'],
			['xenia', 'eugene'],
			["Изменить текст", "Отмена"]
			]
		reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
		await update.message.reply_text(
			"Прослушайте все голоса и выберите действие:\n"
			"• Нажмите на имя голоса — утвердить и установить балаболку с этим голосом\n"
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

	if choice in AVAILABLE_VOICES:
		#mount the alarm with selected voice
		try:
			alarm_path = get_alarm_path()
			alarm_speakers = context.user_data.get('alarm_speakers')
			alarm_text = context.user_data.get('alarm_text', '')

			if choice not in alarm_speakers:
				await update.message.reply_text("⚠️ Данные для установки файла не найдены. Отменено.", reply_markup=ReplyKeyboardRemove())
				return ConversationHandler.END

			wav_data = alarm_speakers[choice]
			with alarm_path.open("wb") as f:
				f.write(wav_data)

			# Log the alarm mounting
			logger = get_logger()
			logger.log_alarm_mounted(update, f"{alarm_text} (голос: {choice})")

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
				
				# Log the alarm disabling
				logger = get_logger()
				logger.log_alarm_disabled(update)
				
				await update.message.reply_text(
					"✅ Балаболка отключена, файл удален из сетевой папки.",
					reply_markup=ReplyKeyboardRemove()
				)
			else:
				await update.message.reply_text(
					"Файл балаболки не найден в сетевой папке :(",
					reply_markup=ReplyKeyboardRemove()
				)

			return ConversationHandler.END
			
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