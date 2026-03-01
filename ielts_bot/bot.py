import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    Message,
    WebAppInfo,
)

import database
from assessor import assess_part1, assess_part2, assess_part3, _get_duration_seconds
from formatter import (
    format_assessment,
    format_error,
    format_admin_summary,
)
from keyboards import (
    ADMIN_BTN,
    PART1_BTN,
    PART2_BTN,
    PART3_BTN,
    WEBAPP_BTN,
    interrupt_keyboard,
    main_menu_keyboard,
    question_keyboard,
    results_keyboard,
    start_keyboard,
    topic_keyboard,
)
from questions import generate_session
from states import InterruptAction, QuestionAction, ResultAction, SpeakingStates, TopicAction
from tts import text_to_voice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

ADMIN_USERNAME = (os.getenv("ADMIN_USERNAME") or "").lstrip("@").lower() or None
_admin_ids: set[int] = set()

WELCOME_TEXT = (
    "🎓 <b>IELTS Speaking Practice</b>\n"
    "\n"
    "В этом боте ты сможешь тренировать свой спикинг.\n"
    "\n"
    "Официальный экзамен состоит из 3 частей:\n"
    "🗣 <b>Part 1</b> — Interview (вопросы на повседневные темы)\n"
    "🎙 <b>Part 2</b> — Long Turn (монолог 2 минуты по карточке)\n"
    "💬 <b>Part 3</b> — Discussion (обсуждение абстрактных тем)\n"
    "\n"
    "Здесь ты можешь потренировать их по отдельности.\n"
    "Попробуй ответить на вопросы, получи обратную связь,\n"
    "проанализируй и попробуй ещё раз — отточи свой ответ\n"
    "до совершенства. Это существенно поднимет твою оценку\n"
    "на экзамене! 🚀\n"
    "\n"
    "👇 <b>Выбери раздел в меню ниже</b>"
)

HELP_TEXT = (
    "📖 <b>Справка</b>\n"
    "\n"
    "<b>Как пользоваться:</b>\n"
    "  1. Выберите часть экзамена в меню\n"
    "  2. Примите предложенную тему или выберите другую\n"
    "  3. Отвечайте голосовыми сообщениями на английском\n"
    "  4. Получите оценку и рекомендации\n"
    "\n"
    "<b>Part 1</b> — 4-5 вопросов, ответ 15-30 сек на каждый\n"
    "<b>Part 2</b> — 1 карточка, монолог до 2 минут\n"
    "<b>Part 3</b> — 4-5 вопросов, ответ 30-60 сек на каждый\n"
    "\n"
    "<b>Советы:</b>\n"
    "  • Говорите в тихом месте\n"
    "  • Держите телефон близко ко рту\n"
    "  • Отвечайте развёрнуто\n"
    "\n"
    "<b>Команды:</b>\n"
    "  /start   — Главное меню\n"
    "  /help    — Эта справка\n"
    "  /cancel  — Отменить текущую сессию"
)

PROCESSING_TEXT = (
    "🎧 <b>Анализирую ваши ответы...</b>\n"
    "\n"
    "<i>Слушаю произношение, оцениваю грамматику,\n"
    "лексику и связность речи. Это может занять\n"
    "некоторое время.</i>"
)

THAI_TZ = timezone(timedelta(hours=7))


def _parse_retry_time(e: Exception) -> datetime | None:
    """Extract retry-after timestamp from an OpenAI RateLimitError."""
    try:
        headers = getattr(getattr(e, "response", None), "headers", None) or {}
        if reset_str := headers.get("x-ratelimit-reset-requests"):
            return datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
        if retry_secs := headers.get("retry-after"):
            return datetime.now(timezone.utc) + timedelta(seconds=float(retry_secs))
    except Exception:
        pass
    try:
        msg = str(e)
        m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", msg)
        if m and any(m.groups()):
            h = int(m.group(1) or 0)
            mins = int(m.group(2) or 0)
            secs = float(m.group(3) or 0)
            return datetime.now(timezone.utc) + timedelta(hours=h, minutes=mins, seconds=secs)
    except Exception:
        pass
    return None


def _format_rate_limit_msg(e: Exception) -> str:
    reset_dt = _parse_retry_time(e)
    if reset_dt:
        thai_dt = reset_dt.astimezone(THAI_TZ)
        return (
            "⏳ <b>Дневной лимит исчерпан.</b>\n\n"
            f"Лимит обновится в <b>{thai_dt.strftime('%H:%M')}</b> по тайскому времени "
            f"({thai_dt.strftime('%-d %b')}).\n"
            "Попробуй снова после этого времени."
        )
    return (
        "⏳ <b>Дневной лимит исчерпан.</b>\n\n"
        "Попробуй снова позже — лимит скоро обновится."
    )


PART_NAMES = {
    1: "Part 1 — Interview",
    2: "Part 2 — Long Turn",
    3: "Part 3 — Discussion",
}

PART_INSTRUCTIONS = {
    1: (
        "Эта часть имитирует короткое интервью с экзаменатором "
        "на знакомые повседневные темы: дом, работа, учёба, "
        "хобби, путешествия и т.д.\n"
        "\n"
        "Формат — диалог: экзаменатор задаёт вопрос, ты отвечаешь. "
        "Старайся говорить естественно и развёрнуто "
        "(<b>~20–30 секунд</b> на вопрос), избегая односложных "
        "ответов. При этом не превращай ответ в монолог — это беседа.\n"
        "\n"
        "🎤 На каждый вопрос отправляй отдельное голосовое сообщение."
    ),
    2: (
        "Эта часть — индивидуальный монолог (Long Turn). "
        "Ты получаешь карточку с темой и пунктами, которые нужно "
        "раскрыть. На реальном экзамене даётся <b>1 минута</b> "
        "на подготовку и ровно <b>2 минуты</b> на ответ — после "
        "этого экзаменатор останавливает.\n"
        "\n"
        "Речь сверх 2 минут <b>не оценивается</b>. Если говоришь "
        "значительно меньше 1:30, это может снизить балл за "
        "Fluency & Coherence — на уровне Band 6+ требуется "
        "умение говорить развёрнуто.\n"
        "\n"
        "🎤 Когда будешь готов — запиши одно голосовое сообщение."
    ),
    3: (
        "Эта часть — двусторонняя дискуссия. Экзаменатор задаёт "
        "более абстрактные и аналитические вопросы на широкие темы.\n"
        "\n"
        "Здесь ценится умение аргументировать, сравнивать, "
        "рассуждать о причинах и последствиях. Отвечай развёрнуто "
        "(<b>~30–60 секунд</b> на вопрос), приводи примеры "
        "и обосновывай свою точку зрения.\n"
        "\n"
        "🎤 На каждый вопрос отправляй отдельное голосовое сообщение."
    ),
}


# ── /start ───────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if db_session_id := data.get("db_session_id"):
        await database.fail_session(db_session_id)
    await state.clear()
    user = message.from_user
    await database.upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    is_adm = _is_admin(user.id, user.username)
    if is_adm:
        _admin_ids.add(user.id)
    logger.info(
        "cmd_start: user_id=%d username=%s is_admin=%s admin_ids=%s",
        user.id, user.username, is_adm, _admin_ids,
    )
    # TEXT INTERFACE DISABLED: showing compact welcome with Web App button only.
    # RESTORE: replace with WELCOME_TEXT and re-enable state below.
    await message.answer(
        "🎓 <b>IELTS Speaking Practice</b>\n\n"
        "Нажми кнопку <b>Web App</b> ниже, чтобы открыть тренажёр.",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(is_admin=is_adm),
    )
    # RESTORE: await state.set_state(SpeakingStates.choosing_part)


# ── /help ────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)


# ── /cancel ──────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if db_session_id := data.get("db_session_id"):
        await database.fail_session(db_session_id)
    await state.clear()
    await message.answer(
        "Сессия отменена. Выбери раздел экзамена:",
        reply_markup=main_menu_keyboard(
            is_admin=_is_admin(message.from_user.id, message.from_user.username),
        ),
    )
    await state.set_state(SpeakingStates.choosing_part)


# ── /webapp ──────────────────────────────────────────────

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://gafrustam.ru/ielts/")


@router.message(Command("webapp"))
async def cmd_webapp(message: Message) -> None:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🌐 Open Web App",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ]])
    await message.answer(
        "🌐 <b>IELTS Speaking Practice — Web App</b>\n\n"
        "Тренируй спикинг прямо в браузере или в мини-приложении Telegram.",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# ── /admin ───────────────────────────────────────────────

def _is_admin(user_id: int = 0, username: str | None = None) -> bool:
    if user_id and user_id in _admin_ids:
        return True
    return ADMIN_USERNAME is not None and bool(username) and username.lower() == ADMIN_USERNAME


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id, message.from_user.username):
        return
    if not database.is_available():
        await message.answer("⚠️ База данных недоступна.")
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    stats = await database.get_admin_summary_stats()
    retention = await database.get_admin_retention()
    text = format_admin_summary(stats, retention)
    await message.answer(text, parse_mode=ParseMode.HTML)


# ── Menu button: Admin ──────────────────────────────────

@router.message(F.text == ADMIN_BTN)
async def handle_admin_button(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id, message.from_user.username):
        return
    if not database.is_available():
        await message.answer("⚠️ База данных недоступна.")
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    stats = await database.get_admin_summary_stats()
    retention = await database.get_admin_retention()
    text = format_admin_summary(stats, retention)
    await message.answer(text, parse_mode=ParseMode.HTML)


# ── Topic generation helper ──────────────────────────────

async def _generate_topic_session(
    part: int, user_id: int, related_topic: str | None = None,
) -> dict:
    """Pick a topic from the bank and generate questions for it."""
    bank_topic = await database.get_random_topic(part, user_id)

    if bank_topic:
        topic_name = bank_topic["topic"]
        cue_card_template = bank_topic.get("cue_card")
        session = await generate_session(
            part,
            topic=topic_name,
            cue_card_template=cue_card_template if part == 2 else None,
            related_topic=related_topic if part == 3 else None,
        )
        # Ensure topic name from bank is used
        session.setdefault("topic", topic_name)
    else:
        session = await generate_session(
            part,
            related_topic=related_topic if part == 3 else None,
        )

    return session


# ── Part selection ───────────────────────────────────────

@router.message(SpeakingStates.choosing_part, F.text.in_({PART1_BTN, PART2_BTN, PART3_BTN}))
async def handle_part_selection(message: Message, state: FSMContext) -> None:
    part_map = {PART1_BTN: 1, PART2_BTN: 2, PART3_BTN: 3}
    part = part_map[message.text]

    await state.update_data(
        part=part,
        current_q_index=0,
        audio_file_ids=[],
        audio_durations=[],
    )

    text = f"📝 <b>{PART_NAMES[part]}</b>\n\n{PART_INSTRUCTIONS[part]}"
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )
    await state.set_state(SpeakingStates.choosing_topic)


# ── Topic callbacks ──────────────────────────────────────

@router.callback_query(TopicAction.filter(F.action == "another"), SpeakingStates.choosing_topic)
async def handle_another_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]

    await callback.answer("Генерирую новую тему...")

    try:
        session = await _generate_topic_session(part, callback.from_user.id)
    except Exception:
        logger.exception("Failed to generate session")
        await callback.answer("Ошибка генерации, попробуйте ещё раз", show_alert=True)
        return

    topic = session.get("topic", "General")
    questions = session.get("questions", [])
    cue_card = session.get("cue_card", "")

    gen_topic_id = await database.save_generated_topic(
        user_id=callback.from_user.id,
        part=part, topic=topic,
        questions=questions or None,
        cue_card=cue_card or None,
    )

    await state.update_data(
        topic=topic,
        questions=questions,
        cue_card=cue_card,
        gen_topic_id=gen_topic_id,
    )

    text = f"📝 <b>{PART_NAMES[part]}</b>\n\nТема: <b>{topic}</b>\n"
    if part != 2:
        text += f"\nВопросов: {len(questions)}\n"
    text += f"\n{PART_INSTRUCTIONS[part]}"

    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=topic_keyboard(),
    )


@router.callback_query(TopicAction.filter(F.action == "accept"), SpeakingStates.choosing_topic)
async def handle_accept_topic(callback: CallbackQuery, state: FSMContext) -> None:
    from openai import RateLimitError as OpenAIRateLimitError

    data = await state.get_data()
    part = data["part"]

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    wait_msg = await callback.message.answer(
        "⏳ <i>Генерирую тему...</i>",
        parse_mode=ParseMode.HTML,
    )
    await bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    # For Part 3, try to link to the user's last Part 2 topic
    related_topic = None
    if part == 3:
        related_topic = await database.get_last_part2_topic(callback.from_user.id)

    try:
        session = await _generate_topic_session(part, callback.from_user.id, related_topic)
    except OpenAIRateLimitError as e:
        logger.warning("Rate limit hit during topic generation: %s", e)
        await wait_msg.edit_text(_format_rate_limit_msg(e), parse_mode=ParseMode.HTML)
        return
    except Exception:
        logger.exception("Failed to generate session")
        await wait_msg.edit_text(
            format_error("Не удалось сгенерировать тему. Попробуйте ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        return

    topic = session.get("topic", "General")
    questions = session.get("questions", [])
    cue_card = session.get("cue_card", "")

    gen_topic_id = await database.save_generated_topic(
        user_id=callback.from_user.id,
        part=part, topic=topic,
        questions=questions or None,
        cue_card=cue_card or None,
    )
    await database.mark_topic_accepted(gen_topic_id)

    # Create DB session
    db_session_id = await database.create_session(
        user_id=callback.from_user.id,
        part=part,
        topic=topic,
        questions=questions or None,
        cue_card=cue_card or None,
        topic_id=gen_topic_id,
    )
    await state.update_data(
        topic=topic,
        questions=questions,
        cue_card=cue_card,
        gen_topic_id=gen_topic_id,
        db_session_id=db_session_id,
    )

    await wait_msg.delete()

    if part == 2:
        asyncio.create_task(_start_part2_countdown(callback.message.chat.id, state))
    else:
        answering_state = (
            SpeakingStates.part1_answering if part == 1
            else SpeakingStates.part3_answering
        )
        await state.set_state(answering_state)
        await _send_question(callback.message, state, 0)


# ── Custom topic ──────────────────────────────────────────

CUSTOM_TOPIC_QA = (
    "✏️ <b>Своя тема</b>\n"
    "\n"
    "Отправь тему и вопросы в одном сообщении.\n"
    "\n"
    "<b>Формат:</b>\n"
    "<code>Topic: Technology\n"
    "1. How often do you use technology?\n"
    "2. What is your favorite gadget?\n"
    "3. Has technology changed the way you communicate?\n"
    "4. Do you think we rely too much on technology?</code>"
)

CUSTOM_TOPIC_CUE_CARD = (
    "✏️ <b>Своя тема</b>\n"
    "\n"
    "Отправь тему и карточку в одном сообщении.\n"
    "\n"
    "<b>Формат:</b>\n"
    "<code>Topic: A memorable trip\n"
    "Describe a memorable trip you took.\n"
    "You should say:\n"
    "- where you went\n"
    "- who you went with\n"
    "- what you did\n"
    "and explain why it was memorable.</code>"
)


@router.callback_query(TopicAction.filter(F.action == "custom"), SpeakingStates.choosing_topic)
async def handle_custom_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    example = CUSTOM_TOPIC_CUE_CARD if part == 2 else CUSTOM_TOPIC_QA
    await callback.message.answer(
        example,
        parse_mode=ParseMode.HTML,
    )
    await state.set_state(SpeakingStates.entering_custom_topic)


@router.message(SpeakingStates.entering_custom_topic, F.text)
async def handle_custom_topic_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]
    text = message.text.strip()

    # Parse topic
    lines = text.split("\n")
    topic = "Custom topic"
    content_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower().startswith("topic:"):
            topic = stripped[6:].strip()
        else:
            content_lines.append(stripped)

    # Remove empty leading lines
    while content_lines and not content_lines[0]:
        content_lines.pop(0)

    questions = []
    cue_card = ""

    if part == 2:
        # Everything after topic line is the cue card
        cue_card = "\n".join(content_lines).strip()
        if not cue_card:
            await message.answer(
                "Не удалось распознать карточку. Попробуй ещё раз в формате выше.",
                parse_mode=ParseMode.HTML,
            )
            return
    else:
        # Parse numbered questions
        for line in content_lines:
            # Strip numbering like "1.", "2)", "1 -", etc.
            cleaned = re.sub(r"^\d+[\.\)\-\s]+", "", line).strip()
            if cleaned:
                questions.append(cleaned)

        if len(questions) < 2:
            await message.answer(
                "Нужно минимум 2 вопроса. Попробуй ещё раз в формате выше.",
                parse_mode=ParseMode.HTML,
            )
            return

    gen_topic_id = await database.save_generated_topic(
        user_id=message.from_user.id,
        part=part, topic=topic,
        questions=questions or None,
        cue_card=cue_card or None,
    )
    await database.mark_topic_accepted(gen_topic_id)

    db_session_id = await database.create_session(
        user_id=message.from_user.id,
        part=part,
        topic=topic,
        questions=questions or None,
        cue_card=cue_card or None,
        topic_id=gen_topic_id,
    )

    await state.update_data(
        topic=topic,
        questions=questions,
        cue_card=cue_card,
        gen_topic_id=gen_topic_id,
        db_session_id=db_session_id,
        current_q_index=0,
        audio_file_ids=[],
        audio_durations=[],
    )

    preview = f"📝 <b>{PART_NAMES[part]}</b>\n\nТема: <b>{topic}</b>\n"
    if part == 2:
        preview += f"\n{cue_card}\n"
    else:
        preview += f"\nВопросов: {len(questions)}\n"

    await message.answer(preview + "\n✅ Тема принята! Начинаем.", parse_mode=ParseMode.HTML)

    if part == 2:
        asyncio.create_task(_start_part2_countdown(message.chat.id, state))
    else:
        answering_state = (
            SpeakingStates.part1_answering if part == 1
            else SpeakingStates.part3_answering
        )
        await state.set_state(answering_state)
        await _send_question(message, state, 0)


# ── Part 2 countdown + start ─────────────────────────────

async def _start_part2_countdown(chat_id: int, state: FSMContext) -> None:
    await state.set_state(SpeakingStates.part2_preparing)

    data = await state.get_data()
    cue_card = data.get("cue_card", "")

    def _build_countdown_text(label: str) -> str:
        text = f"⏱ <b>Подготовка: {label}</b>"
        if cue_card:
            text += f"\n\n📋 <b>Карточка:</b>\n{cue_card}"
        text += "\n\n<i>Когда будешь готов — запиши голосовое сообщение.</i>"
        return text

    msg = await bot.send_message(
        chat_id,
        _build_countdown_text("1:00"),
        parse_mode=ParseMode.HTML,
    )

    for remaining in range(55, 0, -5):
        await asyncio.sleep(5)
        current = await state.get_state()
        if current != SpeakingStates.part2_preparing.state:
            return
        m, s = divmod(remaining, 60)
        try:
            await bot.edit_message_text(
                _build_countdown_text(f"{m}:{s:02d}"),
                chat_id, msg.message_id,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    await asyncio.sleep(5)
    current = await state.get_state()
    if current != SpeakingStates.part2_preparing.state:
        return

    await state.set_state(SpeakingStates.part2_answering)
    end_text = "⏱ <b>Время подготовки вышло!</b>"
    if cue_card:
        end_text += f"\n\n📋 <b>Карточка:</b>\n{cue_card}"
    end_text += "\n\n🎤 Запиши голосовое сообщение (до 2 минут)."
    try:
        await bot.edit_message_text(
            end_text,
            chat_id, msg.message_id,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await bot.send_message(chat_id, end_text, parse_mode=ParseMode.HTML)


# ── Send question via TTS ────────────────────────────────

async def _send_question(message: Message, state: FSMContext, index: int) -> None:
    data = await state.get_data()
    questions = data["questions"]
    question = questions[index]
    total = len(questions)
    part = data.get("part", 1)

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Parts 1 & 3: audio only, no text — question is conveyed via voice
    caption = f"Вопрос {index + 1}/{total}\n\n🎤 Ответьте голосовым сообщением."

    try:
        audio_bytes = await text_to_voice(question)
        voice_file = BufferedInputFile(audio_bytes, filename="question.ogg")
        sent = await bot.send_voice(
            chat_id=message.chat.id,
            voice=voice_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=question_keyboard(),
        )
        await state.update_data(last_question_voice_id=sent.voice.file_id)
    except Exception:
        logger.exception("TTS failed, sending text only")
        await message.answer(
            f"❓ Вопрос {index + 1}/{total}: <i>{question}</i>\n\n"
            f"🎤 Ответьте голосовым сообщением.",
            parse_mode=ParseMode.HTML,
        )


# ── Replay question ─────────────────────────────────────

@router.callback_query(QuestionAction.filter(F.action == "replay"))
async def handle_question_replay(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    voice_id = data.get("last_question_voice_id")
    if not voice_id:
        await callback.answer("Аудио недоступно", show_alert=True)
        return
    await bot.send_voice(
        chat_id=callback.message.chat.id,
        voice=voice_id,
        caption="🔄 Повтор вопроса\n\n🎤 Ответьте голосовым сообщением.",
        reply_markup=question_keyboard(),
    )


# ── Part 1 voice handler ────────────────────────────────

@router.message(SpeakingStates.part1_answering, F.voice)
async def handle_part1_voice(message: Message, state: FSMContext) -> None:
    await _handle_qa_voice(message, state, SpeakingStates.part1_answering)


# ── Part 3 voice handler ────────────────────────────────

@router.message(SpeakingStates.part3_answering, F.voice)
async def handle_part3_voice(message: Message, state: FSMContext) -> None:
    await _handle_qa_voice(message, state, SpeakingStates.part3_answering)


async def _handle_qa_voice(message: Message, state: FSMContext, current_state) -> None:
    data = await state.get_data()
    questions = data["questions"]
    index = data["current_q_index"]
    audio_ids = data["audio_file_ids"]
    durations = data["audio_durations"]

    audio_ids.append(message.voice.file_id)
    durations.append(message.voice.duration or 0)
    index += 1

    await state.update_data(
        audio_file_ids=audio_ids,
        audio_durations=durations,
        current_q_index=index,
    )

    if index < len(questions):
        await _send_question(message, state, index)
    else:
        await _run_assessment(message, state)


# ── Part 2 voice handler ────────────────────────────────

@router.message(SpeakingStates.part2_preparing, F.voice)
async def handle_part2_voice_early(message: Message, state: FSMContext) -> None:
    """User skipped prep time by sending voice early."""
    await state.set_state(SpeakingStates.part2_answering)
    await handle_part2_voice(message, state)


@router.message(SpeakingStates.part2_answering, F.voice)
async def handle_part2_voice(message: Message, state: FSMContext) -> None:
    duration = message.voice.duration or 0

    await state.update_data(
        audio_file_ids=[message.voice.file_id],
        audio_durations=[duration],
    )

    if duration > 120:
        mins = duration // 60
        secs = duration % 60
        await message.answer(
            f"Ваш ответ: <b>{mins}:{secs:02d}</b>. "
            "Будут оценены первые 2 минуты.",
            parse_mode=ParseMode.HTML,
        )

    await _run_assessment(message, state)


# ── Assessment ───────────────────────────────────────────

async def _run_assessment(message: Message, state: FSMContext) -> None:
    await state.set_state(SpeakingStates.assessing)
    status_msg = await message.answer(PROCESSING_TEXT, parse_mode=ParseMode.HTML)

    data = await state.get_data()
    part = data["part"]
    db_session_id = data.get("db_session_id")

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        with tempfile.TemporaryDirectory() as tmp_dir:
            ogg_paths = []
            for i, file_id in enumerate(data["audio_file_ids"]):
                file = await bot.get_file(file_id)
                path = os.path.join(tmp_dir, f"response_{i}.oga")
                await bot.download_file(file.file_path, path)
                ogg_paths.append(path)

            if part == 1:
                result = await assess_part1(
                    ogg_paths, data["questions"], data["topic"],
                    durations=data.get("audio_durations"),
                )
            elif part == 2:
                duration = await asyncio.to_thread(
                    _get_duration_seconds, ogg_paths[0],
                )
                result = await assess_part2(
                    ogg_paths[0], data["cue_card"], duration,
                )
            else:
                result = await assess_part3(
                    ogg_paths, data["questions"], data["topic"],
                    durations=data.get("audio_durations"),
                )

        response_text = format_assessment(result)

        # Save to database
        audio_total = sum(data.get("audio_durations", []))
        await database.complete_session(db_session_id, audio_total)
        await database.save_assessment(
            session_id=db_session_id,
            user_id=message.from_user.id,
            result=result,
        )

        await state.set_state(SpeakingStates.viewing_results)

        if len(response_text) <= 4096:
            await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)
        else:
            await status_msg.delete()
            for chunk in _split_message(response_text):
                await message.answer(chunk, parse_mode=ParseMode.HTML)

        await message.answer(
            "Если хочешь — попробуй ещё раз ту же тему. "
            "Или просто выбери другой раздел в меню снизу 👇",
            reply_markup=results_keyboard(),
        )

    except Exception as e:
        from openai import RateLimitError as OpenAIRateLimitError
        if isinstance(e, OpenAIRateLimitError):
            logger.warning("Rate limit hit during assessment: %s", e)
            err_text = _format_rate_limit_msg(e)
        else:
            logger.exception("Error during assessment")
            err_text = format_error("Не удалось выполнить оценку. Попробуйте ещё раз.")
        await database.fail_session(db_session_id)
        await status_msg.edit_text(err_text, parse_mode=ParseMode.HTML)
        await state.set_state(SpeakingStates.viewing_results)
        await message.answer(
            "Можешь попробовать ещё раз или выбрать другой раздел 👇",
            reply_markup=results_keyboard(),
        )


# ── Result callbacks ─────────────────────────────────────

@router.callback_query(ResultAction.filter(F.action == "retry"), SpeakingStates.viewing_results)
async def handle_retry(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]

    # Create a new DB session for the retry
    db_session_id = await database.create_session(
        user_id=callback.from_user.id,
        part=part,
        topic=data["topic"],
        questions=data.get("questions") or None,
        cue_card=data.get("cue_card") or None,
    )

    await state.update_data(
        audio_file_ids=[],
        audio_durations=[],
        current_q_index=0,
        db_session_id=db_session_id,
    )

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if part == 1:
        await state.set_state(SpeakingStates.part1_answering)
        await _send_question(callback.message, state, 0)
    elif part == 2:
        asyncio.create_task(_start_part2_countdown(callback.message.chat.id, state))
    else:
        await state.set_state(SpeakingStates.part3_answering)
        await _send_question(callback.message, state, 0)


@router.callback_query(ResultAction.filter(F.action == "menu"), SpeakingStates.viewing_results)
async def handle_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    await callback.message.answer(
        "👇 Выбери раздел экзамена:",
        reply_markup=main_menu_keyboard(
            is_admin=_is_admin(callback.from_user.id, callback.from_user.username),
        ),
    )
    await state.set_state(SpeakingStates.choosing_part)


# ── Interrupt: part button pressed during active session ──

ACTIVE_STATES = {
    SpeakingStates.choosing_topic,
    SpeakingStates.entering_custom_topic,
    SpeakingStates.part1_answering,
    SpeakingStates.part2_preparing,
    SpeakingStates.part2_answering,
    SpeakingStates.part3_answering,
    SpeakingStates.assessing,
    SpeakingStates.viewing_results,
}

PART_MAP = {PART1_BTN: 1, PART2_BTN: 2, PART3_BTN: 3}


@router.message(F.text.in_({PART1_BTN, PART2_BTN, PART3_BTN}))
async def handle_part_while_active(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нажми /start, чтобы начать.")
        return

    # No active session yet or session already finished — switch freely
    if current in (
        SpeakingStates.choosing_topic.state,
        SpeakingStates.entering_custom_topic.state,
        SpeakingStates.viewing_results.state,
    ):
        await state.clear()
        await state.set_state(SpeakingStates.choosing_part)
        await handle_part_selection(message, state)
        return

    data = await state.get_data()
    current_part = data.get("part")
    new_part = PART_MAP[message.text]

    if current_part:
        await message.answer(
            f"⚠️ У тебя уже начата <b>{PART_NAMES[current_part]}</b>.\n"
            "Что хочешь сделать?",
            parse_mode=ParseMode.HTML,
            reply_markup=interrupt_keyboard(new_part),
        )
    else:
        await state.clear()
        await state.set_state(SpeakingStates.choosing_part)
        await handle_part_selection(message, state)


@router.callback_query(InterruptAction.filter(F.action == "continue"))
async def handle_interrupt_continue(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Продолжаем!")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(InterruptAction.filter(F.action == "new"))
async def handle_interrupt_new(
    callback: CallbackQuery, callback_data: InterruptAction, state: FSMContext,
) -> None:
    new_part = callback_data.new_part
    # Cancel current session in DB
    data = await state.get_data()
    db_session_id = data.get("db_session_id")
    if db_session_id:
        await database.fail_session(db_session_id)

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.clear()
    await state.update_data(
        part=new_part,
        current_q_index=0,
        audio_file_ids=[],
        audio_durations=[],
    )

    text = f"📝 <b>{PART_NAMES[new_part]}</b>\n\n{PART_INSTRUCTIONS[new_part]}"
    await callback.message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )
    await state.set_state(SpeakingStates.choosing_topic)


# ── Catch-all handlers ───────────────────────────────────

@router.message(SpeakingStates.part1_answering, F.text)
@router.message(SpeakingStates.part3_answering, F.text)
async def handle_text_during_qa(message: Message) -> None:
    await message.answer(
        "🎤 Пожалуйста, отправь <b>голосовое сообщение</b>.",
        parse_mode=ParseMode.HTML,
    )


@router.message(SpeakingStates.part2_answering, F.text)
async def handle_text_during_part2(message: Message) -> None:
    await message.answer(
        "🎤 Запиши <b>голосовое сообщение</b> (до 2 минут).",
        parse_mode=ParseMode.HTML,
    )


@router.message(SpeakingStates.assessing, F.text)
@router.message(SpeakingStates.assessing, F.voice)
async def handle_during_assessing(message: Message) -> None:
    await message.answer("⏳ Анализирую ответы, подождите немного...")


@router.message(F.voice)
async def handle_unexpected_voice(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer(
            "Сначала выберите раздел экзамена.\n"
            "Нажмите /start для начала.",
        )
    else:
        await message.answer(
            "Сейчас я не жду голосового сообщения.\n"
            "Воспользуйтесь меню ниже.",
        )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_unexpected_text(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer(
            "Нажми /start, чтобы начать.",
        )
    elif current == SpeakingStates.choosing_part.state:
        await message.answer(
            "👇 Выбери раздел в меню ниже.",
            reply_markup=main_menu_keyboard(
                is_admin=_is_admin(message.from_user.id, message.from_user.username),
            ),
        )


# ── Utilities ────────────────────────────────────────────

def _split_message(text: str, limit: int = 4096) -> list[str]:
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
        BotCommand(command="start",  description="Главное меню"),
        BotCommand(command="help",   description="Справка"),
        BotCommand(command="cancel", description="Отменить текущую сессию"),
        BotCommand(command="webapp", description="Открыть веб-приложение"),
    ])


async def main() -> None:
    logger.info("Starting IELTS Speaking Practice bot...")
    await database.init_db()
    if ADMIN_USERNAME:
        uid = await database.get_user_id_by_username(ADMIN_USERNAME)
        if uid:
            _admin_ids.add(uid)
            logger.info("Admin user loaded: %s (id=%d)", ADMIN_USERNAME, uid)
    await _set_bot_commands()
    try:
        await dp.start_polling(bot)
    finally:
        await database.close_db()


if __name__ == "__main__":
    asyncio.run(main())
