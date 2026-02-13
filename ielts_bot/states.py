from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class SpeakingStates(StatesGroup):
    choosing_part = State()
    choosing_topic = State()
    part1_answering = State()
    part2_preparing = State()    # countdown before Part 2
    part2_answering = State()
    part3_answering = State()
    assessing = State()
    viewing_results = State()


class TopicAction(CallbackData, prefix="topic"):
    action: str  # "accept" or "another"


class ResultAction(CallbackData, prefix="result"):
    action: str  # "retry" or "menu"


class AdminAction(CallbackData, prefix="admin"):
    page: str  # "overview", "growth", "scores", "users", "usage", "outliers"


class InterruptAction(CallbackData, prefix="interrupt"):
    action: str  # "continue" or "new"
    new_part: int
