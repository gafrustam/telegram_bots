"""
Full-test mode handlers.
Timed mode   — no per-task feedback, score + grade at the end.
Practice mode — brief feedback after each task, grade at the end.
"""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import complete_test_session, create_test_session, get_test_detail, upsert_user
from generator import evaluate_all_answers, generate_task
from keyboards import (
    kb_test_answer_sent,
    kb_test_detail_back,
    kb_test_next,
    kb_test_results,
    kb_test_start,
)
from states import VPRStates
from vpr_data import VPR_STRUCTURE, calculate_grade, get_task_type, grade_emoji

router = Router()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Show test overview
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "mode:test")
async def show_test_info(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    if not grade:
        await call.answer("Сначала выбери класс.", show_alert=True)
        return

    vpr = VPR_STRUCTURE[grade]
    await state.set_state(VPRStates.test_info)
    await call.message.edit_text(
        vpr["test_overview"],
        reply_markup=kb_test_start(),
    )
    await call.answer()


# ---------------------------------------------------------------------------
# Start test
# ---------------------------------------------------------------------------

async def _start_test(call: CallbackQuery, state: FSMContext, mode: str) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    if not grade:
        await call.answer("Сначала выбери класс.", show_alert=True)
        return

    vpr = VPR_STRUCTURE[grade]
    await upsert_user(call.from_user.id, call.from_user.username, call.from_user.first_name)
    session_id = await create_test_session(call.from_user.id, grade, mode)

    await state.set_state(VPRStates.test_in_progress)
    await state.update_data(
        test_mode=mode,
        test_session_id=session_id,
        test_grade=grade,
        test_current_idx=0,                 # 0-based index of current task
        test_answers=[],                     # accumulated answers
        test_start_time=datetime.now().isoformat(),
    )

    mode_label = "⏱ на время" if mode == "timed" else "🧘 без таймера"
    await call.message.edit_text(
        f"🚀 <b>Контрольная началась!</b> ({mode_label})\n\n"
        f"Всего заданий: <b>{vpr['tasks_count']}</b>\n"
        f"{'⚠️ Помни о времени: ' + str(vpr['time_minutes']) + ' минут!' if mode == 'timed' else ''}\n\n"
        "⏳ Загружаю первое задание…"
    )
    await call.answer()

    await _send_next_task(call.message, state)


@router.callback_query(F.data == "test:timed")
async def start_timed(call: CallbackQuery, state: FSMContext) -> None:
    await _start_test(call, state, "timed")


@router.callback_query(F.data == "test:practice")
async def start_practice(call: CallbackQuery, state: FSMContext) -> None:
    await _start_test(call, state, "practice")


# ---------------------------------------------------------------------------
# Send next task
# ---------------------------------------------------------------------------

async def _send_next_task(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data["test_grade"]
    idx = data["test_current_idx"]
    vpr = VPR_STRUCTURE[grade]
    task_types = vpr["task_types"]

    if idx >= len(task_types):
        # Should not happen — handled by finish flow
        return

    task_type = task_types[idx]
    task_num = task_type["num"]
    total = vpr["tasks_count"]

    try:
        task = await generate_task(
            grade=grade,
            task_num=task_num,
            topic=task_type["topic"],
            hint=task_type["hint"],
        )
    except Exception as e:
        logger.error("generate_task in test failed: %s", e)
        await message.edit_text(
            "😕 Не удалось сгенерировать задание. Пропускаю.",
        )
        # Record as skipped
        answers = data["test_answers"]
        answers.append({
            "task_num": task_num,
            "task_topic": task_type["topic"],
            "task_text": "(ошибка генерации)",
            "correct_answer": "",
            "user_answer": "(пропущено)",
            "max_points": task_type["max_points"],
        })
        await state.update_data(test_answers=answers, test_current_idx=idx + 1)
        await _advance_or_finish(message, state)
        return

    # Store current task info in state
    await state.update_data(
        test_current_task={
            "task_num": task_num,
            "task_topic": task_type["topic"],
            "task_text": task["task_text"],
            "correct_answer": task["correct_answer"],
            "max_points": task_type["max_points"],
        }
    )

    progress = f"Задание {idx + 1} из {total}"
    mode = data.get("test_mode", "practice")

    # Time hint for timed mode
    if mode == "timed":
        start_dt = datetime.fromisoformat(data["test_start_time"])
        elapsed = int((datetime.now() - start_dt).total_seconds())
        time_limit = vpr["time_minutes"] * 60
        remaining = max(0, time_limit - elapsed)
        mins, secs = divmod(remaining, 60)
        time_info = f"⏱ Осталось: <b>{mins}:{secs:02d}</b>\n"
    else:
        time_info = ""

    text = (
        f"📝 <b>{progress}</b>\n"
        f"{time_info}"
        f"{'─' * 30}\n\n"
        f"<b>№{task_num}. {task_type['topic']}</b>\n\n"
        f"{task['task_text']}\n\n"
        f"{'─' * 30}\n"
        f"✏️ <i>Напиши ответ в чат</i>"
    )
    await message.edit_text(text)


# ---------------------------------------------------------------------------
# Receive answer during test
# ---------------------------------------------------------------------------

@router.message(VPRStates.test_in_progress)
async def receive_test_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    current_task = data.get("test_current_task")
    if not current_task:
        await message.answer("⚠️ Произошла ошибка. Попробуй начать контрольную заново.")
        return

    user_answer = message.text.strip()
    answers = data.get("test_answers", [])

    # Append answer (evaluation happens later or now depending on mode)
    entry = {**current_task, "user_answer": user_answer}
    answers.append(entry)

    idx = data["test_current_idx"]
    vpr = VPR_STRUCTURE[data["test_grade"]]
    total = vpr["tasks_count"]
    mode = data.get("test_mode", "practice")

    await state.update_data(test_answers=answers, test_current_idx=idx + 1)

    if mode == "practice":
        # Evaluate immediately and show brief feedback
        from generator import evaluate_answer
        try:
            result = await evaluate_answer(
                current_task["task_text"],
                current_task["correct_answer"],
                user_answer,
                current_task["max_points"],
            )
        except Exception:
            result = {
                "points": 0, "is_correct": False,
                "verdict": "⚠️ Ошибка проверки",
                "explanation": f"Правильный ответ: {current_task['correct_answer']}",
            }

        # Update the stored entry with points
        answers[-1].update(result)
        await state.update_data(test_answers=answers)

        pts = result["points"]
        max_pts = current_task["max_points"]
        filled = "🟩" * pts + "⬜" * (max_pts - pts)

        feedback = (
            f"{result['verdict']}\n"
            f"{filled} <b>{pts}/{max_pts}</b>\n\n"
            f"{result['explanation']}"
        )
        await message.answer(
            feedback,
            reply_markup=kb_test_answer_sent(idx + 1, total, mode),
        )
    else:
        # Timed: no feedback, just move forward
        await message.answer(
            f"✅ Ответ принят.\n\n"
            f"Выполнено: <b>{idx + 1}/{total}</b>",
            reply_markup=kb_test_next(idx + 1, total),
        )


# ---------------------------------------------------------------------------
# Next task (callback)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "test:next", VPRStates.test_in_progress)
async def test_next(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await call.message.edit_text("⏳ Загружаю следующее задание…")
    await _send_next_task(call.message, state)


# ---------------------------------------------------------------------------
# Finish test
# ---------------------------------------------------------------------------

async def _advance_or_finish(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    idx = data["test_current_idx"]
    vpr = VPR_STRUCTURE[data["test_grade"]]
    if idx < vpr["tasks_count"]:
        await _send_next_task(message, state)
    else:
        await _finish_test(message, state)


@router.callback_query(F.data == "test:finish")
async def test_finish_callback(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await call.message.edit_text("⏳ <b>Подсчитываю результаты…</b>")
    await _finish_test(call.message, state)


async def _finish_test(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data["test_grade"]
    mode = data.get("test_mode", "practice")
    session_id = data["test_session_id"]
    answers = data.get("test_answers", [])
    vpr = VPR_STRUCTURE[grade]

    start_dt = datetime.fromisoformat(data["test_start_time"])
    elapsed_sec = int((datetime.now() - start_dt).total_seconds())
    elapsed_str = f"{elapsed_sec // 60}:{elapsed_sec % 60:02d}"

    # For timed mode, evaluate all answers now (batch)
    if mode == "timed":
        try:
            answers = await evaluate_all_answers(answers)
        except Exception as e:
            logger.error("batch evaluation failed: %s", e)

    total_score = sum(a.get("points", 0) for a in answers)
    max_score = vpr["max_score"]
    mark = calculate_grade(grade, total_score)
    emoji = grade_emoji(mark)

    # Save to DB
    try:
        await complete_test_session(session_id, total_score, max_score, mark, answers)
    except Exception as e:
        logger.warning("complete_test_session failed: %s", e)

    await state.set_state(VPRStates.viewing_test_results)

    # Build results message
    pct = round(total_score / max_score * 100) if max_score else 0
    bar_len = 10
    filled = round(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    time_warning = ""
    if mode == "timed" and elapsed_sec > vpr["time_minutes"] * 60:
        over = elapsed_sec - vpr["time_minutes"] * 60
        time_warning = f"\n⚠️ <i>Превышено время на {over // 60}:{over % 60:02d}</i>"

    result_text = (
        f"{emoji} <b>Контрольная завершена!</b>\n\n"
        f"Класс: <b>{vpr['grade_name']}</b>\n"
        f"Режим: {'⏱ На время' if mode == 'timed' else '🧘 Тренировка'}\n"
        f"Время: {elapsed_str}{time_warning}\n\n"
        f"{'─' * 30}\n"
        f"Баллы: <b>{total_score}</b> из <b>{max_score}</b>\n"
        f"[{bar}] {pct}%\n\n"
        f"🏆 <b>Оценка: {mark}</b>\n\n"
    )

    # Grading context
    for m, mn, mx in vpr["grading"]:
        marker = "←" if m == mark else "  "
        result_text += f"{grade_emoji(m)} «{m}»: {mn}–{mx} баллов {marker}\n"

    await message.edit_text(
        result_text,
        reply_markup=kb_test_results(session_id),
    )


# ---------------------------------------------------------------------------
# Detailed breakdown
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("testdetail:"))
async def show_test_detail(call: CallbackQuery, state: FSMContext) -> None:
    session_id = int(call.data.split(":")[1])
    await call.answer()

    try:
        session = await get_test_detail(session_id)
    except Exception as e:
        logger.error("get_test_detail failed: %s", e)
        await call.message.edit_text("😕 Не удалось загрузить детали.", reply_markup=kb_test_detail_back())
        return

    if not session:
        await call.message.edit_text("😕 Сессия не найдена.", reply_markup=kb_test_detail_back())
        return

    tasks = session.get("tasks", [])
    vpr = VPR_STRUCTURE[session["grade"]]

    lines = [
        f"📋 <b>Подробный разбор — {vpr['grade_name']}</b>\n",
        f"Итого: {session['total_score']}/{session['max_score']} баллов · Оценка «{session['grade_mark']}»\n",
        "─" * 30,
    ]

    for t in tasks:
        task_num = t.get("task_num", "?")
        topic = t.get("task_topic", "")
        pts = t.get("points", 0)
        max_pts = t.get("max_points", 2)
        user_ans = t.get("user_answer", "—")
        correct_ans = t.get("correct_answer", "—")
        is_correct = t.get("is_correct", False)

        icon = "✅" if is_correct else ("⚠️" if pts > 0 else "❌")
        lines.append(
            f"\n{icon} <b>№{task_num}</b> <i>{topic}</i>\n"
            f"   Ответ: <code>{user_ans}</code> | Верно: <code>{correct_ans}</code>\n"
            f"   Баллы: {pts}/{max_pts}"
        )

    detail_text = "\n".join(lines)

    # Split if too long
    if len(detail_text) <= 4096:
        await call.message.edit_text(detail_text, reply_markup=kb_test_detail_back())
    else:
        chunks = [detail_text[i:i + 4000] for i in range(0, len(detail_text), 4000)]
        await call.message.edit_text(chunks[0])
        for chunk in chunks[1:-1]:
            await call.message.answer(chunk)
        await call.message.answer(chunks[-1], reply_markup=kb_test_detail_back())
