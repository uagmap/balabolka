from telegram import BotCommand
from telegram.ext import Application


async def set_commands_menu(application: Application) -> None:
	commands = [
		BotCommand("help", "Показать команды"),
		BotCommand("ping", "Проверка работы бота"),
		BotCommand("files", "Показать файлы в сетевой папке списком"),
		BotCommand("tts", "Сгенерировать аудиофайл оповещения"),
		BotCommand("alarm", "Режим установки балаболки"),
	]
	await application.bot.set_my_commands(commands)


