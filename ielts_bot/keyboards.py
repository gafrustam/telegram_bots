import os

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from states import TopicAction, ResultAction, InterruptAction, QuestionAction, NextPartAction

PART1_BTN  = "🗣 Part 1 — Interview"
PART2_BTN  = "🎙 Part 2 — Long Turn"
PART3_BTN  = "💬 Part 3 — Discussion"
ADMIN_BTN  = "🔧 Админ-панель"
WEBAPP_BTN = "🌐 Запустить приложение"
START_BTN  = "🚀 Начать тест"

_WEBAPP_URL = os.getenv("WEBAPP_URL", "https://gafrustam.ru/ielts/")


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=START_BTN)],
        [KeyboardButton(text=WEBAPP_BTN, web_app=WebAppInfo(url=_WEBAPP_URL))],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_BTN)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Начать",
            callback_data=TopicAction(action="accept").pack(),
        )],
    ])


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
            text="🔁 Пройти весь тест заново",
            callback_data=ResultAction(action="retry").pack(),
        )],
        [InlineKeyboardButton(
            text="📋 В меню",
            callback_data=ResultAction(action="menu").pack(),
        )],
    ])


def next_part_keyboard(next_part: int) -> InlineKeyboardMarkup:
    part_names = {2: "Part 2 — Long Turn 🎙", 3: "Part 3 — Discussion 💬"}
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"➡️ Перейти к {part_names.get(next_part, f'Part {next_part}')}",
            callback_data=NextPartAction(next_part=next_part).pack(),
        )],
    ])


def question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Прослушать ещё раз",
            callback_data=QuestionAction(action="replay").pack(),
        )],
    ])


PART_SHORT = {1: "Part 1", 2: "Part 2", 3: "Part 3"}


def interrupt_keyboard(new_part: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Продолжить",
            callback_data=InterruptAction(action="continue", new_part=new_part).pack(),
        )],
        [InlineKeyboardButton(
            text="🔄 Начать заново",
            callback_data=InterruptAction(action="new", new_part=new_part).pack(),
        )],
    ])


