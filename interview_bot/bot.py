"""
Interview Prep Bot — ежедневные алгоритмические задачи для подготовки к собеседованиям.
"""
import asyncio
import html
import logging
import os
import random
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    Message,
)

import database as db
from feedback import check_solution, translate_text
from keyboards import (
    LEVELS,
    after_test_keyboard,
    cancel_keyboard,
    level_keyboard,
    next_problem_keyboard,
    problem_keyboard,
    prog_language_keyboard,
    settings_bot_lang_keyboard,
    settings_keyboard,
    settings_lang_keyboard,
    settings_level_keyboard,
    wrong_answer_keyboard,
)
from problems_data import PROBLEMS
try:
    from problems_data_new import NEW_PROBLEMS
    PROBLEMS = PROBLEMS + NEW_PROBLEMS
except ImportError:
    pass
from states import ProblemStates, SetupStates, SettingsStates

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/interview_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler()],
)
log = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_TOKEN"]
MOSCOW_TZ = timezone(timedelta(hours=3))

# ─── Motivational quotes ──────────────────────────────────────────────────────

QUOTES_RU = [
    "«Каждый эксперт когда-то был новичком.» — Хелен Хейс",
    "«Программирование — это не про то, что ты знаешь, а про то, как ты думаешь.» — Steve McConnell",
    "«Лучший способ предсказать будущее — создать его.» — Алан Кей",
    "«Сложность — враг надёжности.» — Тони Хоар",
    "«Учиться — значит открывать то, что ты уже знал.» — Ричард Бах",
    "«Каждая строка кода — шаг к мастерству.»",
    "«Алгоритмы — это поэзия логики.»",
    "«Не бойся медленного прогресса. Бойся стоять на месте.» — китайская пословица",
    "«Ошибки — это плата за обучение.» — Генри Форд",
    "«Упорство побеждает всё.» — Вергилий",
    "«Хороший код пишется сердцем и головой одновременно.»",
    "«Решённая задача — это маленькая победа. Собери их тысячи.»",
    "«Умение решать задачи — это мышца. Чем больше тренируешься, тем сильнее она.»",
    "«Путь в тысячу миль начинается с одного шага.» — Лао-цзы",
    "«Сегодняшняя дисциплина — завтрашняя свобода.»",
]

QUOTES_EN = [
    '"Every expert was once a beginner." — Helen Hayes',
    '"Programming is not about what you know; it\'s about what you can figure out." — Chris Pine',
    '"The best way to predict the future is to create it." — Alan Kay',
    '"Complexity is the enemy of reliability." — Tony Hoare',
    '"Talk is cheap. Show me the code." — Linus Torvalds',
    '"First, solve the problem. Then, write the code." — John Johnson',
    '"Clean code is not written by following a set of rules. It comes from a professional mind." — Robert C. Martin',
    '"A journey of a thousand miles begins with a single step." — Lao Tzu',
    '"Failure is the tuition you pay for success." — Walter Brunell',
    '"Persistence beats talent every time."',
]


def get_quote(lang: str) -> str:
    return random.choice(QUOTES_EN if lang == "en" else QUOTES_RU)


# ─── Text helpers ─────────────────────────────────────────────────────────────

LEVEL_EMOJI = {"intern": "👶", "junior": "🌱", "middle": "⚡", "senior": "🔥"}


async def format_problem_text(problem: dict, prog_language: str, lang: str = "ru") -> str:
    """Format a problem for sending to user. Translates if lang=en."""
    examples = problem["examples"]
    constraints = problem["constraints"]

    # Build text in Russian first
    examples_text = "\n".join(
        f"  <b>Пример {i+1}:</b>\n"
        f"  Вход: <code>{html.escape(str(ex['input']))}</code>\n"
        f"  Выход: <code>{html.escape(str(ex['output']))}</code>"
        + (f"\n  <i>{html.escape(str(ex['explanation']))}</i>" if ex.get("explanation") else "")
        for i, ex in enumerate(examples)
    )
    constraints_text = "\n".join(f"  • {html.escape(c)}" for c in constraints)

    emoji = LEVEL_EMOJI.get(problem["level"], "")
    level_label = LEVELS.get(problem["level"], problem["level"])

    text = (
        f"🧩 <b>{html.escape(problem['title'])}</b>\n"
        f"{emoji} Уровень: {level_label}\n\n"
        f"{html.escape(problem['description'])}\n\n"
        f"<b>Примеры:</b>\n{examples_text}\n\n"
        f"<b>Ограничения:</b>\n{constraints_text}\n\n"
        f"⌨️ Отправь своё решение на <b>{html.escape(prog_language)}</b> следующим сообщением."
    )

    if lang == "en":
        text = await translate_text(text)

    return text


# ─── Router ───────────────────────────────────────────────────────────────────

router = Router()


# ─── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user = db.get_user(message.from_user.id)
    db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    if user and db.is_setup_complete(message.from_user.id):
        await state.clear()
        lang = user.get("bot_language", "ru")
        if lang == "en":
            await message.answer(
                "👋 Welcome back! Use /settings to change preferences or just send code to continue solving.",
            )
        else:
            await message.answer(
                "👋 Привет! Ты уже в системе. Используй /settings для настроек "
                "или отправь решение текущей задачи.\n\n"
                "Хочешь получить новую задачу прямо сейчас?",
                reply_markup=next_problem_keyboard(),
            )
        return

    await state.clear()
    await message.answer(
        "👋 Привет! Я помогу тебе готовиться к техническим собеседованиям.\n\n"
        "Каждый день — новая алгоритмическая задача в стиле LeetCode, "
        "подсказки и разбор решений.\n\n"
        "Сначала выбери <b>язык программирования</b>, на котором будешь решать:",
        parse_mode=ParseMode.HTML,
        reply_markup=prog_language_keyboard(),
    )
    await state.set_state(SetupStates.choosing_prog_language)


# ─── Setup flow ───────────────────────────────────────────────────────────────

@router.callback_query(SetupStates.choosing_prog_language, F.data.startswith("setup_lang:"))
async def setup_lang_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":", 1)[1]
    await state.update_data(prog_language=lang)
    await callback.message.edit_text(
        f"✅ Язык: <b>{lang}</b>\n\n"
        "Теперь выбери <b>уровень сложности</b>:",
        parse_mode=ParseMode.HTML,
        reply_markup=level_keyboard("setup_level"),
    )
    await state.set_state(SetupStates.choosing_level)


@router.callback_query(SetupStates.choosing_level, F.data.startswith("setup_level:"))
async def setup_level_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split(":", 1)[1]
    data = await state.get_data()
    prog_language = data["prog_language"]

    db.update_user(callback.from_user.id, prog_language=prog_language, level=level)

    await callback.message.edit_text(
        f"🎯 Отлично! Уровень: <b>{LEVELS[level]}</b>, язык: <b>{prog_language}</b>\n\n"
        "⏳ Загружаю первую задачу...",
        parse_mode=ParseMode.HTML,
    )
    await state.clear()
    await send_next_problem(callback.message, callback.from_user.id, state)


# ─── Problem sending ──────────────────────────────────────────────────────────

async def send_next_problem(
    message: Message,
    user_id: int,
    state: FSMContext,
    edit: bool = False,
) -> None:
    user = db.get_user(user_id)
    if not user:
        return

    level = user["level"]
    prog_language = user["prog_language"]
    bot_lang = user.get("bot_language", "ru")

    problem = db.get_next_problem(user_id, level)
    if not problem:
        text = "🎉 Ты решил все задачи этого уровня! Попробуй повысить сложность в /settings."
        if bot_lang == "en":
            text = "🎉 You've solved all problems at this level! Try a higher difficulty in /settings."
        await message.answer(text)
        return

    record_id = db.record_problem_sent(user_id, problem["id"])
    await state.set_data({
        "problem_id": problem["id"],
        "record_id": record_id,
        "hints_revealed": 0,
        "solution_shown": False,
    })
    await state.set_state(ProblemStates.solving)

    text = await format_problem_text(problem, prog_language, bot_lang)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=problem_keyboard(0))


# ─── Hints & Surrender ────────────────────────────────────────────────────────

@router.callback_query(ProblemStates.solving, F.data.startswith("hint:"))
async def on_hint(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    hints_revealed = data.get("hints_revealed", 0)
    problem = db.get_problem(data["problem_id"])
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")

    if callback.data == "hint:1":
        hint_text = problem["hint1"]
        hints_revealed = 1
        prefix = "💡 <b>Подсказка 1:</b>\n"
    elif callback.data == "hint:2":
        hint_text = problem["hint2"]
        hints_revealed = 2
        prefix = "💡 <b>Подсказка 2:</b>\n"
    elif callback.data == "hint:3":
        hint_text = problem.get("hint3") or problem["solution_text"]
        hints_revealed = 3
        prefix = "💡 <b>Подсказка 3:</b>\n"
    else:  # verbal solution
        hint_text = problem["solution_text"]
        hints_revealed = 4
        prefix = "📖 <b>Решение (словами):</b>\n"

    if lang == "en":
        hint_text = await translate_text(hint_text)

    await state.update_data(hints_revealed=hints_revealed)
    db.update_problem_record(data["record_id"], hints_used=hints_revealed)

    await callback.message.answer(
        f"{prefix}{hint_text}",
        parse_mode=ParseMode.HTML,
        reply_markup=problem_keyboard(hints_revealed),
    )
    await callback.answer()


@router.callback_query(F.data == "surrender")
async def on_surrender(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    problem = db.get_problem(data["problem_id"])
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")

    solution = problem["solution_text"]
    if lang == "en":
        solution = await translate_text(solution)

    db.update_problem_record(data["record_id"], status="failed", solution_shown=1)

    quote = get_quote(lang)
    if lang == "en":
        msg = (
            f"📖 <b>Solution:</b>\n{solution}\n\n"
            f"💪 Don't give up — you'll get the next one!\n\n"
            f"<i>{quote}</i>"
        )
    else:
        msg = (
            f"📖 <b>Решение:</b>\n{solution}\n\n"
            f"💪 Не сдавайся — следующую задачу ты точно возьмёшь!\n\n"
            f"<i>{quote}</i>"
        )

    await callback.message.answer(msg, parse_mode=ParseMode.HTML, reply_markup=next_problem_keyboard())
    await state.set_data({**data, "solution_shown": True})
    await state.set_state(ProblemStates.solving)
    await callback.answer()


# ─── Solution checking ────────────────────────────────────────────────────────

@router.message(ProblemStates.solving, F.text)
async def on_solution(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    # If user clicked "next problem" callback, ignore stray text
    if not data.get("problem_id"):
        return

    problem = db.get_problem(data["problem_id"])
    user = db.get_user(message.from_user.id)
    lang = user.get("bot_language", "ru")
    prog_language = user["prog_language"]

    # Send typing action
    await message.bot.send_chat_action(message.chat.id, "typing")

    result = await check_solution(problem, message.text, prog_language)

    is_correct = result.get("is_correct")

    if is_correct is None:
        # API error
        await message.answer(result["verdict"])
        return

    quote = get_quote(lang)

    if is_correct:
        db.update_problem_record(data["record_id"], status="solved")
        improvement = result.get("improvement")

        if lang == "en":
            text = (
                f"✅ <b>Correct!</b>\n\n"
                f"{result['verdict']}\n\n"
                f"⏱ <b>Efficiency:</b> {result['efficiency']}"
            )
            if improvement:
                text += f"\n\n💡 <b>Tip:</b> {improvement}"
            text += f"\n\n<i>{quote}</i>"
        else:
            text = (
                f"✅ <b>Правильно!</b>\n\n"
                f"{result['verdict']}\n\n"
                f"⏱ <b>Эффективность:</b> {result['efficiency']}"
            )
            if improvement:
                text += f"\n\n💡 <b>Совет:</b> {improvement}"
            text += f"\n\n<i>{quote}</i>"

        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=next_problem_keyboard())
        await state.set_data({**data, "last_feedback": result})

    else:
        db.update_problem_record(data["record_id"], status="failed")

        if lang == "en":
            text = (
                f"❌ <b>Not quite right...</b>\n\n"
                f"{result['verdict']}\n\n"
                f"Would you like to see the failing test or give up?"
            )
        else:
            text = (
                f"❌ <b>Не совсем верно...</b>\n\n"
                f"{result['verdict']}\n\n"
                f"Хочешь посмотреть тест, на котором падает решение, или сдаться?"
            )

        await state.set_data({**data, "last_feedback": result})
        await state.set_state(ProblemStates.viewing_wrong)
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=wrong_answer_keyboard())


@router.callback_query(ProblemStates.viewing_wrong, F.data == "show_test")
async def on_show_test(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    feedback = data.get("last_feedback", {})
    problem = db.get_problem(data["problem_id"])
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")

    # Try feedback's failing_test first, then problem's built-in failing_test
    failing_test = feedback.get("failing_test") or problem.get("failing_test") or ""
    mistake = feedback.get("mistake") or ""

    if lang == "en":
        if failing_test:
            failing_test = await translate_text(failing_test)
        if mistake:
            mistake = await translate_text(mistake)
        text = (
            f"🧪 <b>Failing test case:</b>\n<code>{failing_test}</code>\n\n"
        )
        if mistake:
            text += f"🔍 <b>Hint about the error:</b> {mistake}\n\n"
        text += "❓ Can you spot the bug? Describe where you went wrong:"
    else:
        text = (
            f"🧪 <b>Тест, на котором падает решение:</b>\n<code>{failing_test}</code>\n\n"
        )
        if mistake:
            text += f"🔍 <b>Подсказка об ошибке:</b> {mistake}\n\n"
        text += "❓ Как ты думаешь, в чём ошибка? Перечисли, что пошло не так:"

    await state.set_state(ProblemStates.entering_errors)
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()


@router.message(ProblemStates.entering_errors, F.text)
async def on_errors_entered(message: Message, state: FSMContext) -> None:
    user = db.get_user(message.from_user.id)
    lang = user.get("bot_language", "ru")
    data = await state.get_data()

    if lang == "en":
        text = (
            "💪 Great analysis! Understanding your mistakes is half the battle.\n\n"
            "Ready to see the correct solution?"
        )
    else:
        text = (
            "💪 Отличный разбор! Понимание своих ошибок — это уже половина победы.\n\n"
            "Хочешь увидеть правильное решение?"
        )

    await state.set_state(ProblemStates.after_errors)
    await message.answer(text, reply_markup=after_test_keyboard())


@router.callback_query(ProblemStates.after_errors, F.data == "show_solution")
async def on_show_solution(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    problem = db.get_problem(data["problem_id"])
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")

    solution = problem["solution_text"]
    if lang == "en":
        solution = await translate_text(solution)

    quote = get_quote(lang)
    db.update_problem_record(data["record_id"], solution_shown=1)

    if lang == "en":
        text = f"✅ <b>Correct Solution:</b>\n{solution}\n\n<i>{quote}</i>"
    else:
        text = f"✅ <b>Правильное решение:</b>\n{solution}\n\n<i>{quote}</i>"

    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=next_problem_keyboard())
    await state.set_state(ProblemStates.solving)
    await callback.answer()


@router.callback_query(ProblemStates.after_errors, F.data == "retry")
async def on_retry_after_errors(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")
    problem = db.get_problem(data["problem_id"])
    prog_language = user["prog_language"]

    if lang == "en":
        text = "🔄 Give it another shot! Send your updated solution:"
    else:
        text = "🔄 Попробуй ещё раз! Отправь исправленное решение:"

    await state.set_state(ProblemStates.solving)
    await callback.message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=problem_keyboard(data.get("hints_revealed", 0)),
    )
    await callback.answer()


# ─── Next problem callback ────────────────────────────────────────────────────

@router.callback_query(F.data == "next_problem")
async def on_next_problem(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await send_next_problem(callback.message, callback.from_user.id, state)
    await callback.answer()


# ─── /settings ────────────────────────────────────────────────────────────────

@router.message(Command("settings"))
async def cmd_settings(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала напиши /start")
        return
    lang = user.get("bot_language", "ru")
    prog_language = user.get("prog_language", "Python")
    level = LEVELS.get(user.get("level", "junior"), "—")
    notif_time = user.get("notification_time", "12:00")

    if lang == "en":
        text = (
            f"⚙️ <b>Settings</b>\n\n"
            f"💻 Language: <b>{prog_language}</b>\n"
            f"📊 Level: <b>{level}</b>\n"
            f"⏰ Daily task time: <b>{notif_time} MSK</b>\n"
            f"🌍 Bot language: <b>English</b>\n\n"
            f"What would you like to change?"
        )
    else:
        text = (
            f"⚙️ <b>Настройки</b>\n\n"
            f"💻 Язык программирования: <b>{prog_language}</b>\n"
            f"📊 Уровень: <b>{level}</b>\n"
            f"⏰ Время задачи: <b>{notif_time} МСК</b>\n"
            f"🌍 Язык бота: <b>Русский</b>\n\n"
            f"Что хочешь изменить?"
        )
    await state.set_state(SettingsStates.main)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=settings_keyboard())


@router.callback_query(SettingsStates.main, F.data.startswith("settings:"))
async def on_settings_menu(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":", 1)[1]
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")

    if action == "prog_lang":
        await state.set_state(SettingsStates.changing_prog_language)
        text = "💻 Выбери новый язык программирования:" if lang == "ru" else "💻 Choose a programming language:"
        await callback.message.edit_text(text, reply_markup=settings_lang_keyboard())

    elif action == "level":
        await state.set_state(SettingsStates.changing_level)
        text = "📊 Выбери уровень сложности:" if lang == "ru" else "📊 Choose difficulty level:"
        await callback.message.edit_text(text, reply_markup=settings_level_keyboard())

    elif action == "time":
        await state.set_state(SettingsStates.changing_time)
        text = (
            "⏰ Введи время отправки ежедневной задачи в формате <b>ЧЧ:ММ</b> (по МСК).\n"
            "Например: <code>09:00</code> или <code>20:30</code>"
            if lang == "ru" else
            "⏰ Enter the daily task time in <b>HH:MM</b> format (Moscow time).\n"
            "Example: <code>09:00</code> or <code>20:30</code>"
        )
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=cancel_keyboard())

    elif action == "bot_lang":
        await state.set_state(SettingsStates.changing_bot_language)
        await callback.message.edit_text("🌍 Выбери язык / Choose language:", reply_markup=settings_bot_lang_keyboard())

    elif action == "stats":
        stats = db.get_user_stats(callback.from_user.id)
        solved = stats.get("solved", 0)
        failed = stats.get("failed", 0)
        sent = stats.get("sent", 0)
        total = solved + failed + sent
        if lang == "en":
            text = (
                f"📈 <b>Your Statistics</b>\n\n"
                f"✅ Solved: {solved}\n"
                f"❌ Failed: {failed}\n"
                f"📬 Sent (pending): {sent}\n"
                f"📊 Total: {total}"
            )
        else:
            text = (
                f"📈 <b>Твоя статистика</b>\n\n"
                f"✅ Решено: {solved}\n"
                f"❌ Не решено: {failed}\n"
                f"📬 Отправлено (в процессе): {sent}\n"
                f"📊 Всего: {total}"
            )
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=settings_keyboard())

    elif action == "back":
        await state.set_state(SettingsStates.main)
        await cmd_settings.__wrapped__(callback.message, state) if hasattr(cmd_settings, "__wrapped__") else None
        await callback.message.delete()
        await callback.message.answer(
            "⚙️ Настройки:" if lang == "ru" else "⚙️ Settings:",
            reply_markup=settings_keyboard(),
        )

    await callback.answer()


@router.callback_query(SettingsStates.changing_prog_language, F.data.startswith("set_prog_lang:"))
async def on_set_prog_lang(callback: CallbackQuery, state: FSMContext) -> None:
    lang_choice = callback.data.split(":", 1)[1]
    db.update_user(callback.from_user.id, prog_language=lang_choice)
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")
    await state.set_state(SettingsStates.main)
    text = f"✅ Язык изменён на <b>{lang_choice}</b>!" if lang == "ru" else f"✅ Language changed to <b>{lang_choice}</b>!"
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=settings_keyboard())
    await callback.answer()


@router.callback_query(SettingsStates.changing_bot_language, F.data.startswith("set_bot_lang:"))
async def on_set_bot_lang(callback: CallbackQuery, state: FSMContext) -> None:
    bot_lang = callback.data.split(":", 1)[1]
    db.update_user(callback.from_user.id, bot_language=bot_lang)
    await state.set_state(SettingsStates.main)
    if bot_lang == "en":
        text = "✅ Language changed to <b>English</b>!"
    else:
        text = "✅ Язык бота изменён на <b>Русский</b>!"
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=settings_keyboard())
    await callback.answer()


@router.callback_query(SettingsStates.changing_level, F.data.startswith("set_level:"))
async def on_set_level(callback: CallbackQuery, state: FSMContext) -> None:
    new_level = callback.data.split(":", 1)[1]
    db.update_user(callback.from_user.id, level=new_level)
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru")
    level_label = LEVELS[new_level]
    await state.clear()

    if lang == "en":
        text = f"✅ Level changed to <b>{level_label}</b>! Sending your first task at this level..."
    else:
        text = f"✅ Уровень изменён на <b>{level_label}</b>! Отправляю первую задачу нового уровня..."

    await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
    await callback.answer()
    # Send a new problem at the new level immediately
    await send_next_problem(callback.message, callback.from_user.id, state)


@router.message(SettingsStates.changing_time, F.text)
async def on_set_time(message: Message, state: FSMContext) -> None:
    time_str = message.text.strip()
    user = db.get_user(message.from_user.id)
    lang = user.get("bot_language", "ru")

    # Validate HH:MM format
    try:
        h, m = time_str.split(":")
        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        time_str = f"{int(h):02d}:{int(m):02d}"
    except Exception:
        if lang == "en":
            await message.answer("❌ Invalid format. Please use HH:MM, e.g. 09:00")
        else:
            await message.answer("❌ Неверный формат. Используй ЧЧ:ММ, например 09:00")
        return

    db.update_user(message.from_user.id, notification_time=time_str)
    await state.set_state(SettingsStates.main)

    if lang == "en":
        text = f"✅ Daily task time set to <b>{time_str} MSK</b>!"
    else:
        text = f"✅ Время задачи установлено на <b>{time_str} МСК</b>!"

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings:back")
async def on_settings_back_any(callback: CallbackQuery, state: FSMContext) -> None:
    user = db.get_user(callback.from_user.id)
    lang = user.get("bot_language", "ru") if user else "ru"
    await state.set_state(SettingsStates.main)
    await callback.message.edit_text(
        "⚙️ Настройки:" if lang == "ru" else "⚙️ Settings:",
        reply_markup=settings_keyboard(),
    )
    await callback.answer()


# ─── /help ────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user = db.get_user(message.from_user.id)
    lang = user.get("bot_language", "ru") if user else "ru"
    if lang == "en":
        text = (
            "📚 <b>Help</b>\n\n"
            "/start — start the bot\n"
            "/settings — change language, level, notification time\n"
            "/help — this message\n\n"
            "<b>How it works:</b>\n"
            "1. Choose your programming language and difficulty level\n"
            "2. Receive a daily algorithmic problem\n"
            "3. Send your solution as a code message\n"
            "4. Get feedback: correctness + efficiency\n"
            "5. Use hints if needed 💡"
        )
    else:
        text = (
            "📚 <b>Помощь</b>\n\n"
            "/start — начать работу с ботом\n"
            "/settings — изменить язык, уровень, время уведомлений\n"
            "/help — это сообщение\n\n"
            "<b>Как это работает:</b>\n"
            "1. Выбираешь язык программирования и уровень сложности\n"
            "2. Каждый день получаешь алгоритмическую задачу\n"
            "3. Отправляешь решение кодом в чат\n"
            "4. Получаешь фидбек: правильность + эффективность\n"
            "5. Используй подсказки если нужно 💡"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)


# ─── Scheduler ────────────────────────────────────────────────────────────────

async def daily_task_scheduler(bot: Bot) -> None:
    """Runs every minute. Sends daily problems to users whose notification_time matches now."""
    while True:
        try:
            now_moscow = datetime.now(MOSCOW_TZ)
            current_time = now_moscow.strftime("%H:%M")

            users = db.get_all_active_users()
            for user in users:
                if user.get("notification_time") != current_time:
                    continue
                # Don't send if user hasn't completed setup
                if not user.get("prog_language") or not user.get("level"):
                    continue

                user_id = user["user_id"]
                lang = user.get("bot_language", "ru")
                level = user["level"]
                prog_language = user["prog_language"]

                problem = db.get_next_problem(user_id, level)
                if not problem:
                    try:
                        if lang == "en":
                            await bot.send_message(
                                user_id,
                                "🎉 You've solved all problems at this level! Try a higher difficulty in /settings.",
                            )
                        else:
                            await bot.send_message(
                                user_id,
                                "🎉 Ты решил все задачи этого уровня! Повышай сложность в /settings.",
                            )
                    except Exception:
                        log.exception("Failed to notify user %d of completed problems", user_id)
                    continue

                try:
                    record_id = db.record_problem_sent(user_id, problem["id"])
                    # We store state here but can't use FSMContext in scheduler
                    # The user will send their solution and bot will pick it up
                    text = await format_problem_text(problem, prog_language, lang)
                    if lang == "en":
                        header = f"☀️ <b>Good morning! Your daily task:</b>\n\n"
                    else:
                        header = f"☀️ <b>Ежедневная задача:</b>\n\n"
                    await bot.send_message(
                        user_id,
                        header + text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=problem_keyboard(0),
                    )
                    log.info("Sent daily problem %d to user %d", problem["id"], user_id)
                except Exception:
                    log.exception("Failed to send daily task to user %d", user_id)
                    db.update_user(user_id, is_active=0)

        except Exception:
            log.exception("Scheduler error")

        # Sleep until next minute
        await asyncio.sleep(60)


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    db.init_db()

    from problems_data import PROBLEMS as _BASE
    try:
        from problems_data_new import NEW_PROBLEMS as _NEW
        _ALL = _BASE + _NEW
    except ImportError:
        _ALL = _BASE
    db.seed_problems(_ALL)
    log.info("DB seeded with %d problems", len(PROBLEMS))

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start",    description="Начать / Start"),
        BotCommand(command="settings", description="Настройки / Settings"),
        BotCommand(command="help",     description="Помощь / Help"),
    ])

    # Start scheduler as background task
    asyncio.create_task(daily_task_scheduler(bot))

    log.info("Interview bot started")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
