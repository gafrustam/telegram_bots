from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from states import TopicAction, ResultAction, AdminAction, InterruptAction

PART1_BTN = "🗣 Part 1 — Interview"
PART2_BTN = "🎙 Part 2 — Long Turn"
PART3_BTN = "💬 Part 3 — Discussion"
STATS_BTN = "📊 Моя статистика"
ADMIN_BTN = "🔧 Админ-панель"


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=PART1_BTN)],
        [KeyboardButton(text=PART2_BTN)],
        [KeyboardButton(text=PART3_BTN)],
        [KeyboardButton(text=STATS_BTN)],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_BTN)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Начать",
            callback_data=TopicAction(action="accept").pack(),
        )],
        [InlineKeyboardButton(
            text="🔄 Другая тема",
            callback_data=TopicAction(action="another").pack(),
        )],
    ])


def results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔁 Пройти заново",
            callback_data=ResultAction(action="retry").pack(),
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data=ResultAction(action="menu").pack(),
        )],
    ])


PART_SHORT = {1: "Part 1", 2: "Part 2", 3: "Part 3"}


def interrupt_keyboard(new_part: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Продолжить",
            callback_data=InterruptAction(action="continue", new_part=new_part).pack(),
        )],
        [InlineKeyboardButton(
            text=f"🔄 Перейти к {PART_SHORT.get(new_part, 'Part')}",
            callback_data=InterruptAction(action="new", new_part=new_part).pack(),
        )],
    ])


def admin_nav_keyboard(current: str) -> InlineKeyboardMarkup:
    pages = [
        ("📊 Обзор", "overview"),
        ("📈 Рост", "growth"),
        ("🎯 Баллы", "scores"),
        ("👥 Юзеры", "users"),
        ("⏱ Нагрузка", "usage"),
        ("⚡ Выбросы", "outliers"),
    ]
    buttons = [
        InlineKeyboardButton(
            text=label,
            callback_data=AdminAction(page=page).pack(),
        )
        for label, page in pages
        if page != current
    ]
    row1 = buttons[:3]
    row2 = buttons[3:]
    rows = [row1]
    if row2:
        rows.append(row2)
    return InlineKeyboardMarkup(inline_keyboard=rows)
