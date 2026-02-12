from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class SpeakingStates(StatesGroup):
    choosing_part = State()
    choosing_topic = State()
    part1_answering = State()
    part2_answering = State()
    part3_answering = State()
    assessing = State()
    viewing_results = State()


class TopicAction(CallbackData, prefix="topic"):
    action: str  # "accept" or "another"


class ResultAction(CallbackData, prefix="result"):
    action: str  # "retry" or "menu"


class AdminAction(CallbackData, prefix="admin"):
    page: str  # "overview", "daily", "top_users", "parts"
