from aiogram.fsm.state import State, StatesGroup


class SetupStates(StatesGroup):
    choosing_prog_language = State()
    choosing_level = State()


class ProblemStates(StatesGroup):
    solving = State()          # ждём код от пользователя
    viewing_wrong = State()    # неверный ответ, можно посмотреть тест или сдаться
    entering_errors = State()  # бот спросил «где ошибка?»
    after_errors = State()     # пользователь перечислил ошибки


class SettingsStates(StatesGroup):
    main = State()
    changing_time = State()
    changing_prog_language = State()
    changing_level = State()
    changing_bot_language = State()
