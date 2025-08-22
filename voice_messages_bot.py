import os
import asyncio
import tempfile
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

telegram_token = os.environ["TELEGRAM_AUDIO_MESSAGE_BOT_TOKEN"]
openai_api_key = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=openai_api_key)

GREETING = "Привет, это бот от @gafrustam, который распознает голосовые сообщения. Просто форвардни сюда чьё-то голосовое сообщение и получи его в текстовом виде. 🎙️➡️📝"

EXT_BY_MIME = {
    "audio/ogg": ".ogg",
    "audio/oga": ".oga",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(GREETING)

async def transcribe_file(path: str):
    def _transcribe():
        with open(path, "rb") as f:
            r = client.audio.transcriptions.create(model="whisper-1", file=f)
            return getattr(r, "text", None)
    return await asyncio.to_thread(_transcribe)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message
        if not msg:
            return

        file_id = None
        mime = None

        if msg.voice:
            file_id = msg.voice.file_id
            mime = msg.voice.mime_type or "audio/ogg"
        elif msg.audio:
            file_id = msg.audio.file_id
            mime = msg.audio.mime_type or "audio/mpeg"
        elif msg.video_note:
            file_id = msg.video_note.file_id
            mime = "video/mp4"
        else:
            return

        tg_file = await context.bot.get_file(file_id)
        ext = EXT_BY_MIME.get(mime, ".ogg")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            temp_path = tmp.name

        await tg_file.download_to_drive(temp_path)
        text = await transcribe_file(temp_path)

        try:
            os.remove(temp_path)
        except OSError:
            pass

        if text and text.strip():
            await msg.reply_text(text.strip(), disable_web_page_preview=True)
    except Exception:
        pass

def main():
    app = Application.builder().token(telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE, handle_media))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
