from telegram import Update
from telegram.ext import ContextTypes


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(
		"/ping - проверка работы бота\n"
		"/files - показать файлы в сетевой папке списком\n"
		"/tts - сгенерировать аудиофайл оповещения (без установки)\n"
		"/alarm - режим установки балаболки\n"
	)

 