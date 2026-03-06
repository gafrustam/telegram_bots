import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, CallbackQuery, Message

import database
import speaking as speaking_module
from formatter import format_admin_stats, format_user_stats
from keyboards import (
    ADMIN_BTN,
    LISTENING_BTN,
    MENU_BTN,
    PART1_BTN,
    PART2_BTN,
    PART3_BTN,
    READING_BTN,
    SPEAKING_BTN,
    STATS_BTN,
    WRITING_BTN,
    main_menu_keyboard,
    speaking_menu_keyboard,
)
from states import SpeakingStates

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/ielts2_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    handlers=[_log_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("BOT_TOKEN", ""))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)
dp.include_router(speaking_module.router)

ADMIN_USERNAME = (os.getenv("ADMIN_USERNAME") or "").lstrip("@").lower()
_admin_ids: set[int] = set()


def _is_admin(user_id: int = 0, username: str | None = None) -> bool:
    if user_id and user_id in _admin_ids:
        return True
    return bool(ADMIN_USERNAME) and bool(username) and username.lower() == ADMIN_USERNAME


# ── Texts ────────────────────────────────────────────────

WELCOME_TEXT = (
    "🎓 <b>IELTS Trainer</b>\n"
    "\n"
    "Добро пожаловать! Это твой персональный тренажёр для подготовки к экзамену IELTS.\n"
    "\n"
    "<b>IELTS</b> (International English Language Testing System) — один из самых "
    "популярных международных экзаменов по английскому языку. Признаётся "
    "более чем в 140 странах для поступления в университеты, эмиграции и работы.\n"
    "\n"
    "Экзамен состоит из <b>4 разделов</b> (в порядке прохождения):\n"
    "\n"
    "🎧 <b>Listening</b> — ~30 мин, 40 вопросов\n"
    "Слушаешь аудиозаписи и отвечаешь на вопросы.\n"
    "\n"
    "📖 <b>Reading</b> — 60 мин, 40 вопросов\n"
    "Читаешь 3 текста и отвечаешь на вопросы.\n"
    "\n"
    "✍️ <b>Writing</b> — 60 мин, 2 задания\n"
    "Task 1 (описание/письмо) + Task 2 (эссе).\n"
    "\n"
    "🗣 <b>Speaking</b> — 11–14 мин, 3 части\n"
    "Устная беседа с экзаменатором.\n"
    "\n"
    "Оценка — от 0 до 9 (полубаллы). Для большинства университетов: Band 6.0–7.0.\n"
    "\n"
    "👇 <b>Выбери раздел для тренировки</b>"
)

SPEAKING_INTRO = (
    "🗣 <b>Speaking — Тренажёр</b>\n"
    "\n"
    "Speaking состоит из 3 частей:\n"
    "\n"
    "<b>Part 1 — Interview</b>\n"
    "Вопросы на личные темы: дом, работа, хобби (~4–5 мин)\n"
    "\n"
    "<b>Part 2 — Long Turn</b>\n"
    "Монолог 2 минуты по карточке (~3–4 мин)\n"
    "\n"
    "<b>Part 3 — Discussion</b>\n"
    "Абстрактная дискуссия по теме Part 2 (~4–5 мин)\n"
    "\n"
    "AI-оценка по 4 критериям IELTS: Fluency & Coherence, Lexical Resource, "
    "Grammatical Range & Accuracy, Pronunciation.\n"
    "\n"
    "👇 Выбери часть:"
)

COMING_SOON_TEXTS = {
    "listening": (
        "🎧 <b>Listening — скоро</b>\n\n"
        "Этот раздел сейчас в разработке.\n"
        "Здесь ты сможешь:\n"
        "• Слушать аудиозаписи в стиле IELTS\n"
        "• Отвечать на вопросы (MC, form completion и др.)\n"
        "• Получать разбор ошибок\n\n"
        "<i>Следи за обновлениями! 🚀</i>"
    ),
    "reading": (
        "📖 <b>Reading — скоро</b>\n\n"
        "Этот раздел сейчас в разработке.\n"
        "Здесь ты сможешь:\n"
        "• Читать тексты IELTS-уровня (General Training)\n"
        "• Отвечать на вопросы (T/F/NG, matching, MC)\n"
        "• Получать анализ ошибок с объяснениями\n\n"
        "<i>Следи за обновлениями! 🚀</i>"
    ),
    "writing": (
        "✍️ <b>Writing — скоро</b>\n\n"
        "Этот раздел сейчас в разработке.\n"
        "Здесь ты сможешь:\n"
        "• Практиковать Task 1 (письмо) и Task 2 (эссе)\n"
        "• Получать оценку по 4 критериям IELTS\n"
        "• Видеть конкретные ошибки и исправления\n\n"
        "<i>Следи за обновлениями! 🚀</i>"
    ),
}

ACTIVE_SPEAKING = {
    SpeakingStates.part1_answering.state,
    SpeakingStates.part2_preparing.state,
    SpeakingStates.part2_answering.state,
    SpeakingStates.part3_answering.state,
    SpeakingStates.assessing.state,
}


# ── /start ───────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if sid := data.get("db_session_id"):
        await database.fail_session(sid)
    await state.clear()

    user = message.from_user
    await database.upsert_user(user.id, user.username, user.first_name, user.last_name)

    is_adm = _is_admin(user.id, user.username)
    if is_adm:
        _admin_ids.add(user.id)

    await message.answer(WELCOME_TEXT, parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard(is_admin=is_adm))


# ── /help ────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Справка</b>\n\n"
        "<b>Команды:</b>\n"
        "  /start — Главное меню\n"
        "  /stats — Твоя статистика\n"
        "  /cancel — Отменить текущую сессию\n\n"
        "<b>Советы для Speaking:</b>\n"
        "  • Говорите в тихом месте\n"
        "  • Держите телефон близко ко рту\n"
        "  • Отвечайте развёрнуто\n"
        "  • Part 1: ~20–30 сек на вопрос\n"
        "  • Part 2: ~2 минуты монолог\n"
        "  • Part 3: ~30–60 сек на вопрос",
        parse_mode=ParseMode.HTML,
    )


# ── /cancel ──────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if sid := data.get("db_session_id"):
        await database.fail_session(sid)
    await state.clear()
    is_adm = _is_admin(message.from_user.id, message.from_user.username)
    await message.answer(
        "Сессия отменена. Выбери раздел:",
        reply_markup=main_menu_keyboard(is_admin=is_adm),
    )


# ── ⬅️ Главное меню ──────────────────────────────────────

@router.message(F.text == MENU_BTN)
async def handle_menu_btn(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current in ACTIVE_SPEAKING:
        data = await state.get_data()
        if sid := data.get("db_session_id"):
            await database.fail_session(sid)
    await state.clear()
    is_adm = _is_admin(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 Главное меню\n\n👇 Выбери раздел:",
        reply_markup=main_menu_keyboard(is_admin=is_adm),
    )


# ── Section buttons ──────────────────────────────────────

@router.message(F.text == SPEAKING_BTN)
async def handle_speaking_btn(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current in ACTIVE_SPEAKING:
        await message.answer(
            "⚠️ У тебя идёт активная сессия Speaking.\n"
            "Нажми ⬅️ Главное меню, чтобы выйти, или продолжи тренировку."
        )
        return

    data = await state.get_data()
    if sid := data.get("db_session_id"):
        await database.fail_session(sid)
    await state.clear()

    await database.log_section_tap(message.from_user.id, "speaking")
    await state.set_state(SpeakingStates.choosing_part)
    await message.answer(SPEAKING_INTRO, parse_mode=ParseMode.HTML, reply_markup=speaking_menu_keyboard())


@router.message(F.text == LISTENING_BTN)
async def handle_listening_btn(message: Message) -> None:
    await database.log_section_tap(message.from_user.id, "listening")
    await message.answer(COMING_SOON_TEXTS["listening"], parse_mode=ParseMode.HTML)


@router.message(F.text == READING_BTN)
async def handle_reading_btn(message: Message) -> None:
    await database.log_section_tap(message.from_user.id, "reading")
    await message.answer(COMING_SOON_TEXTS["reading"], parse_mode=ParseMode.HTML)


@router.message(F.text == WRITING_BTN)
async def handle_writing_btn(message: Message) -> None:
    await database.log_section_tap(message.from_user.id, "writing")
    await message.answer(COMING_SOON_TEXTS["writing"], parse_mode=ParseMode.HTML)


# ── Stats ─────────────────────────────────────────────────

@router.message(F.text == STATS_BTN)
@router.message(Command("stats"))
async def handle_stats(message: Message) -> None:
    if not database.is_available():
        await message.answer("⚠️ База данных недоступна.")
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    stats = await database.get_user_stats(message.from_user.id)
    text = format_user_stats(stats, message.from_user.first_name)
    await message.answer(text, parse_mode=ParseMode.HTML)


# ── Admin ─────────────────────────────────────────────────

@router.message(F.text == ADMIN_BTN)
@router.message(Command("admin"))
async def handle_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id, message.from_user.username):
        return
    if not database.is_available():
        await message.answer("⚠️ База данных недоступна.")
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    stats = await database.get_admin_stats()
    await message.answer(format_admin_stats(stats), parse_mode=ParseMode.HTML)


# ── Catch-all ────────────────────────────────────────────

@router.message(F.voice)
async def handle_unexpected_voice(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нажми /start, чтобы начать.")
    else:
        await message.answer("Сейчас я не жду голосового сообщения. Воспользуйся меню ниже.")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_unexpected_text(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нажми /start, чтобы начать.")


# ── Bot setup ─────────────────────────────────────────────

async def _set_commands() -> None:
    await bot.set_my_commands([
        BotCommand(command="start",  description="Главное меню"),
        BotCommand(command="stats",  description="Моя статистика"),
        BotCommand(command="help",   description="Справка"),
        BotCommand(command="cancel", description="Отменить сессию"),
    ])


async def main() -> None:
    logger.info("Starting IELTS Trainer bot...")
    await database.init_db()

    if ADMIN_USERNAME:
        uid = await database.get_user_id_by_username(ADMIN_USERNAME)
        if uid:
            _admin_ids.add(uid)
            logger.info("Admin loaded: %s (id=%d)", ADMIN_USERNAME, uid)

    await _set_commands()
    try:
        await dp.start_polling(bot)
    finally:
        await database.close_db()


if __name__ == "__main__":
    asyncio.run(main())
