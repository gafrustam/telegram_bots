from aiogram.fsm.state import State, StatesGroup


class VPRStates(StatesGroup):
    # Grade & mode selection
    choosing_grade = State()
    choosing_mode = State()

    # Single-task training
    choosing_task_type = State()
    task_in_progress = State()

    # Full test
    test_info = State()
    test_in_progress = State()
    viewing_test_results = State()

    # Statistics
    viewing_stats = State()
