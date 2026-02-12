from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from states import TopicAction, ResultAction, AdminAction

PART1_BTN = "Part 1 — Interview"
PART2_BTN = "Part 2 — Long Turn"
PART3_BTN = "Part 3 — Discussion"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PART1_BTN)],
            [KeyboardButton(text=PART2_BTN)],
            [KeyboardButton(text=PART3_BTN)],
        ],
        resize_keyboard=True,
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Начать",
            callback_data=TopicAction(action="accept").pack(),
        )],
        [InlineKeyboardButton(
            text="Другая тема",
            callback_data=TopicAction(action="another").pack(),
        )],
    ])


def results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Пройти заново",
            callback_data=ResultAction(action="retry").pack(),
        )],
        [InlineKeyboardButton(
            text="Главное меню",
            callback_data=ResultAction(action="menu").pack(),
        )],
    ])


def admin_nav_keyboard(current: str) -> InlineKeyboardMarkup:
    pages = [
        ("📊 Обзор", "overview"),
        ("📅 По дням", "daily"),
        ("👥 Топ", "top_users"),
        ("📋 Разделы", "parts"),
    ]
    row = [
        InlineKeyboardButton(
            text=label,
            callback_data=AdminAction(page=page).pack(),
        )
        for label, page in pages
        if page != current
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row])
