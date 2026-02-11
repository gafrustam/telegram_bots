import asyncio
import logging
import os
import tempfile

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
)

from assessor import assess_part1, assess_part2, assess_part3, _get_duration_seconds
from formatter import format_assessment, format_error
from keyboards import (
    PART1_BTN,
    PART2_BTN,
    PART3_BTN,
    main_menu_keyboard,
    results_keyboard,
    topic_keyboard,
)
from questions import generate_session
from states import ResultAction, SpeakingStates, TopicAction
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

WELCOME_TEXT = (
    "🎓 <b>IELTS Speaking Practice</b>\n"
    "\n"
    "Я помогу вам подготовиться к IELTS Speaking.\n"
    "Выберите часть экзамена для тренировки:\n"
    "\n"
    "<b>Part 1</b> — Interview (вопросы на повседневные темы)\n"
    "<b>Part 2</b> — Long Turn (монолог 2 минуты по карточке)\n"
    "<b>Part 3</b> — Discussion (обсуждение абстрактных тем)\n"
    "\n"
    "Я задам вопросы, оценю ваши ответы по официальным\n"
    "IELTS Band Descriptors и дам рекомендации.\n"
    "\n"
    "👇 <b>Выберите раздел в меню ниже</b>"
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
    "  /start — Главное меню\n"
    "  /help  — Эта справка"
)

PROCESSING_TEXT = (
    "🎧 <b>Анализирую ваши ответы...</b>\n"
    "\n"
    "<i>Слушаю произношение, оцениваю грамматику,\n"
    "лексику и связность речи. Это может занять\n"
    "некоторое время.</i>"
)

PART_NAMES = {
    1: "Part 1 — Interview",
    2: "Part 2 — Long Turn",
    3: "Part 3 — Discussion",
}


# ── /start ───────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )
    await state.set_state(SpeakingStates.choosing_part)


# ── /help ────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)


# ── Part selection ───────────────────────────────────────

@router.message(SpeakingStates.choosing_part, F.text.in_({PART1_BTN, PART2_BTN, PART3_BTN}))
async def handle_part_selection(message: Message, state: FSMContext) -> None:
    part_map = {PART1_BTN: 1, PART2_BTN: 2, PART3_BTN: 3}
    part = part_map[message.text]

    await message.answer(
        "⏳ <i>Генерирую тему...</i>",
        parse_mode=ParseMode.HTML,
    )
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        session = await generate_session(part)
    except Exception:
        logger.exception("Failed to generate session")
        await message.answer(
            format_error("Не удалось сгенерировать тему. Попробуйте ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        return

    topic = session.get("topic", "General")
    questions = session.get("questions", [])
    cue_card = session.get("cue_card", "")

    await state.update_data(
        part=part,
        topic=topic,
        questions=questions,
        cue_card=cue_card,
        current_q_index=0,
        audio_file_ids=[],
        audio_durations=[],
    )

    text = (
        f"📝 <b>{PART_NAMES[part]}</b>\n"
        f"\n"
        f"Тема: <b>{topic}</b>\n"
    )
    if part == 2:
        text += f"\n{cue_card}\n"
    else:
        text += f"\nВам будет задано {len(questions)} вопросов.\n"

    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=topic_keyboard(),
    )
    await state.set_state(SpeakingStates.choosing_topic)


# ── Topic callbacks ──────────────────────────────────────

@router.callback_query(TopicAction.filter(F.action == "another"), SpeakingStates.choosing_topic)
async def handle_another_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]

    await callback.answer("Генерирую новую тему...")

    try:
        session = await generate_session(part)
    except Exception:
        logger.exception("Failed to generate session")
        await callback.answer("Ошибка генерации, попробуйте ещё раз", show_alert=True)
        return

    topic = session.get("topic", "General")
    questions = session.get("questions", [])
    cue_card = session.get("cue_card", "")

    await state.update_data(
        topic=topic,
        questions=questions,
        cue_card=cue_card,
    )

    text = (
        f"📝 <b>{PART_NAMES[part]}</b>\n"
        f"\n"
        f"Тема: <b>{topic}</b>\n"
    )
    if part == 2:
        text += f"\n{cue_card}\n"
    else:
        text += f"\nВам будет задано {len(questions)} вопросов.\n"

    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=topic_keyboard(),
    )


@router.callback_query(TopicAction.filter(F.action == "accept"), SpeakingStates.choosing_topic)
async def handle_accept_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if part == 2:
        await _start_part2(callback.message, state)
    else:
        answering_state = (
            SpeakingStates.part1_answering if part == 1
            else SpeakingStates.part3_answering
        )
        await state.set_state(answering_state)
        await _send_question(callback.message, state, 0)


# ── Part 2 start ─────────────────────────────────────────

async def _start_part2(message: Message, state: FSMContext) -> None:
    await state.set_state(SpeakingStates.part2_answering)
    await message.answer(
        "⏱ У вас <b>1 минута</b> на подготовку "
        "и до <b>2 минут</b> на ответ.\n"
        "\n"
        "В реальном IELTS экзамене экзаменатор остановит вас\n"
        "ровно через 2 минуты. Речь сверх 2 минут <b>не оценивается</b>.\n"
        "\n"
        "Если вы говорите значительно меньше 2 минут, это может\n"
        "снизить балл за Fluency & Coherence, так как на уровне\n"
        "Band 6+ требуется умение «говорить развёрнуто».\n"
        "\n"
        "🎤 Когда будете готовы — запишите голосовое сообщение.",
        parse_mode=ParseMode.HTML,
    )


# ── Send question via TTS ────────────────────────────────

async def _send_question(message: Message, state: FSMContext, index: int) -> None:
    data = await state.get_data()
    questions = data["questions"]
    question = questions[index]
    total = len(questions)

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        audio_bytes = await text_to_voice(question)
        voice_file = BufferedInputFile(audio_bytes, filename="question.ogg")
        await bot.send_voice(
            chat_id=message.chat.id,
            voice=voice_file,
            caption=f"Вопрос {index + 1}/{total}\n🎤 Ответьте голосовым сообщением.",
        )
    except Exception:
        logger.exception("TTS failed, sending text only")
        await message.answer(
            f"❓ <i>{question}</i>\n\n"
            f"🎤 Ответьте голосовым сообщением.",
            parse_mode=ParseMode.HTML,
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
                )

        response_text = format_assessment(result)
        await state.set_state(SpeakingStates.viewing_results)

        if len(response_text) <= 4096:
            await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)
        else:
            await status_msg.delete()
            for chunk in _split_message(response_text):
                await message.answer(chunk, parse_mode=ParseMode.HTML)

        await message.answer(
            "Что дальше?",
            reply_markup=results_keyboard(),
        )

    except Exception:
        logger.exception("Error during assessment")
        await status_msg.edit_text(
            format_error("Не удалось выполнить оценку. Попробуйте ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        await state.set_state(SpeakingStates.viewing_results)
        await message.answer(
            "Что дальше?",
            reply_markup=results_keyboard(),
        )


# ── Result callbacks ─────────────────────────────────────

@router.callback_query(ResultAction.filter(F.action == "retry"), SpeakingStates.viewing_results)
async def handle_retry(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]

    await state.update_data(
        audio_file_ids=[],
        audio_durations=[],
        current_q_index=0,
    )

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if part == 1:
        await state.set_state(SpeakingStates.part1_answering)
        await _send_question(callback.message, state, 0)
    elif part == 2:
        await _start_part2(callback.message, state)
    else:
        await state.set_state(SpeakingStates.part3_answering)
        await _send_question(callback.message, state, 0)


@router.callback_query(ResultAction.filter(F.action == "menu"), SpeakingStates.viewing_results)
async def handle_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    await callback.message.answer(
        "👇 Выберите раздел экзамена:",
        reply_markup=main_menu_keyboard(),
    )
    await state.set_state(SpeakingStates.choosing_part)


# ── Catch-all handlers ───────────────────────────────────

@router.message(SpeakingStates.part1_answering, F.text)
@router.message(SpeakingStates.part3_answering, F.text)
async def handle_text_during_qa(message: Message) -> None:
    await message.answer(
        "🎤 Пожалуйста, отправьте <b>голосовое сообщение</b>.",
        parse_mode=ParseMode.HTML,
    )


@router.message(SpeakingStates.part2_answering, F.text)
async def handle_text_during_part2(message: Message) -> None:
    await message.answer(
        "🎤 Запишите <b>голосовое сообщение</b> (до 2 минут).",
        parse_mode=ParseMode.HTML,
    )


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
            "Нажмите /start, чтобы начать.",
        )
    elif current == SpeakingStates.choosing_part.state:
        await message.answer(
            "👇 Выберите раздел в меню ниже.",
            reply_markup=main_menu_keyboard(),
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
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Справка"),
    ])


async def main() -> None:
    logger.info("Starting IELTS Speaking Practice bot...")
    await _set_bot_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
