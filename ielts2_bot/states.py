from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class SpeakingStates(StatesGroup):
    choosing_part  = State()
    choosing_topic = State()
    entering_custom_topic = State()
    part1_answering   = State()
    part2_preparing   = State()  # 1-min countdown
    part2_answering   = State()
    part3_answering   = State()
    assessing         = State()
    viewing_results   = State()


class TopicAction(CallbackData, prefix="topic"):
    action: str  # "accept" | "another" | "custom"


class ResultAction(CallbackData, prefix="result"):
    action: str  # "retry" | "menu"


class InterruptAction(CallbackData, prefix="interrupt"):
    action: str   # "continue" | "new"
    new_part: int


class QuestionAction(CallbackData, prefix="question"):
    action: str  # "replay"
