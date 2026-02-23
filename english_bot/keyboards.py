from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from states import TopicAction, ResultAction

# Reply keyboard button labels
NEW_DIALOG_BTN = "\U0001f5e3 New dialogue"
LEVEL_UP_BTN = "\U0001f4c8 Level up"
LEVEL_DOWN_BTN = "\U0001f4c9 Level down"
END_BTN = "\u26d4 End"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=NEW_DIALOG_BTN)],
            [KeyboardButton(text=LEVEL_UP_BTN), KeyboardButton(text=LEVEL_DOWN_BTN)],
        ],
        resize_keyboard=True,
    )


def conversation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=END_BTN)]],
        resize_keyboard=True,
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Start",
                callback_data=TopicAction(action="start").pack(),
            ),
            InlineKeyboardButton(
                text="Another topic",
                callback_data=TopicAction(action="another").pack(),
            ),
        ],
    ])


def results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="New dialogue",
                callback_data=ResultAction(action="new").pack(),
            ),
            InlineKeyboardButton(
                text="Menu",
                callback_data=ResultAction(action="menu").pack(),
            ),
        ],
    ])
