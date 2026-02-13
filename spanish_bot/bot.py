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

import database
from assessor import (
    assess_conversation,
    generate_scenario,
    get_conversation_reply,
    transcribe_voice,
)
from difficulty import get_level, format_level_info
from formatter import (
    format_assessment,
    format_error,
    format_level_change,
    format_scenario,
    format_user_stats,
)
from keyboards import (
    END_BTN,
    LEVEL_DOWN_BTN,
    LEVEL_UP_BTN,
    NEW_DIALOG_BTN,
    conversation_keyboard,
    main_menu_keyboard,
    results_keyboard,
    topic_keyboard,
)
from states import ConversationStates, ResultAction, TopicAction
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
    "🇪🇸 <b>Spanish Conversation Practice</b>\n"
    "\n"
    "Практикуй разговорный испанский с ИИ-собеседником!\n"
    "\n"
    "Как это работает:\n"
    "1. Нажми <b>Nuevo dialogo</b> — получишь тему и словарь\n"
    "2. Нажми <b>Empezar</b> — бот начнёт разговор голосом\n"
    "3. Отвечай голосовыми сообщениями на испанском\n"
    "4. После диалога получишь подробную оценку\n"
    "\n"
    "Уровень подстраивается под тебя — повышай или понижай\n"
    "сложность кнопками в меню.\n"
    "\n"
    "👇 <b>Начни прямо сейчас!</b>"
)

HELP_TEXT = (
    "📖 <b>Справка</b>\n"
    "\n"
    "<b>Как пользоваться:</b>\n"
    "  1. Нажми «Nuevo dialogo» в меню\n"
    "  2. Посмотри тему и словарь, нажми «Empezar»\n"
    "  3. Бот начнёт разговор голосом — отвечай голосовыми\n"
    "  4. После всех обменов или нажатия «Terminar» — оценка\n"
    "\n"
    "<b>Уровни:</b>\n"
    "  25 уровней от A0 до C2\n"
    "  📈 Subir dificultad — повысить\n"
    "  📉 Bajar dificultad — понизить\n"
    "\n"
    "<b>Советы:</b>\n"
    "  • Говори в тихом месте\n"
    "  • Старайся использовать предложенные слова\n"
    "  • Не бойся ошибок — бот мягко поправит\n"
    "\n"
    "<b>Команды:</b>\n"
    "  /start   — Главное меню\n"
    "  /help    — Эта справка\n"
    "  /mystats — Моя статистика"
)

PROCESSING_TEXT = (
    "🎧 <b>Анализирую разговор...</b>\n"
    "\n"
    "<i>Оцениваю произношение, грамматику, словарный запас\n"
    "и общее понимание. Это может занять некоторое время.</i>"
)


# ── /start ───────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    await database.upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    level_num = await database.get_user_level(user.id)
    level_info = format_level_info(level_num)

    await message.answer(
        WELCOME_TEXT + f"\n\n🎓 <b>{level_info}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )
    await state.set_state(ConversationStates.menu)


# ── /help ────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)


# ── /mystats ─────────────────────────────────────────────

@router.message(Command("mystats"))
async def cmd_mystats(message: Message) -> None:
    if not database.is_available():
        await message.answer("⚠️ База данных недоступна.", parse_mode=ParseMode.HTML)
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    stats = await database.get_user_stats(message.from_user.id)
    if stats is None:
        await message.answer(
            "📊 <b>Статистика</b>\n\n"
            "У тебя пока нет завершённых диалогов.\n"
            "Нажми «Nuevo dialogo», чтобы начать!",
            parse_mode=ParseMode.HTML,
        )
        return

    recent = await database.get_user_recent_assessments(message.from_user.id)
    text = format_user_stats(stats, recent)
    await message.answer(text, parse_mode=ParseMode.HTML)


# ── Level up/down ────────────────────────────────────────

@router.message(ConversationStates.menu, F.text == LEVEL_UP_BTN)
async def handle_level_up(message: Message, state: FSMContext) -> None:
    await _change_level(message, +1)


@router.message(ConversationStates.menu, F.text == LEVEL_DOWN_BTN)
async def handle_level_down(message: Message, state: FSMContext) -> None:
    await _change_level(message, -1)


async def _change_level(message: Message, delta: int) -> None:
    old_level = await database.get_user_level(message.from_user.id)
    new_level = max(1, min(25, old_level + delta))

    if new_level == old_level:
        direction = "максимальный" if delta > 0 else "минимальный"
        await message.answer(
            f"Уже {direction} уровень!",
            parse_mode=ParseMode.HTML,
        )
        return

    await database.set_user_level(message.from_user.id, new_level)
    lvl = get_level(new_level)
    text = format_level_change(old_level, new_level, lvl.label, lvl.cefr)
    await message.answer(text, parse_mode=ParseMode.HTML)


# ── Nuevo dialogo ────────────────────────────────────────

@router.message(ConversationStates.menu, F.text == NEW_DIALOG_BTN)
async def handle_new_dialog(message: Message, state: FSMContext) -> None:
    await _generate_and_show_scenario(message, state)


async def _generate_and_show_scenario(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    level_num = await database.get_user_level(user_id)
    level = get_level(level_num)

    await message.answer("⏳ <i>Генерирую тему...</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        scenario_data = await generate_scenario(level)
    except Exception:
        logger.exception("Failed to generate scenario")
        await message.answer(
            format_error("Не удалось сгенерировать тему. Попробуй ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        return

    topic = scenario_data.get("topic", "Conversacion")
    scenario_text = scenario_data.get("scenario", "")
    vocabulary = scenario_data.get("vocabulary", [])
    opening_line = scenario_data.get("opening_line", "Hola!")

    await state.update_data(
        level_num=level_num,
        topic=topic,
        scenario=scenario_text,
        vocabulary=vocabulary,
        opening_line=opening_line,
        conversation_history=[],
        user_audio_file_ids=[],
        exchange_count=0,
        db_conversation_id=None,
    )

    text = format_scenario(topic, scenario_text, vocabulary)
    text += f"\n\n🎓 <b>Nivel {level.level} — {level.label} ({level.cefr})</b>"
    text += f"\n💬 Обменов: {level.exchanges}"

    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=topic_keyboard(),
    )
    await state.set_state(ConversationStates.viewing_vocab)


# ── Topic callbacks ──────────────────────────────────────

@router.callback_query(TopicAction.filter(F.action == "another"), ConversationStates.viewing_vocab)
async def handle_another_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    level_num = data.get("level_num", 3)
    level = get_level(level_num)

    await callback.answer("Генерирую новую тему...")

    try:
        scenario_data = await generate_scenario(level)
    except Exception:
        logger.exception("Failed to generate scenario")
        await callback.answer("Ошибка генерации, попробуй ещё раз", show_alert=True)
        return

    topic = scenario_data.get("topic", "Conversacion")
    scenario_text = scenario_data.get("scenario", "")
    vocabulary = scenario_data.get("vocabulary", [])
    opening_line = scenario_data.get("opening_line", "Hola!")

    await state.update_data(
        topic=topic,
        scenario=scenario_text,
        vocabulary=vocabulary,
        opening_line=opening_line,
    )

    text = format_scenario(topic, scenario_text, vocabulary)
    text += f"\n\n🎓 <b>Nivel {level.level} — {level.label} ({level.cefr})</b>"
    text += f"\n💬 Обменов: {level.exchanges}"

    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=topic_keyboard(),
    )


@router.callback_query(TopicAction.filter(F.action == "start"), ConversationStates.viewing_vocab)
async def handle_start_conversation(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    level_num = data["level_num"]
    topic = data["topic"]
    scenario = data["scenario"]
    vocabulary = data["vocabulary"]
    opening_line = data["opening_line"]

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    # Create DB conversation
    db_conv_id = await database.create_conversation(
        user_id=callback.from_user.id,
        level=level_num,
        topic=topic,
        scenario=scenario,
    )
    await state.update_data(db_conversation_id=db_conv_id)

    # Save vocabulary to DB
    await database.save_vocabulary(
        user_id=callback.from_user.id,
        conversation_id=db_conv_id,
        words=vocabulary,
    )

    # Initialize conversation history with the opening line
    history = [{"role": "assistant", "content": opening_line}]
    await state.update_data(
        conversation_history=history,
        exchange_count=0,
    )

    # Save bot's opening message to DB
    await database.save_message(
        conversation_id=db_conv_id,
        role="bot",
        text=opening_line,
        audio_file_id=None,
        seq_num=0,
    )

    # Send opening line as voice + text
    await bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    try:
        audio_bytes = await text_to_voice(opening_line)
        voice_file = BufferedInputFile(audio_bytes, filename="bot_reply.ogg")
        await bot.send_voice(
            chat_id=callback.message.chat.id,
            voice=voice_file,
            caption=f"🤖 {opening_line}",
            reply_markup=conversation_keyboard(),
        )
    except Exception:
        logger.exception("TTS failed for opening line")
        await callback.message.answer(
            f"🤖 <i>{opening_line}</i>\n\n🎤 Отвечай голосовым сообщением.",
            parse_mode=ParseMode.HTML,
            reply_markup=conversation_keyboard(),
        )

    await state.set_state(ConversationStates.conversing)


# ── Conversation: voice handler ──────────────────────────

@router.message(ConversationStates.conversing, F.voice)
async def handle_voice_in_conversation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    level_num = data["level_num"]
    level = get_level(level_num)
    history = data["conversation_history"]
    audio_ids = data["user_audio_file_ids"]
    exchange_count = data["exchange_count"]
    db_conv_id = data.get("db_conversation_id")
    scenario = data["scenario"]

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Download and transcribe user's voice
    file = await bot.get_file(message.voice.file_id)
    voice_data = await bot.download_file(file.file_path)
    ogg_bytes = voice_data.read()

    try:
        user_text = await transcribe_voice(ogg_bytes)
    except Exception:
        logger.exception("Whisper transcription failed")
        await message.answer(
            "⚠️ Не удалось распознать голос. Попробуй ещё раз.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Show transcription to user
    await message.answer(
        f"🗣 <i>{user_text}</i>",
        parse_mode=ParseMode.HTML,
    )

    # Save user audio file ID and update history
    audio_ids.append(message.voice.file_id)
    history.append({"role": "user", "content": user_text})
    exchange_count += 1

    # Save user message to DB
    seq_num = len(history) - 1
    await database.save_message(
        conversation_id=db_conv_id,
        role="user",
        text=user_text,
        audio_file_id=message.voice.file_id,
        seq_num=seq_num,
    )

    # Check if we've reached max exchanges
    if exchange_count >= level.exchanges:
        await state.update_data(
            conversation_history=history,
            user_audio_file_ids=audio_ids,
            exchange_count=exchange_count,
        )
        await message.answer(
            "✅ Диалог завершён! Анализирую...",
            parse_mode=ParseMode.HTML,
        )
        await _run_assessment(message, state)
        return

    # Get bot reply
    exchanges_left = level.exchanges - exchange_count
    try:
        bot_reply = await get_conversation_reply(
            history=history,
            level=level,
            scenario=scenario,
            exchanges_left=exchanges_left,
        )
    except Exception:
        logger.exception("Failed to get conversation reply")
        await message.answer(
            "⚠️ Ошибка генерации ответа. Завершаю диалог для оценки...",
            parse_mode=ParseMode.HTML,
        )
        await state.update_data(
            conversation_history=history,
            user_audio_file_ids=audio_ids,
            exchange_count=exchange_count,
        )
        await _run_assessment(message, state)
        return

    history.append({"role": "assistant", "content": bot_reply})

    # Save bot message to DB
    await database.save_message(
        conversation_id=db_conv_id,
        role="bot",
        text=bot_reply,
        audio_file_id=None,
        seq_num=len(history) - 1,
    )

    await state.update_data(
        conversation_history=history,
        user_audio_file_ids=audio_ids,
        exchange_count=exchange_count,
    )

    # Send bot reply as voice + text
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        audio_bytes = await text_to_voice(bot_reply)
        voice_file = BufferedInputFile(audio_bytes, filename="bot_reply.ogg")
        await bot.send_voice(
            chat_id=message.chat.id,
            voice=voice_file,
            caption=f"🤖 {bot_reply}\n\n💬 {exchanges_left - 1} обменов осталось",
        )
    except Exception:
        logger.exception("TTS failed for bot reply")
        await message.answer(
            f"🤖 <i>{bot_reply}</i>\n\n"
            f"💬 {exchanges_left - 1} обменов осталось\n"
            "🎤 Отвечай голосовым сообщением.",
            parse_mode=ParseMode.HTML,
        )


# ── Conversation: "Terminar" button ─────────────────────

@router.message(ConversationStates.conversing, F.text == END_BTN)
async def handle_end_conversation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("user_audio_file_ids"):
        await message.answer(
            "Отправь хотя бы одно голосовое сообщение перед завершением.",
            parse_mode=ParseMode.HTML,
        )
        return

    await message.answer(
        "✅ Завершаю диалог и анализирую...",
        parse_mode=ParseMode.HTML,
    )
    await _run_assessment(message, state)


# ── Assessment ───────────────────────────────────────────

async def _run_assessment(message: Message, state: FSMContext) -> None:
    await state.set_state(ConversationStates.assessing)
    status_msg = await message.answer(PROCESSING_TEXT, parse_mode=ParseMode.HTML)

    data = await state.get_data()
    level_num = data["level_num"]
    level = get_level(level_num)
    history = data["conversation_history"]
    audio_ids = data["user_audio_file_ids"]
    exchange_count = data["exchange_count"]
    db_conv_id = data.get("db_conversation_id")
    scenario = data["scenario"]

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        # Download all user audio files
        with tempfile.TemporaryDirectory() as tmp_dir:
            ogg_paths = []
            for i, file_id in enumerate(audio_ids):
                file = await bot.get_file(file_id)
                path = os.path.join(tmp_dir, f"user_{i}.oga")
                await bot.download_file(file.file_path, path)
                ogg_paths.append(path)

            result = await assess_conversation(
                ogg_paths=ogg_paths,
                history=history,
                level=level,
                scenario=scenario,
                exchange_count=exchange_count,
            )

        response_text = format_assessment(result)

        # Save to database
        await database.complete_conversation(db_conv_id, exchange_count)
        await database.save_assessment(
            conversation_id=db_conv_id,
            user_id=message.from_user.id,
            result=result,
        )

        await state.set_state(ConversationStates.viewing_results)

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
        await database.fail_conversation(db_conv_id)
        await status_msg.edit_text(
            format_error("Не удалось выполнить оценку. Попробуй ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        await state.set_state(ConversationStates.viewing_results)
        await message.answer(
            "Что дальше?",
            reply_markup=results_keyboard(),
        )


# ── Result callbacks ─────────────────────────────────────

@router.callback_query(ResultAction.filter(F.action == "new"), ConversationStates.viewing_results)
async def handle_result_new(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    await state.set_state(ConversationStates.menu)

    # Generate new scenario directly
    user_id = callback.from_user.id
    level_num = await database.get_user_level(user_id)
    level = get_level(level_num)

    await callback.message.answer(
        "⏳ <i>Генерирую тему...</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )
    await bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    try:
        scenario_data = await generate_scenario(level)
    except Exception:
        logger.exception("Failed to generate scenario")
        await callback.message.answer(
            format_error("Не удалось сгенерировать тему. Попробуй ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        return

    topic = scenario_data.get("topic", "Conversacion")
    scenario_text = scenario_data.get("scenario", "")
    vocabulary = scenario_data.get("vocabulary", [])
    opening_line = scenario_data.get("opening_line", "Hola!")

    await state.update_data(
        level_num=level_num,
        topic=topic,
        scenario=scenario_text,
        vocabulary=vocabulary,
        opening_line=opening_line,
        conversation_history=[],
        user_audio_file_ids=[],
        exchange_count=0,
        db_conversation_id=None,
    )

    text = format_scenario(topic, scenario_text, vocabulary)
    text += f"\n\n🎓 <b>Nivel {level.level} — {level.label} ({level.cefr})</b>"
    text += f"\n💬 Обменов: {level.exchanges}"

    await callback.message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=topic_keyboard(),
    )
    await state.set_state(ConversationStates.viewing_vocab)


@router.callback_query(ResultAction.filter(F.action == "menu"), ConversationStates.viewing_results)
async def handle_result_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()

    level_num = await database.get_user_level(callback.from_user.id)
    level_info = format_level_info(level_num)

    await callback.message.answer(
        f"👇 Выбери действие в меню.\n\n🎓 <b>{level_info}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )
    await state.set_state(ConversationStates.menu)


# ── Catch-all handlers ───────────────────────────────────

@router.message(ConversationStates.conversing, F.text)
async def handle_text_during_conversation(message: Message) -> None:
    if message.text == END_BTN:
        return  # handled above
    await message.answer(
        "🎤 Отправь <b>голосовое сообщение</b> на испанском.",
        parse_mode=ParseMode.HTML,
    )


@router.message(F.voice)
async def handle_unexpected_voice(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нажми /start, чтобы начать.")
    else:
        await message.answer(
            "Сейчас я не жду голосового сообщения.\n"
            "Нажми «Nuevo dialogo» для начала диалога.",
        )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_unexpected_text(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нажми /start, чтобы начать.")
    elif current == ConversationStates.menu.state:
        await message.answer(
            "👇 Используй кнопки меню.",
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
        BotCommand(command="mystats", description="Моя статистика"),
    ])


async def main() -> None:
    logger.info("Starting Spanish Conversation Practice bot...")
    await database.init_db()
    await _set_bot_commands()
    try:
        await dp.start_polling(bot)
    finally:
        await database.close_db()


if __name__ == "__main__":
    asyncio.run(main())
