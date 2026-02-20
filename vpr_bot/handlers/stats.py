"""
Statistics handlers.
"""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database import get_task_stats, get_test_history
from keyboards import kb_stats_back, kb_stats_main
from states import VPRStates
from vpr_data import VPR_STRUCTURE, grade_emoji

router = Router()
logger = logging.getLogger(__name__)


def _pct_bar(correct: int, total: int, width: int = 10) -> str:
    if total == 0:
        return "░" * width + " нет данных"
    pct = correct / total
    filled = round(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {round(pct * 100)}%"


# ---------------------------------------------------------------------------
# Stats for a specific grade
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("stats:grade:"))
async def stats_by_grade(call: CallbackQuery, state: FSMContext) -> None:
    grade = int(call.data.split(":")[-1])
    vpr = VPR_STRUCTURE[grade]
    await call.answer()

    try:
        rows = await get_task_stats(call.from_user.id, grade)
    except Exception as e:
        logger.error("get_task_stats failed: %s", e)
        await call.message.edit_text("😕 Не удалось загрузить статистику.", reply_markup=kb_stats_back())
        return

    if not rows:
        await call.message.edit_text(
            f"📊 <b>Статистика — {vpr['grade_name']}</b>\n\n"
            "Ты ещё не решал задания этого класса.\n"
            "Перейди в «Тренировать задание», чтобы начать!",
            reply_markup=kb_stats_back(),
        )
        return

    # Build per-task map
    stats_map = {r["task_num"]: r for r in rows}

    total_attempts = sum(r["total"] for r in rows)
    total_correct = sum(r["correct"] for r in rows)
    total_pts = sum(r["pts_earned"] for r in rows)
    total_pts_max = sum(r["pts_max"] for r in rows)

    lines = [
        f"📊 <b>Статистика — {vpr['grade_name']}</b>\n",
        f"Всего попыток: <b>{total_attempts}</b> · "
        f"Верных: <b>{total_correct}</b> ({round(total_correct / total_attempts * 100) if total_attempts else 0}%)\n",
        "─" * 30,
    ]

    for t in vpr["task_types"]:
        n = t["num"]
        s = stats_map.get(n)
        if s:
            bar = _pct_bar(s["correct"], s["total"])
            pts_info = f"{s['pts_earned']}/{s['pts_max']} балл."
            lines.append(
                f"\n<b>№{n}</b> {t['topic']}\n"
                f"   {bar}  ({s['correct']}/{s['total']})  {pts_info}"
            )
        else:
            lines.append(
                f"\n<b>№{n}</b> {t['topic']}\n"
                f"   [{'░' * 10}] не тренировалось"
            )

    text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4050] + "\n\n<i>…</i>"

    await call.message.edit_text(text, reply_markup=kb_stats_back())


# ---------------------------------------------------------------------------
# Stats per grade (from mode menu)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "mode:stats_grade")
async def stats_grade_from_mode(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    if not grade:
        await call.answer("Сначала выбери класс.", show_alert=True)
        return
    # Reuse the grade stats handler
    call.data = f"stats:grade:{grade}"
    await stats_by_grade(call, state)


# ---------------------------------------------------------------------------
# Test history
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "stats:history")
async def stats_history(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    try:
        history = await get_test_history(call.from_user.id, limit=20)
    except Exception as e:
        logger.error("get_test_history failed: %s", e)
        await call.message.edit_text("😕 Не удалось загрузить историю.", reply_markup=kb_stats_back())
        return

    if not history:
        await call.message.edit_text(
            "📜 <b>История контрольных</b>\n\n"
            "Ты ещё не проходил ни одной контрольной.\n"
            "Перейди в «Пройти контрольную», чтобы начать!",
            reply_markup=kb_stats_back(),
        )
        return

    lines = ["📜 <b>История контрольных</b>\n", "─" * 30]

    for h in history:
        grade = h["grade"]
        vpr = VPR_STRUCTURE.get(grade, {})
        grade_name = vpr.get("grade_name", f"{grade} кл.")
        mark = h["grade_mark"]
        emoji_m = grade_emoji(mark) if mark else "❓"
        score = h["total_score"]
        max_s = h["max_score"]
        mode_label = "⏱" if h["mode"] == "timed" else "🧘"

        # Parse date
        try:
            dt = datetime.fromisoformat(h["completed_at"])
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            date_str = h.get("completed_at", "—")

        lines.append(
            f"\n{emoji_m} <b>«{mark}»</b>  {grade_name}  {mode_label}\n"
            f"   {date_str}  ·  {score}/{max_s} баллов"
        )

    text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4050] + "\n\n<i>… (показаны последние 20)</i>"

    await call.message.edit_text(text, reply_markup=kb_stats_back())
