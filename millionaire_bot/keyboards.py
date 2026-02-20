"""All InlineKeyboard builders for the Millionaire bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ── Callback data constants ───────────────────────────────────────────────────
NOOP = "noop"
START_GAME = "start_game"
NEXT_Q = "next_q"
QUIT_GAME = "quit_game"
PLAY_AGAIN = "play_again"
SHOW_LADDER = "show_ladder"
LIFELINE_FIFTY = "ll_fifty"
LIFELINE_PHONE = "ll_phone"
LIFELINE_AUDIENCE = "ll_audience"


def _ans(letter: str) -> str:
    return f"ans_{letter}"


def _confirm(letter: str) -> str:
    return f"confirm_{letter}"


CANCEL_CONFIRM = "cancel_confirm"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def _noop(text: str) -> InlineKeyboardButton:
    return _btn(text, NOOP)


# ── Welcome screen ────────────────────────────────────────────────────────────
def welcome_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_btn("🎮  Начать игру", START_GAME))
    b.row(_btn("📊  Таблица призов", SHOW_LADDER))
    return b.as_markup()


# ── Question screen ───────────────────────────────────────────────────────────
def question_keyboard(
    options: dict[str, str],
    lifelines: dict[str, bool],
    removed: list[str],
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    # Answer buttons — 2 × 2 grid
    for letter in ("A", "B", "C", "D"):
        if letter in removed:
            b.button(text="—", callback_data=NOOP)
        else:
            text = f"{letter})  {options[letter]}"
            b.button(text=text, callback_data=_ans(letter))
    b.adjust(2)

    # Lifeline row
    def ll_btn(key: str, active_text: str, used_text: str, cb: str) -> InlineKeyboardButton:
        if lifelines.get(key):
            return _btn(active_text, cb)
        return _noop(used_text)

    b.row(
        ll_btn("fifty",    "🔢 50/50",         "✗ 50/50",         LIFELINE_FIFTY),
        ll_btn("phone",    "📞 Звонок другу",   "✗ Звонок",        LIFELINE_PHONE),
        ll_btn("audience", "👥 Помощь зала",    "✗ Помощь зала",   LIFELINE_AUDIENCE),
    )

    # Bottom row
    b.row(
        _btn("📊 Лесенка призов", SHOW_LADDER),
        _btn("🚶 Забрать деньги", QUIT_GAME),
    )

    return b.as_markup()


# ── Confirmation screen ───────────────────────────────────────────────────────
def confirm_keyboard(letter: str, option_text: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_btn(f"✅  Да! {letter}) {option_text} — финальный ответ", _confirm(letter)))
    b.row(_btn("↩️  Изменить ответ", CANCEL_CONFIRM))
    return b.as_markup()


# ── Result screen ─────────────────────────────────────────────────────────────
def result_keyboard(
    options: dict[str, str],
    correct: str,
    selected: str,
    removed: list[str],
) -> InlineKeyboardMarkup:
    """Shows answer buttons with correct/wrong highlights; all disabled."""
    b = InlineKeyboardBuilder()
    for letter in ("A", "B", "C", "D"):
        if letter in removed and letter != correct:
            b.button(text="—", callback_data=NOOP)
        elif letter == correct and letter == selected:
            b.button(text=f"✅  {letter}) {options[letter]}", callback_data=NOOP)
        elif letter == correct:
            b.button(text=f"✅  {letter}) {options[letter]}", callback_data=NOOP)
        elif letter == selected:
            b.button(text=f"❌  {letter}) {options[letter]}", callback_data=NOOP)
        else:
            b.button(text=f"     {letter}) {options[letter]}", callback_data=NOOP)
    b.adjust(2)
    return b.as_markup()


def correct_answer_keyboard(is_final: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if is_final:
        b.row(_btn("🏆  Ещё раз сыграть!", PLAY_AGAIN))
    else:
        b.row(_btn("➡️  Следующий вопрос", NEXT_Q))
        b.row(_btn("🚶  Забрать деньги и уйти", QUIT_GAME))
    return b.as_markup()


def game_over_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_btn("🔄  Играть снова", PLAY_AGAIN))
    return b.as_markup()


# ── Loading placeholder ───────────────────────────────────────────────────────
def loading_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_noop("⏳  Генерирую вопрос…"))
    return b.as_markup()


def back_to_game_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(_noop("◀️  Закрыть"))
    return b.as_markup()
