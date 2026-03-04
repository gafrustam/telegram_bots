"""Who Wants to Be a Millionaire — Telegram bot."""

import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from config import (
    BOT_TOKEN,
    PRIZE_LADDER,
    SAFE_HAVENS,
    TOTAL_QUESTIONS,
    fmt,
    prize,
    safe_haven_amount,
    walkaway_amount,
)
from keyboards import (
    CANCEL_CONFIRM,
    LIFELINE_AUDIENCE,
    LIFELINE_FIFTY,
    LIFELINE_PHONE,
    NEXT_Q,
    NOOP,
    PLAY_AGAIN,
    QUIT_GAME,
    SHOW_LADDER,
    START_GAME,
    back_to_game_keyboard,
    confirm_keyboard,
    correct_answer_keyboard,
    game_over_keyboard,
    loading_keyboard,
    question_keyboard,
    result_keyboard,
    welcome_keyboard,
)
from database import init_db, upsert_user
from questions import (
    ask_audience,
    fifty_fifty,
    format_audience_bars,
    generate_question,
    phone_a_friend,
)

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/millionaire_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler()],
)
log = logging.getLogger(__name__)

router = Router()


# ── FSM States ────────────────────────────────────────────────────────────────
class Game(StatesGroup):
    question   = State()   # Waiting for answer / lifeline
    confirming = State()   # "Final answer?" screen
    result     = State()   # Showing correct/wrong result


# ── Helpers ───────────────────────────────────────────────────────────────────
def _lifeline_defaults() -> dict:
    return {"fifty": True, "phone": True, "audience": True}


def _mini_ladder(level: int) -> str:
    """Compact progress bar for question header."""
    parts = []
    for lvl in range(1, TOTAL_QUESTIONS + 1):
        if lvl == level:
            parts.append(f"<b>[{lvl}]</b>")
        elif lvl in SAFE_HAVENS:
            parts.append(f"🔒{lvl}")
        else:
            parts.append(str(lvl))
    return " · ".join(parts)


def _question_text(level: int, question: str, note: str = "") -> str:
    current_prize = fmt(prize(level))
    haven = safe_haven_amount(level)
    haven_line = f"\n🔒 Несгораемая сумма: <b>{fmt(haven)}</b>" if haven else ""

    header = (
        f"🎯 <b>Вопрос {level} из {TOTAL_QUESTIONS}</b>\n"
        f"💰 Разыгрывается: <b>{current_prize}</b>"
        f"{haven_line}"
    )
    divider = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    note_block = f"\n\n{note}" if note else ""

    return f"{header}{divider}❓ <b>{question}</b>{note_block}{divider}Выберите ответ:"


def _full_ladder_text(current_level: int) -> str:
    lines = ["📊 <b>ТАБЛИЦА ПРИЗОВ</b>\n<pre>"]
    for lvl in range(TOTAL_QUESTIONS, 0, -1):
        amount = PRIZE_LADDER[lvl - 1]
        amount_str = f"{amount:>12,}".replace(",", " ") + " ₽"

        if lvl == TOTAL_QUESTIONS:
            icon = "🏆"
        elif lvl in SAFE_HAVENS:
            icon = "🔒"
        else:
            icon = "  "

        if lvl == current_level:
            line = f"▶ {lvl:2d}. {amount_str}  ← вы здесь"
        else:
            line = f"{icon} {lvl:2d}. {amount_str}"
        lines.append(line)

    lines.append("</pre>")
    return "\n".join(lines)


async def _show_question(
    target: Message | CallbackQuery,
    state: FSMContext,
    level: int,
    q_data: dict,
    note: str = "",
) -> None:
    """Render (or re-render) a question, editing or sending as needed."""
    data = await state.get_data()
    lifelines: dict = data.get("lifelines", _lifeline_defaults())
    removed: list = data.get("removed", [])

    text = _question_text(level, q_data["question"], note)
    kb = question_keyboard(q_data["options"], lifelines, removed)

    msg: Message = target if isinstance(target, Message) else target.message
    try:
        sent = await msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        log.exception("edit_text failed, falling back to answer")
        sent = await msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)

    await state.update_data(msg_id=sent.message_id)
    await state.set_state(Game.question)


# ── /start ────────────────────────────────────────────────────────────────────
@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    text = (
        "🏆 <b>КТО ХОЧЕТ СТАТЬ МИЛЛИОНЕРОМ?</b>\n\n"
        "Добро пожаловать в самую напряжённую интеллектуальную игру!\n\n"
        "📋 <b>Правила:</b>\n"
        "• 15 вопросов с нарастающей сложностью\n"
        "• 4 варианта ответа на каждый вопрос\n"
        "• 3 подсказки: 🔢 50/50 · 📞 Звонок другу · 👥 Помощь зала\n"
        "• Несгораемые суммы: <b>5 000 ₽</b> и <b>100 000 ₽</b>\n"
        "• В любой момент можно забрать выигрыш и уйти\n\n"
        f"💰 <b>Главный приз: {fmt(PRIZE_LADDER[-1])}</b>\n\n"
        "<i>Готовы проверить свои знания?</i>"
    )
    await message.answer(text, reply_markup=welcome_keyboard(), parse_mode=ParseMode.HTML)


# ── /help ─────────────────────────────────────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "ℹ️ <b>Подсказки</b>\n\n"
        "🔢 <b>50/50</b> — убирает два неправильных варианта ответа.\n"
        "📞 <b>Звонок другу</b> — умный друг даст совет (ИИ).\n"
        "👥 <b>Помощь зала</b> — зрители голосуют, видите проценты (ИИ).\n\n"
        "Каждую подсказку можно использовать лишь один раз за игру.\n\n"
        "/start — главное меню"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


# ── Start game ────────────────────────────────────────────────────────────────
@router.callback_query(F.data == START_GAME)
@router.callback_query(F.data == PLAY_AGAIN)
async def cb_start_game(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    # Show loading placeholder
    loading_msg = await callback.message.edit_text(
        "⏳ <b>Генерирую первый вопрос…</b>\n<i>Это займёт пару секунд.</i>",
        reply_markup=loading_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    try:
        q_data = await generate_question(1)
    except Exception:
        log.exception("Question generation failed")
        await loading_msg.edit_text(
            "❌ Не удалось получить вопрос. Попробуйте снова.",
            reply_markup=welcome_keyboard(),
        )
        return

    await state.update_data(
        level=1,
        question=q_data["question"],
        options=q_data["options"],
        correct=q_data["correct"],
        lifelines=_lifeline_defaults(),
        removed=[],
    )

    text = _question_text(1, q_data["question"])
    kb = question_keyboard(q_data["options"], _lifeline_defaults(), [])
    sent = await loading_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(msg_id=sent.message_id)
    await state.set_state(Game.question)


# ── Show full prize ladder ────────────────────────────────────────────────────
@router.callback_query(F.data == SHOW_LADDER)
async def cb_show_ladder(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    level = data.get("level", 1)
    ladder_text = _full_ladder_text(level)

    await callback.message.answer(
        ladder_text,
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_game_keyboard(),
    )


# ── Answer selected (show confirmation) ──────────────────────────────────────
@router.callback_query(Game.question, F.data.startswith("ans_"))
async def cb_answer_selected(callback: CallbackQuery, state: FSMContext) -> None:
    letter = callback.data[-1]  # "A", "B", "C", or "D"
    await callback.answer()

    data = await state.get_data()
    options: dict = data["options"]
    removed: list = data.get("removed", [])

    if letter in removed:
        await callback.answer("Этот вариант недоступен.", show_alert=True)
        return

    option_text = options[letter]
    await state.update_data(pending_answer=letter)
    await state.set_state(Game.confirming)

    level = data["level"]
    note = f"🤔 Ваш ответ: <b>{letter}) {option_text}</b>"
    text = _question_text(level, data["question"], note)

    await callback.message.edit_text(
        text,
        reply_markup=confirm_keyboard(letter, option_text),
        parse_mode=ParseMode.HTML,
    )


# ── Cancel confirmation (back to answer selection) ───────────────────────────
@router.callback_query(Game.confirming, F.data == CANCEL_CONFIRM)
async def cb_cancel_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.update_data(pending_answer=None)
    await state.set_state(Game.question)

    text = _question_text(data["level"], data["question"])
    kb = question_keyboard(data["options"], data["lifelines"], data.get("removed", []))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ── Final answer confirmed ────────────────────────────────────────────────────
@router.callback_query(Game.confirming, F.data.startswith("confirm_"))
async def cb_confirm_answer(callback: CallbackQuery, state: FSMContext) -> None:
    letter = callback.data[-1]
    await callback.answer()

    data = await state.get_data()
    level: int = data["level"]
    options: dict = data["options"]
    correct: str = data["correct"]
    removed: list = data.get("removed", [])
    lifelines: dict = data["lifelines"]

    is_correct = letter == correct
    result_kb = result_keyboard(options, correct, letter, removed)

    if is_correct:
        current_prize = prize(level)
        is_final = level == TOTAL_QUESTIONS

        if is_final:
            result_text = (
                f"🎉🏆 <b>ПОЗДРАВЛЯЕМ! ВЫ ВЫИГРАЛИ {fmt(current_prize)}!</b> 🏆🎉\n\n"
                f"❓ <b>{data['question']}</b>\n\n"
                f"✅ Правильный ответ: <b>{correct}) {options[correct]}</b>\n\n"
                f"<i>Вы прошли все 15 вопросов! Невероятно!</i>"
            )
        else:
            next_prize = prize(level + 1)
            result_text = (
                f"✅ <b>ПРАВИЛЬНО!</b>\n\n"
                f"❓ <b>{data['question']}</b>\n\n"
                f"<b>{correct}) {options[correct]}</b>\n\n"
                f"💰 Вы выиграли: <b>{fmt(current_prize)}</b>\n"
                f"➡️ Следующий вопрос разыгрывает <b>{fmt(next_prize)}</b>"
            )

        await state.update_data(earned=current_prize)
        await state.set_state(Game.result)
        await callback.message.edit_text(
            result_text,
            reply_markup=result_kb,
            parse_mode=ParseMode.HTML,
        )
        # Add action buttons below result display
        action_msg_text = result_text + "\n\n" + ("━━━━━━━━━━━━━━━━━━━━━━━━━━" if not is_final else "")
        await callback.message.edit_text(
            result_text,
            reply_markup=correct_answer_keyboard(is_final),
            parse_mode=ParseMode.HTML,
        )

    else:
        earned = safe_haven_amount(level)
        result_text = (
            f"❌ <b>НЕПРАВИЛЬНО!</b>\n\n"
            f"❓ <b>{data['question']}</b>\n\n"
            f"Ваш ответ: ❌ <b>{letter}) {options[letter]}</b>\n"
            f"Правильный ответ: ✅ <b>{correct}) {options[correct]}</b>\n\n"
        )
        if earned:
            result_text += f"💔 Вы уходите с несгораемой суммой: <b>{fmt(earned)}</b>"
        else:
            result_text += "💔 К сожалению, вы уходите ни с чем."

        await state.set_state(Game.result)
        await callback.message.edit_text(
            result_text,
            reply_markup=game_over_keyboard(),
            parse_mode=ParseMode.HTML,
        )


# ── Next question ─────────────────────────────────────────────────────────────
@router.callback_query(Game.result, F.data == NEXT_Q)
async def cb_next_question(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    next_level = data["level"] + 1

    # Show loading
    await callback.message.edit_text(
        f"⏳ <b>Вопрос {next_level} из {TOTAL_QUESTIONS}…</b>\n<i>Генерирую вопрос.</i>",
        reply_markup=loading_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    try:
        q_data = await generate_question(next_level)
    except Exception:
        log.exception("Question generation failed")
        await callback.message.edit_text(
            "❌ Ошибка генерации вопроса. Попробуйте ещё раз.",
            reply_markup=game_over_keyboard(),
        )
        return

    lifelines: dict = data.get("lifelines", _lifeline_defaults())

    await state.update_data(
        level=next_level,
        question=q_data["question"],
        options=q_data["options"],
        correct=q_data["correct"],
        removed=[],
        pending_answer=None,
    )
    await state.set_state(Game.question)

    text = _question_text(next_level, q_data["question"])
    kb = question_keyboard(q_data["options"], lifelines, [])
    sent = await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.update_data(msg_id=sent.message_id)


# ── Quit / take the money ─────────────────────────────────────────────────────
@router.callback_query(F.data == QUIT_GAME)
async def cb_quit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    level: int = data.get("level", 1)
    earned: int = data.get("earned", walkaway_amount(level))

    if earned:
        farewell = (
            f"🚶 <b>Вы забираете деньги и уходите.</b>\n\n"
            f"💰 Ваш выигрыш: <b>{fmt(earned)}</b>\n\n"
            "<i>Отличная игра! До следующего раза!</i>"
        )
    else:
        farewell = (
            "🚶 <b>Вы уходите из игры.</b>\n\n"
            "💔 К сожалению, вы ничего не выигрываете.\n\n"
            "<i>Попробуйте ещё раз!</i>"
        )

    await state.clear()
    await callback.message.edit_text(
        farewell, reply_markup=game_over_keyboard(), parse_mode=ParseMode.HTML
    )


# ── Lifeline: 50/50 ───────────────────────────────────────────────────────────
@router.callback_query(Game.question, F.data == LIFELINE_FIFTY)
async def cb_fifty_fifty(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("🔢 Подсказка 50/50 активирована!")
    data = await state.get_data()
    lifelines: dict = data["lifelines"]

    if not lifelines.get("fifty"):
        await callback.answer("Эта подсказка уже использована.", show_alert=True)
        return

    removed: list = data.get("removed", [])
    to_remove = fifty_fifty(data["options"], data["correct"], removed)
    removed += to_remove

    lifelines["fifty"] = False
    await state.update_data(lifelines=lifelines, removed=removed)

    # Rebuild question message with updated keyboard
    note = (
        f"🔢 <b>50/50:</b> убраны варианты "
        f"<b>{', '.join(to_remove)}</b>"
    )
    text = _question_text(data["level"], data["question"], note)
    kb = question_keyboard(data["options"], lifelines, removed)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ── Lifeline: Phone a Friend ──────────────────────────────────────────────────
@router.callback_query(Game.question, F.data == LIFELINE_PHONE)
async def cb_phone_friend(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("📞 Соединяю с другом…")
    data = await state.get_data()
    lifelines: dict = data["lifelines"]

    if not lifelines.get("phone"):
        await callback.answer("Эта подсказка уже использована.", show_alert=True)
        return

    # Show loading indicator
    note = "📞 <b>Звонок другу:</b> <i>соединяем…</i>"
    text = _question_text(data["level"], data["question"], note)
    kb = question_keyboard(data["options"], lifelines, data.get("removed", []))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

    try:
        advice = await phone_a_friend(
            data["question"],
            data["options"],
            data["correct"],
            data.get("removed", []),
        )
    except Exception:
        log.exception("Phone a friend failed")
        advice = "Извини, не дозвонился…"

    lifelines["phone"] = False
    await state.update_data(lifelines=lifelines)

    note = f"📞 <b>Звонок другу:</b>\n\n<i>«{advice}»</i>"
    text = _question_text(data["level"], data["question"], note)
    kb = question_keyboard(data["options"], lifelines, data.get("removed", []))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ── Lifeline: Ask the Audience ────────────────────────────────────────────────
@router.callback_query(Game.question, F.data == LIFELINE_AUDIENCE)
async def cb_audience(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("👥 Собираю голоса зала…")
    data = await state.get_data()
    lifelines: dict = data["lifelines"]

    if not lifelines.get("audience"):
        await callback.answer("Эта подсказка уже использована.", show_alert=True)
        return

    # Show loading
    note = "👥 <b>Помощь зала:</b> <i>подсчитываем голоса…</i>"
    text = _question_text(data["level"], data["question"], note)
    kb = question_keyboard(data["options"], lifelines, data.get("removed", []))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

    try:
        votes = await ask_audience(
            data["question"],
            data["options"],
            data["correct"],
            data.get("removed", []),
        )
    except Exception:
        log.exception("Ask audience failed")
        votes = {k: 25 for k in data["options"] if k not in data.get("removed", [])}

    lifelines["audience"] = False
    await state.update_data(lifelines=lifelines)

    bars = format_audience_bars(votes, data["options"])
    note = bars
    text = _question_text(data["level"], data["question"], note)
    kb = question_keyboard(data["options"], lifelines, data.get("removed", []))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ── No-op (disabled buttons) ──────────────────────────────────────────────────
@router.callback_query(F.data == NOOP)
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ── Stale callbacks (e.g. after state cleared) ───────────────────────────────
@router.callback_query()
async def cb_catch_all(callback: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await callback.answer(
            "Нет активной игры. Нажмите /start чтобы начать.", show_alert=True
        )
    else:
        await callback.answer()


# ── Bootstrap ─────────────────────────────────────────────────────────────────
async def main() -> None:
    await init_db()

    bot = Bot(token=BOT_TOKEN, default=None)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Millionaire bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
