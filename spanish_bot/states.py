from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class ConversationStates(StatesGroup):
    menu = State()
    viewing_vocab = State()
    conversing = State()
    assessing = State()
    viewing_results = State()


class TopicAction(CallbackData, prefix="topic"):
    action: str  # "start" or "another"


class ResultAction(CallbackData, prefix="result"):
    action: str  # "new" or "menu"
