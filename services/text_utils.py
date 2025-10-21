from telegram import InputMediaAudio, Update
from services.tts import is_cyrillic_text, generate_all_voices

async def validate_and_send_tts(update: Update, context, text: str):
    """Validate that text is Cyrillic, generate TTS for all speakers and send as media group"""

    if not is_cyrillic_text(text):
        await update.message.reply_text("⚠️ Поддерживается только кириллица. Отправьте текст на русском или /cancel.")
        return False
    
    try:
        wav_files = generate_all_voices(text)
        media_group = [InputMediaAudio(file, filename=f"{voice}.wav") for voice, file in wav_files.items()]
        await update.message.reply_media_group(media=media_group)
        context.user_data['alarm_speakers'] = {voice: file.getvalue() for voice, file in wav_files.items()} #store for mounting later
        return True
    except Exception as e:
        await update.message.reply_text(f"Ошибка TTS: {e}\nВведите текст снова или /cancel.")
        return False