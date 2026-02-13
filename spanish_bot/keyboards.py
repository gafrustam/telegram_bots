from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from states import TopicAction, ResultAction

# Reply keyboard button labels
NEW_DIALOG_BTN = "\U0001f5e3 Nuevo dialogo"
LEVEL_UP_BTN = "\U0001f4c8 Subir dificultad"
LEVEL_DOWN_BTN = "\U0001f4c9 Bajar dificultad"
END_BTN = "\u26d4 Terminar"


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
                text="Empezar",
                callback_data=TopicAction(action="start").pack(),
            ),
            InlineKeyboardButton(
                text="Otro tema",
                callback_data=TopicAction(action="another").pack(),
            ),
        ],
    ])


def results_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Nuevo dialogo",
                callback_data=ResultAction(action="new").pack(),
            ),
            InlineKeyboardButton(
                text="Menu",
                callback_data=ResultAction(action="menu").pack(),
            ),
        ],
    ])
