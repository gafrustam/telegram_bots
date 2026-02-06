import asyncio
import logging
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, Message

from assessor import assess_speaking
from formatter import format_assessment, format_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()
router = Router()
dp.include_router(router)

WELCOME_TEXT = (
    "🎓 <b>IELTS Speaking Assessor</b>\n"
    "\n"
    "Я оцениваю ваш IELTS Speaking по официальным\n"
    "критериям и даю рекомендации по улучшению.\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n"
    "<b>Как пользоваться:</b>\n"
    "  1.  Запишите голосовое сообщение\n"
    "       на английском языке\n"
    "  2.  Отправьте его в этот чат\n"
    "  3.  Получите детальную оценку\n"
    "\n"
    "<b>Критерии оценки:</b>\n"
    "  • Fluency & Coherence\n"
    "  • Lexical Resource\n"
    "  • Grammatical Range & Accuracy\n"
    "  • Pronunciation\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n"
    "Оценка производится по официальным IELTS\n"
    "Band Descriptors с учётом рекомендаций\n"
    "для сертифицированных экзаменаторов.\n"
    "\n"
    "🎤 <b>Отправьте голосовое сообщение, чтобы начать!</b>"
)

HELP_TEXT = (
    "📖 <b>Справка</b>\n"
    "\n"
    "🎤 <b>Голосовое сообщение</b> — отправьте аудио\n"
    "на английском, чтобы получить оценку.\n"
    "\n"
    "Минимальная длительность — <b>10 секунд</b>.\n"
    "Рекомендуемая — <b>1–3 минуты</b>.\n"
    "\n"
    "<b>Советы для лучшей оценки:</b>\n"
    "  • Говорите в тихом месте\n"
    "  • Держите телефон близко ко рту\n"
    "  • Отвечайте на вопрос из IELTS Speaking\n"
    "    (Part 2 или Part 3 подходят лучше всего)\n"
    "\n"
    "<b>Команды:</b>\n"
    "  /start  —  Приветствие\n"
    "  /help   —  Эта справка"
)

PROCESSING_TEXT = (
    "🎧 <b>Анализирую ваше сообщение...</b>\n"
    "\n"
    "<i>Слушаю произношение, оцениваю грамматику,\n"
    "лексику и связность речи. Это может занять\n"
    "некоторое время.</i>"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)


@router.message(F.voice | F.audio)
async def handle_voice(message: Message) -> None:
    status_msg = await message.answer(PROCESSING_TEXT, parse_mode=ParseMode.HTML)

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file = await bot.get_file(file_id)

        with tempfile.TemporaryDirectory() as tmp_dir:
            ogg_path = os.path.join(tmp_dir, "voice.oga")
            await bot.download_file(file.file_path, ogg_path)

            result = await assess_speaking(ogg_path)

        response_text = format_assessment(result)

        if len(response_text) <= 4096:
            await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)
        else:
            await status_msg.delete()
            chunks = _split_message(response_text)
            for chunk in chunks:
                await message.answer(chunk, parse_mode=ParseMode.HTML)

    except Exception:
        logger.exception("Error processing voice message")
        await status_msg.edit_text(
            format_error("Не удалось обработать аудио. Попробуйте ещё раз."),
            parse_mode=ParseMode.HTML,
        )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message) -> None:
    await message.answer(
        "🎤 Отправьте <b>голосовое сообщение</b> на английском языке,\n"
        "и я оценю ваш Speaking по критериям IELTS.",
        parse_mode=ParseMode.HTML,
    )


def _split_message(text: str, limit: int = 4096) -> list[str]:
    """Split a long message into chunks at line boundaries."""
    chunks = []
    current = ""
    for line in text.split("\n"):
        candidate = current + "\n" + line if current else line
        if len(candidate) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def _set_bot_commands() -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Справка по использованию"),
    ])


async def main() -> None:
    logger.info("Starting IELTS Speaking Assessor bot...")
    await _set_bot_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
