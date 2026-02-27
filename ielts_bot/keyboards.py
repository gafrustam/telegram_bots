import os

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from states import TopicAction, ResultAction, InterruptAction

PART1_BTN  = "🗣 Part 1 — Interview"
PART2_BTN  = "🎙 Part 2 — Long Turn"
PART3_BTN  = "💬 Part 3 — Discussion"
STATS_BTN  = "📊 Моя статистика"
ADMIN_BTN  = "🔧 Админ-панель"
WEBAPP_BTN = "🌐 Web App"

_WEBAPP_URL = os.getenv("WEBAPP_URL", "https://gafrustam.ru/ielts/")


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    # TEXT INTERFACE DISABLED — only Web App button shown.
    # To restore full keyboard, uncomment the rows below.
    keyboard = [
        # [KeyboardButton(text=PART1_BTN)],   # RESTORE: Part 1
        # [KeyboardButton(text=PART2_BTN)],   # RESTORE: Part 2
        # [KeyboardButton(text=PART3_BTN)],   # RESTORE: Part 3
        # [KeyboardButton(text=STATS_BTN)],   # RESTORE: Stats
        [KeyboardButton(text=WEBAPP_BTN, web_app=WebAppInfo(url=_WEBAPP_URL))],
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
        [InlineKeyboardButton(
            text="✏️ Своя тема",
            callback_data=TopicAction(action="custom").pack(),
        )],
    ])


def results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔁 Пройти заново",
            callback_data=ResultAction(action="retry").pack(),
        )],
        [InlineKeyboardButton(
            text="📋 В меню",
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


