from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from states import TopicAction, ResultAction, InterruptAction, QuestionAction

# ── Main menu buttons ────────────────────────────────────
LISTENING_BTN = "🎧 Listening"
READING_BTN   = "📖 Reading"
WRITING_BTN   = "✍️ Writing"
SPEAKING_BTN  = "🗣 Speaking"
STATS_BTN     = "📊 Моя статистика"
ADMIN_BTN     = "🔧 Админ-панель"

# ── Speaking sub-menu buttons ────────────────────────────
PART1_BTN = "🗣 Part 1 — Interview"
PART2_BTN = "🎙 Part 2 — Long Turn"
PART3_BTN = "💬 Part 3 — Discussion"
MENU_BTN  = "⬅️ Главное меню"


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=LISTENING_BTN)],
        [KeyboardButton(text=READING_BTN)],
        [KeyboardButton(text=WRITING_BTN)],
        [KeyboardButton(text=SPEAKING_BTN)],
        [KeyboardButton(text=STATS_BTN)],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_BTN)])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def speaking_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PART1_BTN)],
            [KeyboardButton(text=PART2_BTN)],
            [KeyboardButton(text=PART3_BTN)],
            [KeyboardButton(text=MENU_BTN)],
        ],
        resize_keyboard=True,
    )


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="▶️ Начать",
            callback_data=TopicAction(action="accept").pack(),
        ),
    ]])


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


def question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔄 Прослушать ещё раз",
            callback_data=QuestionAction(action="replay").pack(),
        ),
    ]])


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
