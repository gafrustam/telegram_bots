"""
Common handlers: /start, navigation callbacks (nav:*).
"""

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import upsert_user
from keyboards import kb_grades, kb_mode, kb_stats_main, kb_task_types
from states import VPRStates
from vpr_data import VPR_STRUCTURE

router = Router()
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 <b>Привет! Я — тренажёр для подготовки к ВПР по математике.</b>\n\n"
    "С моей помощью ты можешь:\n"
    "🎯 Отрабатывать конкретные типы заданий\n"
    "📝 Проходить полную контрольную с оценкой\n"
    "📊 Отслеживать свой прогресс\n\n"
    "Выбери свой класс 👇"
)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    await state.clear()
    await state.set_state(VPRStates.choosing_grade)
    await message.answer(WELCOME_TEXT, reply_markup=kb_grades())


# ---------------------------------------------------------------------------
# Navigation callbacks
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "nav:grades")
async def nav_grades(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(VPRStates.choosing_grade)
    await call.message.edit_text(WELCOME_TEXT, reply_markup=kb_grades())
    await call.answer()


@router.callback_query(F.data.startswith("grade:"))
async def select_grade(call: CallbackQuery, state: FSMContext) -> None:
    grade = int(call.data.split(":")[1])
    data = VPR_STRUCTURE[grade]
    await state.update_data(grade=grade)
    await state.set_state(VPRStates.choosing_mode)
    text = (
        f"📚 <b>{data['grade_name']}</b>\n\n"
        f"Контрольная: {data['tasks_count']} заданий · {data['time_minutes']} минут · "
        f"макс. {data['max_score']} баллов\n\n"
        "Что будем делать?"
    )
    await call.message.edit_text(text, reply_markup=kb_mode(grade))
    await call.answer()


@router.callback_query(F.data == "nav:mode")
async def nav_mode(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    if not grade:
        await nav_grades(call, state)
        return
    vpr = VPR_STRUCTURE[grade]
    await state.set_state(VPRStates.choosing_mode)
    text = (
        f"📚 <b>{vpr['grade_name']}</b>\n\n"
        f"Контрольная: {vpr['tasks_count']} заданий · {vpr['time_minutes']} минут · "
        f"макс. {vpr['max_score']} баллов\n\n"
        "Что будем делать?"
    )
    await call.message.edit_text(text, reply_markup=kb_mode(grade))
    await call.answer()


@router.callback_query(F.data == "nav:task_types")
async def nav_task_types(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    if not grade:
        await nav_grades(call, state)
        return
    vpr = VPR_STRUCTURE[grade]
    await state.set_state(VPRStates.choosing_task_type)
    text = (
        f"🎯 <b>Тренировка — {vpr['grade_name']}</b>\n\n"
        "Выбери тип задания для отработки:"
    )
    await call.message.edit_text(text, reply_markup=kb_task_types(grade))
    await call.answer()


@router.callback_query(F.data == "mode:train")
async def mode_train(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    if not grade:
        await nav_grades(call, state)
        return
    vpr = VPR_STRUCTURE[grade]
    await state.set_state(VPRStates.choosing_task_type)
    text = (
        f"🎯 <b>Тренировка — {vpr['grade_name']}</b>\n\n"
        "Выбери тип задания для отработки:"
    )
    await call.message.edit_text(text, reply_markup=kb_task_types(grade))
    await call.answer()


@router.callback_query(F.data == "nav:stats")
async def nav_stats(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(VPRStates.viewing_stats)
    await call.message.edit_text(
        "📊 <b>Статистика</b>\n\nВыбери, что хочешь посмотреть:",
        reply_markup=kb_stats_main(),
    )
    await call.answer()
