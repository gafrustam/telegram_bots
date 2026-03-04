import asyncio
import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import database
from transcriber import transcribe

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/voice_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

GREETING = (
    "Привет, это бот от @gafrustam, который распознает голосовые сообщения. "
    "Просто форвардни сюда чьё-то голосовое сообщение и получи его в текстовом виде. 🎙️➡️📝"
)

EXT_BY_MIME = {
    "audio/ogg": ".ogg",
    "audio/oga": ".oga",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        user = update.message.from_user
        logger.info("user_id=%d username=%s /start", user.id, user.username)
        await database.upsert_user(user.id, user.username, user.first_name, user.last_name)
        await update.message.reply_text(GREETING)


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg:
        return

    user = msg.from_user
    user_id = user.id if user else None
    uid_tag = f"user_id={user_id} " if user_id else ""

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

    logger.info("%sreceived media file_id=%s mime=%s", uid_tag, file_id, mime)

    if user:
        await database.upsert_user(user.id, user.username, user.first_name, user.last_name)

    tg_file = await context.bot.get_file(file_id)
    ext = EXT_BY_MIME.get(mime, ".ogg")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        temp_path = tmp.name

    try:
        await tg_file.download_to_drive(temp_path)
        text = await transcribe(temp_path, mime, user_id=user_id)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    if text and text.strip():
        provider = os.getenv("AI_PROVIDER", "openai").lower()
        await database.save_transcription(
            user_id=user_id or 0,
            chat_id=msg.chat_id,
            file_id=file_id,
            mime_type=mime,
            text=text.strip(),
            provider=provider,
        )
        await msg.reply_text(text.strip(), disable_web_page_preview=True)
    else:
        logger.warning("%sempty transcription result", uid_tag)


async def post_init(application: Application) -> None:
    await database.init_db()
    logger.info("Voice messages bot started")


async def post_shutdown(application: Application) -> None:
    await database.close_db()


def main() -> None:
    app = (
        Application.builder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE, handle_media))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
