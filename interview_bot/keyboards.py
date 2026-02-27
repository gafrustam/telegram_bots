from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

PROG_LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java",
    "C++", "C#", "Go", "Kotlin", "Swift", "PHP",
]

LEVELS = {
    "intern": "👶 Стажёр",
    "junior": "🌱 Джун",
    "middle": "⚡ Мидл",
    "senior": "🔥 Синьор",
}

BOT_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

LEVEL_LABELS = {k: v.split(" ", 1)[1] for k, v in LEVELS.items()}  # без эмодзи


def prog_language_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for lang in PROG_LANGUAGES:
        b.button(text=lang, callback_data=f"setup_lang:{lang}")
    b.adjust(3)
    return b.as_markup()


def level_keyboard(prefix: str = "setup_level") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in LEVELS.items():
        b.button(text=label, callback_data=f"{prefix}:{key}")
    b.adjust(2)
    return b.as_markup()


def problem_keyboard(hints_revealed: int) -> InlineKeyboardMarkup:
    """Кнопки под задачей (пока не отправлено решение)."""
    b = InlineKeyboardBuilder()
    if hints_revealed == 0:
        b.button(text="💡 Подсказка 1", callback_data="hint:1")
    elif hints_revealed == 1:
        b.button(text="💡 Подсказка 2", callback_data="hint:2")
    elif hints_revealed == 2:
        b.button(text="💡 Подсказка 3", callback_data="hint:3")
    elif hints_revealed >= 3:
        b.button(text="📖 Решение словами", callback_data="hint:verbal")
    b.button(text="🏳️ Сдаться", callback_data="surrender")
    b.adjust(2)
    return b.as_markup()


def wrong_answer_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🧪 Посмотреть тест", callback_data="show_test")
    b.button(text="🏳️ Сдаться", callback_data="surrender")
    b.adjust(2)
    return b.as_markup()


def after_test_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Показать решение", callback_data="show_solution")
    b.button(text="🔄 Попробовать снова", callback_data="retry")
    b.adjust(2)
    return b.as_markup()


def next_problem_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➡️ Следующая задача", callback_data="next_problem")
    b.adjust(1)
    return b.as_markup()


def settings_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💻 Язык программирования", callback_data="settings:prog_lang")
    b.button(text="📊 Уровень сложности",     callback_data="settings:level")
    b.button(text="⏰ Время уведомлений",     callback_data="settings:time")
    b.button(text="🌍 Язык бота",            callback_data="settings:bot_lang")
    b.button(text="📈 Моя статистика",       callback_data="settings:stats")
    b.adjust(1)
    return b.as_markup()


def settings_lang_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for lang in PROG_LANGUAGES:
        b.button(text=lang, callback_data=f"set_prog_lang:{lang}")
    b.button(text="« Назад", callback_data="settings:back")
    b.adjust(3)
    return b.as_markup()


def settings_bot_lang_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in BOT_LANGUAGES.items():
        b.button(text=label, callback_data=f"set_bot_lang:{key}")
    b.button(text="« Назад", callback_data="settings:back")
    b.adjust(2)
    return b.as_markup()


def settings_level_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in LEVELS.items():
        b.button(text=label, callback_data=f"set_level:{key}")
    b.button(text="« Назад", callback_data="settings:back")
    b.adjust(2)
    return b.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data="settings:back")
    b.adjust(1)
    return b.as_markup()
