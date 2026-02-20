"""
Inline keyboard factories for VPR Bot.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from vpr_data import SUPPORTED_GRADES, VPR_STRUCTURE


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def kb_grades() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for grade in SUPPORTED_GRADES:
        builder.button(
            text=f"📚 {grade} класс",
            callback_data=f"grade:{grade}",
        )
    builder.button(text="📊 Моя статистика", callback_data="nav:stats")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------

def kb_mode(grade: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Тренировать задание", callback_data="mode:train")
    builder.button(text="📝 Пройти контрольную", callback_data="mode:test")
    builder.button(text="📊 Статистика по классу", callback_data="mode:stats_grade")
    builder.button(text="◀️ Назад", callback_data="nav:grades")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Task-type selection
# ---------------------------------------------------------------------------

def kb_task_types(grade: int) -> InlineKeyboardMarkup:
    data = VPR_STRUCTURE[grade]
    builder = InlineKeyboardBuilder()
    for t in data["task_types"]:
        builder.button(
            text=f"№{t['num']} — {t['topic']}",
            callback_data=f"task:{t['num']}",
        )
    builder.button(text="◀️ Назад", callback_data="nav:mode")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Task training — after evaluation
# ---------------------------------------------------------------------------

def kb_task_result(task_num: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💡 Получить теорию", callback_data=f"theory:{task_num}")
    builder.button(text="🔄 Ещё задание", callback_data=f"task:{task_num}")
    builder.button(text="📋 Другой тип", callback_data="nav:task_types")
    builder.button(text="🏠 В меню", callback_data="nav:mode")
    builder.adjust(2, 2)
    return builder.as_markup()


def kb_after_theory(task_num: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Ещё такое задание", callback_data=f"task:{task_num}")
    builder.button(text="📋 Другой тип", callback_data="nav:task_types")
    builder.button(text="🏠 В меню", callback_data="nav:mode")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Test mode
# ---------------------------------------------------------------------------

def kb_test_start() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏱ Начать на время", callback_data="test:timed")
    builder.button(text="🧘 Тренироваться без таймера", callback_data="test:practice")
    builder.button(text="◀️ Назад", callback_data="nav:mode")
    builder.adjust(1)
    return builder.as_markup()


def kb_test_answer_sent(current: int, total: int, mode: str) -> InlineKeyboardMarkup:
    """Shown after user sends answer in practice mode (with immediate feedback)."""
    builder = InlineKeyboardBuilder()
    if current < total:
        builder.button(
            text=f"➡️ Следующее задание ({current + 1}/{total})",
            callback_data="test:next",
        )
    else:
        builder.button(text="📊 Посмотреть результаты", callback_data="test:finish")
    return builder.as_markup()


def kb_test_next(current: int, total: int) -> InlineKeyboardMarkup:
    """Shown after user sends answer in timed mode (no feedback)."""
    builder = InlineKeyboardBuilder()
    if current < total:
        builder.button(
            text=f"➡️ Задание {current + 1}/{total}",
            callback_data="test:next",
        )
    else:
        builder.button(text="✅ Завершить и увидеть оценку", callback_data="test:finish")
    return builder.as_markup()


def kb_test_results(session_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Подробный разбор", callback_data=f"testdetail:{session_id}")
    builder.button(text="🔄 Пройти ещё раз", callback_data="mode:test")
    builder.button(text="🏠 В меню", callback_data="nav:mode")
    builder.adjust(1)
    return builder.as_markup()


def kb_test_detail_back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В меню", callback_data="nav:mode")
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def kb_stats_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for grade in SUPPORTED_GRADES:
        builder.button(text=f"📚 {grade} класс", callback_data=f"stats:grade:{grade}")
    builder.button(text="📜 История контрольных", callback_data="stats:history")
    builder.button(text="🏠 В меню", callback_data="nav:grades")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def kb_stats_back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ К статистике", callback_data="nav:stats")
    builder.button(text="🏠 В меню", callback_data="nav:grades")
    builder.adjust(2)
    return builder.as_markup()
