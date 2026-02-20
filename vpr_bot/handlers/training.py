"""
Single-task training mode handlers.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import save_task_attempt
from generator import generate_task, generate_theory
from generator import evaluate_answer
from keyboards import kb_after_theory, kb_task_result
from states import VPRStates
from vpr_data import VPR_STRUCTURE, get_task_type

router = Router()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Select task type → generate task
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("task:"))
async def select_task_type(call: CallbackQuery, state: FSMContext) -> None:
    task_num = int(call.data.split(":")[1])
    user_data = await state.get_data()
    grade = user_data.get("grade")
    if not grade:
        await call.answer("Сначала выбери класс.", show_alert=True)
        return

    task_type = get_task_type(grade, task_num)

    # Loading message
    await call.message.edit_text(
        f"⏳ <b>Генерирую задание №{task_num}…</b>\n\n"
        f"Тема: {task_type['topic']}",
    )
    await call.answer()

    try:
        task = await generate_task(
            grade=grade,
            task_num=task_num,
            topic=task_type["topic"],
            hint=task_type["hint"],
        )
    except Exception as e:
        logger.error("Task generation failed: %s", e)
        from keyboards import kb_task_types
        await call.message.edit_text(
            "😕 Не удалось сгенерировать задание. Попробуй ещё раз.",
            reply_markup=kb_task_types(grade),
        )
        return

    await state.update_data(
        task_num=task_num,
        task_text=task["task_text"],
        correct_answer=task["correct_answer"],
        solution=task.get("solution", ""),
        max_points=task_type["max_points"],
    )
    await state.set_state(VPRStates.task_in_progress)

    vpr = VPR_STRUCTURE[grade]
    text = (
        f"📝 <b>Задание №{task_num} — {vpr['grade_name']}</b>\n"
        f"<i>{task_type['topic']}</i>\n"
        f"{'─' * 30}\n\n"
        f"{task['task_text']}\n\n"
        f"{'─' * 30}\n"
        f"✏️ <i>Напиши ответ в чат</i>"
    )
    await call.message.edit_text(text)


# ---------------------------------------------------------------------------
# User sends answer
# ---------------------------------------------------------------------------

@router.message(VPRStates.task_in_progress)
async def receive_answer(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    grade = user_data.get("grade")
    task_num = user_data.get("task_num")
    task_text = user_data.get("task_text", "")
    correct_answer = user_data.get("correct_answer", "")
    max_points = user_data.get("max_points", 2)
    user_answer = message.text.strip()

    # Evaluating…
    wait_msg = await message.answer("⏳ <b>Проверяю ответ…</b>")

    try:
        result = await evaluate_answer(task_text, correct_answer, user_answer, max_points)
    except Exception as e:
        logger.error("evaluate_answer failed: %s", e)
        await wait_msg.delete()
        await message.answer("😕 Ошибка при проверке. Попробуй ещё раз.")
        return

    points = result["points"]
    is_correct = result["is_correct"]
    verdict = result["verdict"]
    explanation = result["explanation"]

    # Save to DB
    task_type = get_task_type(grade, task_num)
    try:
        await save_task_attempt(
            user_id=message.from_user.id,
            grade=grade,
            task_num=task_num,
            task_topic=task_type["topic"],
            task_text=task_text,
            correct_answer=correct_answer,
            user_answer=user_answer,
            is_correct=is_correct,
            points_earned=points,
            points_max=max_points,
        )
    except Exception as e:
        logger.warning("save_task_attempt failed: %s", e)

    await wait_msg.delete()

    # Score bar
    filled = "🟩" * points
    empty = "⬜" * (max_points - points)
    score_bar = filled + empty

    result_text = (
        f"<b>{verdict}</b>\n\n"
        f"Твой ответ: <code>{user_answer}</code>\n"
        f"Правильный ответ: <code>{correct_answer}</code>\n\n"
        f"Баллы: {score_bar} <b>{points}/{max_points}</b>\n\n"
        f"💬 {explanation}"
    )

    await message.answer(
        result_text,
        reply_markup=kb_task_result(task_num),
    )


# ---------------------------------------------------------------------------
# Get theory
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("theory:"))
async def show_theory(call: CallbackQuery, state: FSMContext) -> None:
    task_num = int(call.data.split(":")[1])
    user_data = await state.get_data()
    grade = user_data.get("grade")
    if not grade:
        await call.answer("Сначала выбери класс.", show_alert=True)
        return

    task_type = get_task_type(grade, task_num)
    vpr = VPR_STRUCTURE[grade]

    await call.message.edit_text(
        f"⏳ <b>Готовлю теорию по заданию №{task_num}…</b>",
    )
    await call.answer()

    try:
        theory = await generate_theory(
            grade=grade,
            task_num=task_num,
            topic=task_type["topic"],
            hint=task_type["hint"],
        )
    except Exception as e:
        logger.error("Theory generation failed: %s", e)
        await call.message.edit_text(
            "😕 Не удалось загрузить теорию. Попробуй позже.",
            reply_markup=kb_after_theory(task_num),
        )
        return

    header = (
        f"💡 <b>Теория: задание №{task_num} — {vpr['grade_name']}</b>\n"
        f"<i>{task_type['topic']}</i>\n"
        f"{'─' * 30}\n\n"
    )

    # Telegram message limit is 4096 chars — split if needed
    full_text = header + theory
    if len(full_text) <= 4096:
        await call.message.edit_text(full_text, reply_markup=kb_after_theory(task_num))
    else:
        # Split: send header + first part, then continuation
        await call.message.edit_text(full_text[:4000] + "\n\n<i>(продолжение →)</i>")
        await call.message.answer(
            full_text[4000:],
            reply_markup=kb_after_theory(task_num),
        )
