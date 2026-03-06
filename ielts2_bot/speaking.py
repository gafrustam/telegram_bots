"""Speaking section — full Telegram-based IELTS Speaking Practice."""
import asyncio
import logging
import os
import re
import tempfile

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import database
from assessor import assess_part1, assess_part2, assess_part3, _get_duration_seconds
from formatter import format_assessment, format_error
from keyboards import (
    ADMIN_BTN,
    MENU_BTN,
    PART1_BTN,
    PART2_BTN,
    PART3_BTN,
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

logger = logging.getLogger(__name__)

router = Router()

PART_NAMES = {
    1: "Part 1 — Interview",
    2: "Part 2 — Long Turn",
    3: "Part 3 — Discussion",
}

PART_INSTRUCTIONS = {
    1: (
        "Эта часть имитирует интервью с экзаменатором на знакомые "
        "повседневные темы: дом, работа, учёба, хобби, путешествия.\n\n"
        "Отвечай развёрнуто (<b>~20–30 секунд</b> на вопрос), "
        "избегай односложных ответов.\n\n"
        "🎤 На каждый вопрос отправляй отдельное голосовое сообщение."
    ),
    2: (
        "Индивидуальный монолог (Long Turn). "
        "Ты получаешь карточку с темой и пунктами.\n\n"
        "На реальном экзамене: <b>1 минута</b> на подготовку, "
        "<b>2 минуты</b> на ответ. Речь сверх 2 минут не оценивается. "
        "Менее ~1:30 может снизить балл за Fluency.\n\n"
        "🎤 Когда будешь готов — запиши одно голосовое сообщение."
    ),
    3: (
        "Двусторонняя дискуссия на абстрактные темы.\n\n"
        "Аргументируй, сравнивай, рассуждай. "
        "Отвечай развёрнуто (<b>~30–60 секунд</b> на вопрос).\n\n"
        "🎤 На каждый вопрос отправляй отдельное голосовое сообщение."
    ),
}

PROCESSING_TEXT = (
    "🎧 <b>Анализирую ваши ответы...</b>\n\n"
    "<i>Слушаю произношение, оцениваю грамматику, лексику "
    "и связность речи. Это может занять некоторое время.</i>"
)


# ── Helpers ──────────────────────────────────────────────

def _is_admin(username: str | None) -> bool:
    from config import ADMIN_USERNAME
    return bool(ADMIN_USERNAME) and bool(username) and username.lower() == ADMIN_USERNAME


async def _generate_topic_session(
    part: int, user_id: int, related_topic: str | None = None,
) -> dict:
    bank_topic = await database.get_random_topic(part, user_id)
    if bank_topic:
        topic_name = bank_topic["topic"]
        session = await generate_session(
            part,
            topic=topic_name,
            cue_card_template=bank_topic.get("cue_card") if part == 2 else None,
            related_topic=related_topic if part == 3 else None,
        )
        session.setdefault("topic", topic_name)
    else:
        session = await generate_session(part, related_topic=related_topic if part == 3 else None)
    return session


def _split_message(text: str, limit: int = 4096) -> list[str]:
    chunks, current = [], ""
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


# ── Part selection ───────────────────────────────────────

@router.message(SpeakingStates.choosing_part, F.text.in_({PART1_BTN, PART2_BTN, PART3_BTN}))
async def handle_part_selection(message: Message, state: FSMContext) -> None:
    part = {PART1_BTN: 1, PART2_BTN: 2, PART3_BTN: 3}[message.text]
    await state.update_data(part=part, current_q_index=0, audio_file_ids=[], audio_durations=[])
    text = f"📝 <b>{PART_NAMES[part]}</b>\n\n{PART_INSTRUCTIONS[part]}"
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=start_keyboard())
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

    gen_id = await database.save_generated_topic(
        user_id=callback.from_user.id, part=part, topic=topic,
        questions=questions or None, cue_card=cue_card or None,
    )
    await state.update_data(topic=topic, questions=questions, cue_card=cue_card, gen_topic_id=gen_id)

    text = f"📝 <b>{PART_NAMES[part]}</b>\n\nТема: <b>{topic}</b>\n"
    if part != 2:
        text += f"\nВопросов: {len(questions)}\n"
    text += f"\n{PART_INSTRUCTIONS[part]}"
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=topic_keyboard())


@router.callback_query(TopicAction.filter(F.action == "accept"), SpeakingStates.choosing_topic)
async def handle_accept_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    wait_msg = await callback.message.answer("⏳ <i>Генерирую тему...</i>", parse_mode=ParseMode.HTML)
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    related_topic = None
    if part == 3:
        related_topic = await database.get_last_part2_topic(callback.from_user.id)

    try:
        session = await _generate_topic_session(part, callback.from_user.id, related_topic)
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

    gen_id = await database.save_generated_topic(
        user_id=callback.from_user.id, part=part, topic=topic,
        questions=questions or None, cue_card=cue_card or None,
    )
    await database.mark_topic_accepted(gen_id)

    db_session_id = await database.create_session(
        user_id=callback.from_user.id, part=part, topic=topic,
        questions=questions or None, cue_card=cue_card or None,
        topic_id=gen_id,
    )
    await state.update_data(
        topic=topic, questions=questions, cue_card=cue_card,
        gen_topic_id=gen_id, db_session_id=db_session_id,
    )
    await wait_msg.delete()

    if part == 2:
        asyncio.create_task(_start_part2_countdown(
            callback.message.chat.id, state, callback.message.bot,
        ))
    else:
        await state.set_state(SpeakingStates.part1_answering if part == 1 else SpeakingStates.part3_answering)
        await _send_question(callback.message, state, 0)


# ── Custom topic ─────────────────────────────────────────

@router.callback_query(TopicAction.filter(F.action == "custom"), SpeakingStates.choosing_topic)
async def handle_custom_topic(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if part == 2:
        example = (
            "✏️ <b>Своя тема</b>\n\nОтправь тему и карточку:\n\n"
            "<code>Topic: A memorable trip\n"
            "Describe a memorable trip you took.\nYou should say:\n"
            "- where you went\n- who you went with\n- what you did\n"
            "and explain why it was memorable.</code>"
        )
    else:
        example = (
            "✏️ <b>Своя тема</b>\n\nОтправь тему и вопросы:\n\n"
            "<code>Topic: Technology\n"
            "1. How often do you use technology?\n"
            "2. What is your favorite gadget?\n"
            "3. Has technology changed how you communicate?\n"
            "4. Do we rely too much on technology?</code>"
        )
    await callback.message.answer(example, parse_mode=ParseMode.HTML)
    await state.set_state(SpeakingStates.entering_custom_topic)


@router.message(SpeakingStates.entering_custom_topic, F.text)
async def handle_custom_topic_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]
    lines = message.text.strip().split("\n")
    topic = "Custom topic"
    content_lines = []
    for line in lines:
        s = line.strip()
        if s.lower().startswith("topic:"):
            topic = s[6:].strip()
        else:
            content_lines.append(s)
    while content_lines and not content_lines[0]:
        content_lines.pop(0)

    questions, cue_card = [], ""
    if part == 2:
        cue_card = "\n".join(content_lines).strip()
        if not cue_card:
            await message.answer("Не удалось распознать карточку. Попробуй ещё раз в формате выше.")
            return
    else:
        for line in content_lines:
            cleaned = re.sub(r"^\d+[\.\)\-\s]+", "", line).strip()
            if cleaned:
                questions.append(cleaned)
        if len(questions) < 2:
            await message.answer("Нужно минимум 2 вопроса. Попробуй ещё раз в формате выше.")
            return

    gen_id = await database.save_generated_topic(
        user_id=message.from_user.id, part=part, topic=topic,
        questions=questions or None, cue_card=cue_card or None,
    )
    await database.mark_topic_accepted(gen_id)

    db_session_id = await database.create_session(
        user_id=message.from_user.id, part=part, topic=topic,
        questions=questions or None, cue_card=cue_card or None,
        topic_id=gen_id,
    )
    await state.update_data(
        topic=topic, questions=questions, cue_card=cue_card,
        gen_topic_id=gen_id, db_session_id=db_session_id,
        current_q_index=0, audio_file_ids=[], audio_durations=[],
    )

    preview = f"📝 <b>{PART_NAMES[part]}</b>\n\nТема: <b>{topic}</b>\n"
    preview += f"\n{cue_card}\n" if part == 2 else f"\nВопросов: {len(questions)}\n"
    await message.answer(preview + "\n✅ Тема принята! Начинаем.", parse_mode=ParseMode.HTML)

    if part == 2:
        asyncio.create_task(_start_part2_countdown(message.chat.id, state, message.bot))
    else:
        await state.set_state(SpeakingStates.part1_answering if part == 1 else SpeakingStates.part3_answering)
        await _send_question(message, state, 0)


# ── Part 2 countdown ─────────────────────────────────────

async def _start_part2_countdown(chat_id: int, state: FSMContext, bot: Bot) -> None:
    await state.set_state(SpeakingStates.part2_preparing)
    data = await state.get_data()
    cue_card = data.get("cue_card", "")

    def _build(label: str) -> str:
        t = f"⏱ <b>Подготовка: {label}</b>"
        if cue_card:
            t += f"\n\n📋 <b>Карточка:</b>\n{cue_card}"
        t += "\n\n<i>Когда будешь готов — запиши голосовое сообщение.</i>"
        return t

    msg = await bot.send_message(chat_id, _build("1:00"), parse_mode=ParseMode.HTML)

    for remaining in range(55, 0, -5):
        await asyncio.sleep(5)
        if await state.get_state() != SpeakingStates.part2_preparing.state:
            return
        m, s = divmod(remaining, 60)
        try:
            await bot.edit_message_text(_build(f"{m}:{s:02d}"), chat_id, msg.message_id, parse_mode=ParseMode.HTML)
        except Exception:
            pass

    await asyncio.sleep(5)
    if await state.get_state() != SpeakingStates.part2_preparing.state:
        return

    await state.set_state(SpeakingStates.part2_answering)
    end = "⏱ <b>Время подготовки вышло!</b>"
    if cue_card:
        end += f"\n\n📋 <b>Карточка:</b>\n{cue_card}"
    end += "\n\n🎤 Запиши голосовое сообщение (до 2 минут)."
    try:
        await bot.edit_message_text(end, chat_id, msg.message_id, parse_mode=ParseMode.HTML)
    except Exception:
        await bot.send_message(chat_id, end, parse_mode=ParseMode.HTML)


# ── Send question via TTS ────────────────────────────────

async def _send_question(message: Message, state: FSMContext, index: int) -> None:
    data = await state.get_data()
    questions = data["questions"]
    question = questions[index]
    total = len(questions)

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    caption = f"Вопрос {index + 1}/{total}\n\n🎤 Ответьте голосовым сообщением."

    try:
        audio_bytes = await text_to_voice(question)
        voice_file = BufferedInputFile(audio_bytes, filename="question.ogg")
        sent = await message.bot.send_voice(
            chat_id=message.chat.id,
            voice=voice_file,
            caption=caption,
            reply_markup=question_keyboard(),
        )
        await state.update_data(last_question_voice_id=sent.voice.file_id)
    except Exception:
        logger.exception("TTS failed, sending text fallback")
        await message.answer(
            f"❓ Вопрос {index + 1}/{total}: <i>{question}</i>\n\n🎤 Ответьте голосовым сообщением.",
            parse_mode=ParseMode.HTML,
        )


# ── Replay question ──────────────────────────────────────

@router.callback_query(QuestionAction.filter(F.action == "replay"))
async def handle_question_replay(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    voice_id = data.get("last_question_voice_id")
    if not voice_id:
        await callback.answer("Аудио недоступно", show_alert=True)
        return
    await callback.message.bot.send_voice(
        chat_id=callback.message.chat.id,
        voice=voice_id,
        caption="🔄 Повтор вопроса\n\n🎤 Ответьте голосовым сообщением.",
        reply_markup=question_keyboard(),
    )


# ── Voice handlers ───────────────────────────────────────

@router.message(SpeakingStates.part1_answering, F.voice)
async def handle_part1_voice(message: Message, state: FSMContext) -> None:
    await _handle_qa_voice(message, state)


@router.message(SpeakingStates.part3_answering, F.voice)
async def handle_part3_voice(message: Message, state: FSMContext) -> None:
    await _handle_qa_voice(message, state)


async def _handle_qa_voice(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    audio_ids = data["audio_file_ids"]
    durations = data["audio_durations"]
    index = data["current_q_index"]

    audio_ids.append(message.voice.file_id)
    durations.append(message.voice.duration or 0)
    index += 1
    await state.update_data(audio_file_ids=audio_ids, audio_durations=durations, current_q_index=index)

    if index < len(data["questions"]):
        await _send_question(message, state, index)
    else:
        await _run_assessment(message, state)


@router.message(SpeakingStates.part2_preparing, F.voice)
async def handle_part2_voice_early(message: Message, state: FSMContext) -> None:
    await state.set_state(SpeakingStates.part2_answering)
    await handle_part2_voice(message, state)


@router.message(SpeakingStates.part2_answering, F.voice)
async def handle_part2_voice(message: Message, state: FSMContext) -> None:
    duration = message.voice.duration or 0
    await state.update_data(audio_file_ids=[message.voice.file_id], audio_durations=[duration])
    if duration > 120:
        mins, secs = duration // 60, duration % 60
        await message.answer(
            f"Ваш ответ: <b>{mins}:{secs:02d}</b>. Будут оценены первые 2 минуты.",
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
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        with tempfile.TemporaryDirectory() as tmp:
            ogg_paths = []
            for i, file_id in enumerate(data["audio_file_ids"]):
                file = await message.bot.get_file(file_id)
                path = os.path.join(tmp, f"r{i}.oga")
                await message.bot.download_file(file.file_path, path)
                ogg_paths.append(path)

            if part == 1:
                result = await assess_part1(ogg_paths, data["questions"], data["topic"],
                                            durations=data.get("audio_durations"))
            elif part == 2:
                duration = await asyncio.to_thread(_get_duration_seconds, ogg_paths[0])
                result = await assess_part2(ogg_paths[0], data["cue_card"], duration)
            else:
                result = await assess_part3(ogg_paths, data["questions"], data["topic"],
                                            durations=data.get("audio_durations"))

        response_text = format_assessment(result)
        audio_total = sum(data.get("audio_durations", []))
        await database.complete_session(db_session_id, audio_total)
        await database.save_assessment(session_id=db_session_id, user_id=message.from_user.id, result=result)
        await state.set_state(SpeakingStates.viewing_results)

        if len(response_text) <= 4096:
            await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)
        else:
            await status_msg.delete()
            for chunk in _split_message(response_text):
                await message.answer(chunk, parse_mode=ParseMode.HTML)

        await message.answer(
            "Попробуй ещё раз ту же тему или вернись в главное меню 👇",
            reply_markup=results_keyboard(),
        )

    except Exception:
        logger.exception("Assessment error")
        await database.fail_session(db_session_id)
        await status_msg.edit_text(
            format_error("Не удалось выполнить оценку. Попробуйте ещё раз."),
            parse_mode=ParseMode.HTML,
        )
        await state.set_state(SpeakingStates.viewing_results)
        await message.answer("Можешь попробовать ещё раз или вернуться в меню 👇", reply_markup=results_keyboard())


# ── Results callbacks ────────────────────────────────────

@router.callback_query(ResultAction.filter(F.action == "retry"), SpeakingStates.viewing_results)
async def handle_retry(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    part = data["part"]
    db_session_id = await database.create_session(
        user_id=callback.from_user.id, part=part,
        topic=data["topic"], questions=data.get("questions") or None,
        cue_card=data.get("cue_card") or None,
    )
    await state.update_data(audio_file_ids=[], audio_durations=[], current_q_index=0, db_session_id=db_session_id)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if part == 1:
        await state.set_state(SpeakingStates.part1_answering)
        await _send_question(callback.message, state, 0)
    elif part == 2:
        asyncio.create_task(_start_part2_countdown(callback.message.chat.id, state, callback.message.bot))
    else:
        await state.set_state(SpeakingStates.part3_answering)
        await _send_question(callback.message, state, 0)


@router.callback_query(ResultAction.filter(F.action == "menu"), SpeakingStates.viewing_results)
async def handle_back_to_menu_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    is_admin = _is_admin(callback.from_user.username)
    await callback.message.answer(
        "👇 Выбери раздел экзамена:",
        reply_markup=main_menu_keyboard(is_admin=is_admin),
    )


# ── Interrupt: part button pressed during active session ──

PART_MAP = {PART1_BTN: 1, PART2_BTN: 2, PART3_BTN: 3}
SOFT_STATES = {
    SpeakingStates.choosing_topic.state,
    SpeakingStates.entering_custom_topic.state,
    SpeakingStates.viewing_results.state,
}


@router.message(F.text.in_({PART1_BTN, PART2_BTN, PART3_BTN}))
async def handle_part_button(message: Message, state: FSMContext) -> None:
    current = await state.get_state()

    if current is None or current == SpeakingStates.choosing_part.state:
        await state.set_state(SpeakingStates.choosing_part)
        await handle_part_selection(message, state)
        return

    if current in SOFT_STATES:
        await state.clear()
        await state.set_state(SpeakingStates.choosing_part)
        await handle_part_selection(message, state)
        return

    data = await state.get_data()
    current_part = data.get("part")
    new_part = PART_MAP[message.text]
    if current_part:
        await message.answer(
            f"⚠️ У тебя уже начата <b>{PART_NAMES[current_part]}</b>.\nЧто хочешь сделать?",
            parse_mode=ParseMode.HTML,
            reply_markup=interrupt_keyboard(new_part),
        )
    else:
        await state.clear()
        await state.set_state(SpeakingStates.choosing_part)
        await handle_part_selection(message, state)


@router.callback_query(InterruptAction.filter(F.action == "continue"))
async def handle_interrupt_continue(callback: CallbackQuery) -> None:
    await callback.answer("Продолжаем!")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(InterruptAction.filter(F.action == "new"))
async def handle_interrupt_new(callback: CallbackQuery, callback_data: InterruptAction, state: FSMContext) -> None:
    data = await state.get_data()
    if sid := data.get("db_session_id"):
        await database.fail_session(sid)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    new_part = callback_data.new_part
    await state.clear()
    await state.update_data(part=new_part, current_q_index=0, audio_file_ids=[], audio_durations=[])
    await callback.message.answer(
        f"📝 <b>{PART_NAMES[new_part]}</b>\n\n{PART_INSTRUCTIONS[new_part]}",
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )
    await state.set_state(SpeakingStates.choosing_topic)


# ── Catch-alls inside speaking ───────────────────────────

@router.message(SpeakingStates.part1_answering, F.text)
@router.message(SpeakingStates.part3_answering, F.text)
async def handle_text_during_qa(message: Message) -> None:
    await message.answer("🎤 Пожалуйста, отправь <b>голосовое сообщение</b>.", parse_mode=ParseMode.HTML)


@router.message(SpeakingStates.part2_answering, F.text)
async def handle_text_during_p2(message: Message) -> None:
    await message.answer("🎤 Запиши <b>голосовое сообщение</b> (до 2 минут).", parse_mode=ParseMode.HTML)


@router.message(SpeakingStates.assessing)
async def handle_during_assessing(message: Message) -> None:
    await message.answer("⏳ Анализирую ответы, подождите немного...")
