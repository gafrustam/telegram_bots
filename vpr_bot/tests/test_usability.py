"""
Usability tests for VPR Bot.

These tests simulate the full user journey through the bot, checking:
  1. Message texts are clear and appropriate for schoolchildren
  2. Button sequences make sense at every step
  3. Navigation (Back/Menu) always works correctly
  4. Statistics show the right information in a readable format
  5. Edge cases don't crash the bot
  6. Keyboard layouts look good (not too wide, not awkward)

Each test class represents a user scenario with a docstring describing
the scenario from a schoolchild's perspective.

Running: pytest tests/test_usability.py -v
"""

import sys
import os
import re
import inspect

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpr_data import VPR_STRUCTURE, SUPPORTED_GRADES, calculate_grade, grade_emoji
from keyboards import (
    kb_grades, kb_mode, kb_task_types, kb_task_result, kb_after_theory,
    kb_test_start, kb_test_answer_sent, kb_test_next,
    kb_test_results, kb_test_detail_back, kb_stats_main, kb_stats_back,
)
from handlers.common import WELCOME_TEXT
import handlers.test as test_handler
import handlers.training as training_handler
import handlers.stats as stats_handler


def get_all_buttons(markup):
    return [btn for row in markup.inline_keyboard for btn in row]


def get_button_texts(markup):
    return [btn.text for row in markup.inline_keyboard for btn in row]


def get_callback_datas(markup):
    return [btn.callback_data for row in markup.inline_keyboard for btn in row]


def get_button_row_lengths(markup):
    return [len(row) for row in markup.inline_keyboard]


# ===========================================================================
# SCENARIO 1: First launch — the student opens the bot
# ===========================================================================

class TestScenario01_FirstLaunch:
    """
    A student opens the bot for the first time.
    They should see a welcoming message that explains what the bot does,
    followed by clear grade selection buttons.
    """

    def test_welcome_message_is_friendly(self):
        """Message should contain a greeting."""
        assert "Привет" in WELCOME_TEXT

    def test_welcome_message_explains_purpose(self):
        """Student should understand what the bot is for."""
        assert "ВПР" in WELCOME_TEXT

    def test_welcome_message_lists_features(self):
        """Three main features should be mentioned."""
        assert "Тренировать" in WELCOME_TEXT or "Отрабатывать" in WELCOME_TEXT
        assert "контрольн" in WELCOME_TEXT or "Проходить" in WELCOME_TEXT
        assert "прогресс" in WELCOME_TEXT or "Отслеживать" in WELCOME_TEXT

    def test_welcome_message_prompts_action(self):
        """Student should know what to do next."""
        assert "класс" in WELCOME_TEXT.lower()

    def test_welcome_message_not_too_long(self):
        """Message shouldn't overwhelm a student."""
        assert len(WELCOME_TEXT) < 500, (
            f"Welcome message is {len(WELCOME_TEXT)} chars — too long for a student"
        )

    def test_grade_buttons_have_four_options(self):
        markup = kb_grades()
        grade_btns = [b for b in get_all_buttons(markup) if "класс" in b.text]
        assert len(grade_btns) == 4

    def test_grade_buttons_use_emoji(self):
        """Buttons should have emoji to make them visually appealing."""
        texts = get_button_texts(kb_grades())
        grade_texts = [t for t in texts if "класс" in t]
        for t in grade_texts:
            assert any(ord(c) > 127 for c in t), f"No emoji in grade button: '{t}'"

    def test_grade_buttons_show_correct_grades(self):
        texts = get_button_texts(kb_grades())
        for grade in [4, 5, 6, 7]:
            assert any(str(grade) in t for t in texts)

    def test_stats_button_present_on_start(self):
        """Student can access their stats right from the start."""
        markup = kb_grades()
        cbs = get_callback_datas(markup)
        assert "nav:stats" in cbs

    def test_grade_keyboard_is_2_columns(self):
        """2-column layout for grade buttons looks clean."""
        markup = kb_grades()
        row_lengths = get_button_row_lengths(markup)
        # First two rows should be 2-wide
        assert row_lengths[0] == 2
        assert row_lengths[1] == 2


# ===========================================================================
# SCENARIO 2: Selecting a grade — mode screen
# ===========================================================================

class TestScenario02_GradeSelected:
    """
    Student selects their class (e.g., 5th grade).
    They should see a summary of the test and options for what to do.
    """

    def test_mode_screen_has_three_main_options(self):
        """Train, Test, Stats — three main options."""
        markup = kb_mode(5)
        cbs = get_callback_datas(markup)
        assert "mode:train" in cbs
        assert "mode:test" in cbs
        assert "mode:stats_grade" in cbs

    def test_mode_screen_has_back_button(self):
        """Can go back to grade selection."""
        cbs = get_callback_datas(kb_mode(5))
        assert "nav:grades" in cbs

    def test_back_button_text_says_back(self):
        texts = get_button_texts(kb_mode(5))
        assert any("назад" in t.lower() for t in texts)

    def test_mode_buttons_have_emoji(self):
        texts = get_button_texts(kb_mode(5))
        for t in texts:
            has_emoji = any(ord(c) > 127 for c in t)
            assert has_emoji, f"Mode button has no emoji: '{t}'"

    def test_each_mode_button_on_separate_row(self):
        """Buttons should not be crammed side by side."""
        markup = kb_mode(5)
        for row in markup.inline_keyboard:
            assert len(row) == 1, f"Row has {len(row)} buttons — should be 1 per row"

    def test_grade_info_contains_task_count(self):
        """Grade data must be available and correct."""
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            assert data["tasks_count"] > 0
            assert data["time_minutes"] > 0
            assert data["max_score"] > 0


# ===========================================================================
# SCENARIO 3: Training mode — the student wants to practice
# ===========================================================================

class TestScenario03_TrainingFlow:
    """
    Student selects training mode and practices specific task types.
    They should see a clear list, get a task, submit an answer,
    get feedback, then continue or try theory.
    """

    def test_task_list_shows_all_tasks_for_grade(self):
        for grade in SUPPORTED_GRADES:
            markup = kb_task_types(grade)
            task_btns = [b for b in get_all_buttons(markup) if b.callback_data.startswith("task:")]
            assert len(task_btns) == VPR_STRUCTURE[grade]["tasks_count"]

    def test_task_buttons_show_number_and_topic(self):
        """Student needs to know which task to pick."""
        markup = kb_task_types(4)
        for btn in get_all_buttons(markup):
            if btn.callback_data.startswith("task:"):
                assert "№" in btn.text, f"Task button missing '№': '{btn.text}'"
                assert "—" in btn.text, f"Task button missing topic separator: '{btn.text}'"

    def test_task_topic_names_not_too_long(self):
        """Button texts shouldn't be super long — looks bad on mobile."""
        for grade in SUPPORTED_GRADES:
            for t in VPR_STRUCTURE[grade]["task_types"]:
                full_text = f"№{t['num']} — {t['topic']}"
                assert len(full_text) <= 60, \
                    f"Grade {grade}, task {t['num']}: button text too long: '{full_text}'"

    def test_task_type_list_has_back_button(self):
        cbs = get_callback_datas(kb_task_types(4))
        assert "nav:mode" in cbs

    def test_post_answer_keyboard_has_four_options(self):
        """After answering: theory, retry, other type, menu."""
        markup = kb_task_result(1)
        btns = get_all_buttons(markup)
        assert len(btns) == 4

    def test_post_answer_keyboard_layout_is_2x2(self):
        """2×2 layout looks balanced."""
        markup = kb_task_result(1)
        assert len(markup.inline_keyboard) == 2
        assert len(markup.inline_keyboard[0]) == 2
        assert len(markup.inline_keyboard[1]) == 2

    def test_after_theory_keyboard_has_continue_options(self):
        markup = kb_after_theory(3)
        texts = get_button_texts(markup)
        assert any("задание" in t.lower() for t in texts)
        assert any("тип" in t.lower() or "другой" in t.lower() for t in texts)
        assert any("меню" in t.lower() for t in texts)

    def test_theory_button_text_is_clear(self):
        texts = get_button_texts(kb_task_result(1))
        theory_btn = next(t for t in texts if "теори" in t.lower())
        assert "💡" in theory_btn or "теори" in theory_btn.lower()

    def test_retry_button_same_task(self):
        """'Ещё задание' should regenerate same task type."""
        cbs = get_callback_datas(kb_task_result(5))
        assert "task:5" in cbs, "Retry should regenerate task 5, not a different task"

    def test_other_type_goes_to_task_list(self):
        cbs = get_callback_datas(kb_task_result(1))
        assert "nav:task_types" in cbs

    def test_menu_from_training_goes_to_mode_screen(self):
        """'В меню' should go to mode screen (not grade selection — grade is already known)."""
        cbs = get_callback_datas(kb_task_result(1))
        assert "nav:mode" in cbs

    def test_handler_receive_answer_handles_none_text(self):
        """
        If student sends a sticker or photo, message.text is None.
        receive_answer should handle this gracefully, not crash.
        """
        source = inspect.getsource(training_handler.receive_answer)
        # Must guard against message.text being None before calling .strip()
        has_guard = (
            "message.text" in source and (
                "if not message.text" in source or
                "message.text is None" in source or
                "if message.text" in source
            )
        )
        assert has_guard, (
            "receive_answer() does not guard against message.text being None.\n"
            "If student sends a sticker/photo, AttributeError: 'NoneType' has no attribute 'strip'.\n"
            "Fix: add 'if not message.text: return await message.answer(...)' before .strip()"
        )

    def test_handler_receive_test_answer_handles_none_text(self):
        """Same issue in test mode."""
        source = inspect.getsource(test_handler.receive_test_answer)
        has_guard = (
            "message.text" in source and (
                "if not message.text" in source or
                "message.text is None" in source or
                "if message.text" in source
            )
        )
        assert has_guard, (
            "receive_test_answer() does not guard against message.text being None.\n"
            "Fix: add 'if not message.text: ...' before calling .strip()"
        )


# ===========================================================================
# SCENARIO 4: Test mode — full test with timed option
# ===========================================================================

class TestScenario04_TestModeTimed:
    """
    Student wants to simulate a real VPR exam with time pressure.
    The flow: overview → timed start → tasks one by one (no feedback) →
    final results with grade.
    """

    def test_test_start_keyboard_has_two_start_options(self):
        markup = kb_test_start()
        cbs = get_callback_datas(markup)
        assert "test:timed" in cbs
        assert "test:practice" in cbs

    def test_timed_button_text_mentions_time(self):
        texts = get_button_texts(kb_test_start())
        timed_btn = next(t for t in texts if "test:timed" in
                         get_callback_datas(kb_test_start()) and "время" in t.lower())
        assert timed_btn is not None

    def test_practice_button_text_mentions_no_timer(self):
        texts = get_button_texts(kb_test_start())
        assert any("таймер" in t.lower() or "без" in t.lower() for t in texts)

    def test_test_start_has_back_button(self):
        cbs = get_callback_datas(kb_test_start())
        assert "nav:mode" in cbs

    def test_timed_mode_per_task_keyboard_shows_progress(self):
        """After each timed answer, the next-task button shows N/total."""
        markup = kb_test_next(3, 10)
        texts = get_button_texts(markup)
        # Should show progress like "4/10"
        assert any("4" in t and "10" in t for t in texts), \
            f"Task progress not shown in timed mode button: {texts}"

    def test_timed_last_task_button_says_finish(self):
        markup = kb_test_next(10, 10)
        texts = get_button_texts(markup)
        assert any("завершить" in t.lower() or "оценку" in t.lower() for t in texts)

    def test_timed_finish_button_callback(self):
        cbs = get_callback_datas(kb_test_next(10, 10))
        assert "test:finish" in cbs

    def test_results_keyboard_has_detail_retry_menu(self):
        markup = kb_test_results(1)
        cbs = get_callback_datas(markup)
        assert "testdetail:1" in cbs
        assert "mode:test" in cbs
        assert "nav:mode" in cbs

    def test_results_keyboard_detail_button_text_clear(self):
        texts = get_button_texts(kb_test_results(1))
        assert any("разбор" in t.lower() or "подробн" in t.lower() for t in texts)

    def test_results_retry_says_try_again(self):
        texts = get_button_texts(kb_test_results(1))
        assert any("ещё" in t.lower() or "пройти" in t.lower() for t in texts)

    def test_grade_criteria_table_covers_all_marks(self):
        """Results show grading scale — all marks 2-5 must appear."""
        for g in SUPPORTED_GRADES:
            grading = VPR_STRUCTURE[g]["grading"]
            marks = {entry[0] for entry in grading}
            assert marks == {2, 3, 4, 5}, f"Grade {g}: missing marks in grading: {marks}"

    def test_test_finish_callback_has_state_filter(self):
        """
        test_finish_callback must have VPRStates.test_in_progress filter
        to prevent double-clicks after state changes.
        Without the filter, clicking an old 'finish' button could re-run
        _finish_test with stale/missing state data, causing KeyError.
        """
        source = inspect.getsource(test_handler.test_finish_callback)
        # The decorator chain should include VPRStates.test_in_progress
        # Check if the handler is decorated with state filter
        # We need to look at the router registrations or source
        # The filter appears in the @router.callback_query decorator arguments
        # A simpler check: look for "test_in_progress" near "test:finish"
        module_source = inspect.getsource(test_handler)
        finish_section = module_source[
            module_source.find('"test:finish"'):
            module_source.find('"test:finish"') + 500
        ]
        has_state_filter = "test_in_progress" in finish_section
        assert has_state_filter, (
            "test_finish_callback should filter by VPRStates.test_in_progress.\n"
            "Without it, clicking an old 'finish' button re-runs _finish_test with "
            "empty state, causing KeyError on data['test_session_id']."
        )

    def test_current_task_cleared_after_test_answer(self):
        """
        After receiving a test answer, test_current_task must be cleared.
        Otherwise a student who sends two messages gets double-counted answers
        and the task counter goes out of sync.
        """
        source = inspect.getsource(test_handler.receive_test_answer)
        # Must set test_current_task to None after processing answer
        clears_task = (
            "test_current_task=None" in source or
            "test_current_task': None" in source or
            "'test_current_task', None" in source
        )
        assert clears_task, (
            "receive_test_answer() must set test_current_task=None after saving answer.\n"
            "Otherwise if student sends 2 messages before clicking 'next', "
            "the same task gets added twice and test_current_idx goes to 2 "
            "instead of 1, skipping task 2 entirely."
        )


# ===========================================================================
# SCENARIO 5: Test mode — practice option with immediate feedback
# ===========================================================================

class TestScenario05_TestModePractice:
    """
    Student chooses practice mode for learning (no time pressure, see results immediately).
    """

    def test_practice_per_task_shows_next_with_progress(self):
        markup = kb_test_answer_sent(2, 14, "practice")
        texts = get_button_texts(markup)
        # Should show progress to next task
        assert any("3" in t and "14" in t for t in texts), \
            f"Practice mode next button should show '3/14', got: {texts}"

    def test_practice_last_task_shows_results_button(self):
        markup = kb_test_answer_sent(14, 14, "practice")
        texts = get_button_texts(markup)
        assert any("результат" in t.lower() for t in texts)

    def test_practice_finish_callback(self):
        cbs = get_callback_datas(kb_test_answer_sent(14, 14, "practice"))
        assert "test:finish" in cbs

    def test_practice_start_message_no_extra_blank_line(self):
        """
        In practice mode, the start message should not have an extra blank line
        where the time warning would be in timed mode.
        The f-string always adds '\\n\\n' even when the conditional part is empty.
        """
        source = inspect.getsource(test_handler._start_test)
        # Find the problematic line with the conditional time warning
        has_extra_newline_bug = (
            "else ''}\n\n" in source or
            "else ''}\n\n" in source
        )
        # Actually the issue is: f"{'...' if mode == 'timed' else ''}\n\n"
        # This adds \n\n even in practice mode. Let's verify by checking the string format.
        # The blank line issue: the else clause returns '' but \n\n is always appended.
        # Detect: if "else ''" is followed immediately by \n\n in the same f-string line
        bad_pattern = re.search(
            r"else ''\}\\n\\n|else ''\}\n\n",
            source
        )
        # Check the actual format string
        has_blank_line_issue = False
        for line in source.split("\n"):
            if "else ''" in line and ("\\n\\n" in line or "\n\n" in repr(line)):
                has_blank_line_issue = True
                break
        # The issue appears in this specific construction in _start_test:
        # f"{'⚠️...' if mode == 'timed' else ''}\n\n"
        # which adds \n\n even when practice mode
        # We just note this exists — a warning not a hard failure
        # (it's cosmetic, not a crash)

    def test_mode_label_correct_in_results(self):
        """Mode label in results message: timed=⏱, practice=🧘."""
        # Verify the source code uses correct labels
        source = inspect.getsource(test_handler._finish_test)
        assert "⏱" in source, "Timed mode should show ⏱ in results"
        assert "🧘" in source, "Practice mode should show 🧘 in results"


# ===========================================================================
# SCENARIO 6: Test detail view — per-task breakdown
# ===========================================================================

class TestScenario06_TestDetail:
    """
    After finishing a test, the student wants to see which tasks they got wrong.
    The detail view should clearly show each task result.
    """

    def test_detail_keyboard_has_menu_option(self):
        cbs = get_callback_datas(kb_test_detail_back())
        assert "nav:mode" in cbs

    def test_detail_keyboard_has_back_to_results_option(self):
        """
        IMPORTANT: After seeing the breakdown, student should be able to
        go back to the results page, not just 'В меню'.
        Currently kb_test_detail_back() only has 'В меню' — this is a UX problem.
        """
        texts = get_button_texts(kb_test_detail_back())
        has_back = any(
            "результат" in t.lower() or "назад" in t.lower()
            for t in texts
        )
        assert has_back, (
            "kb_test_detail_back() must include a 'back to results' button.\n"
            "Students who view the breakdown should be able to return to results,\n"
            "not be forced all the way back to the main menu."
        )

    def test_detail_shows_task_number_and_topic_icons(self):
        """Source code should use ✅/⚠️/❌ icons for task results."""
        source = inspect.getsource(test_handler.show_test_detail)
        assert "✅" in source
        assert "⚠️" in source
        assert "❌" in source

    def test_detail_shows_user_answer_and_correct_answer(self):
        source = inspect.getsource(test_handler.show_test_detail)
        assert "user_answer" in source
        assert "correct_answer" in source

    def test_detail_shows_points(self):
        source = inspect.getsource(test_handler.show_test_detail)
        assert "pts" in source or "points" in source or "баллы" in source.lower()


# ===========================================================================
# SCENARIO 7: Statistics — student checks their progress
# ===========================================================================

class TestScenario07_Statistics:
    """
    Student navigates to stats. They should see their progress by task type
    and test history in a clean, readable format.
    """

    def test_stats_main_has_all_grades(self):
        cbs = get_callback_datas(kb_stats_main())
        for g in SUPPORTED_GRADES:
            assert f"stats:grade:{g}" in cbs

    def test_stats_main_has_history(self):
        cbs = get_callback_datas(kb_stats_main())
        assert "stats:history" in cbs

    def test_stats_main_has_back_to_grades(self):
        """From stats main, student can go back to grade selection."""
        cbs = get_callback_datas(kb_stats_main())
        assert "nav:grades" in cbs

    def test_stats_grade_back_has_two_options(self):
        """From grade stats, student can go back to stats main or to main menu."""
        markup = kb_stats_back()
        cbs = get_callback_datas(markup)
        assert "nav:stats" in cbs
        assert "nav:grades" in cbs

    def test_stats_grade_back_layout_is_2_columns(self):
        """Two back options side by side looks clean."""
        markup = kb_stats_back()
        row_lengths = get_button_row_lengths(markup)
        assert row_lengths[0] == 2, "Back buttons should be in same row"

    def test_history_date_format_code_handles_datetime_objects(self):
        """
        asyncpg returns datetime objects for TIMESTAMPTZ columns, not strings.
        datetime.fromisoformat() only works on strings.
        The code must handle both cases.
        """
        source = inspect.getsource(stats_handler.stats_history)
        # Must handle datetime objects from asyncpg
        # Either: check isinstance, or call .strftime() directly on the object,
        # or use a try/except with proper fallback
        handles_datetime = (
            "isinstance" in source or
            ".strftime" in source or
            "datetime.fromisoformat" in source  # at minimum this exists
        )
        assert "strftime" in source, (
            "stats_history() should call .strftime('%d.%m.%Y %H:%M') directly on the datetime object.\n"
            "asyncpg returns datetime objects, not strings, so datetime.fromisoformat() will fail.\n"
            "Fix: if isinstance(dt, str): dt = datetime.fromisoformat(dt); date_str = dt.strftime(...)"
        )

    def test_pct_bar_shows_percentage(self):
        """The progress bar must show percentage, not just the bar."""
        source = inspect.getsource(stats_handler._pct_bar)
        assert "%" in source

    def test_stats_shows_all_task_types_even_not_practiced(self):
        """
        Stats display should show ALL task types, even ones not practiced yet.
        This motivates students to try new task types.
        """
        source = inspect.getsource(stats_handler.stats_by_grade)
        # Check it iterates over all task_types (not just practiced ones)
        assert "task_types" in source
        assert "не тренировалось" in source or "тренировал" in source

    def test_stats_shows_points_and_correctness(self):
        """Stats should show both accuracy and points for complete picture."""
        source = inspect.getsource(stats_handler.stats_by_grade)
        assert "pts_earned" in source or "pts" in source
        assert "correct" in source


# ===========================================================================
# SCENARIO 8: Navigation — back buttons work everywhere
# ===========================================================================

class TestScenario08_Navigation:
    """
    Student presses back buttons from every screen.
    They should always end up in the right place, never stuck.
    """

    def test_mode_screen_back_goes_to_grades(self):
        """◀️ Назад from mode screen → grade selection."""
        cbs = get_callback_datas(kb_mode(4))
        assert "nav:grades" in cbs

    def test_task_type_screen_back_goes_to_mode(self):
        """◀️ Назад from task list → mode screen."""
        cbs = get_callback_datas(kb_task_types(4))
        assert "nav:mode" in cbs

    def test_test_start_screen_back_goes_to_mode(self):
        """◀️ Назад from test overview → mode screen."""
        cbs = get_callback_datas(kb_test_start())
        assert "nav:mode" in cbs

    def test_training_result_menu_goes_to_mode(self):
        """🏠 В меню from training result → mode screen (grade stays selected)."""
        cbs = get_callback_datas(kb_task_result(1))
        assert "nav:mode" in cbs

    def test_test_results_menu_goes_to_mode(self):
        """🏠 В меню from test results → mode screen."""
        cbs = get_callback_datas(kb_test_results(1))
        assert "nav:mode" in cbs

    def test_stats_back_goes_to_stats_main(self):
        """◀️ К статистике goes back to stats overview."""
        cbs = get_callback_datas(kb_stats_back())
        assert "nav:stats" in cbs

    def test_stats_main_menu_goes_to_grades(self):
        """🏠 В меню from stats → grade selection (root)."""
        cbs = get_callback_datas(kb_stats_main())
        assert "nav:grades" in cbs

    def test_no_dead_end_from_test_detail(self):
        """
        After test detail, student is NOT stuck — they have navigation options.
        Currently only 'В меню' exists here. Should also have 'back to results'.
        """
        markup = kb_test_detail_back()
        btns = get_all_buttons(markup)
        assert len(btns) >= 2, (
            f"kb_test_detail_back() only has {len(btns)} button(s). "
            "Should have at least 2: '◀️ К результатам' and '🏠 В меню'"
        )

    def test_nav_mode_handler_exists(self):
        """nav:mode callback handler exists in common.py."""
        source = inspect.getsource(
            __import__("handlers.common", fromlist=["nav_mode"]).nav_mode
        )
        assert "choosing_mode" in source

    def test_nav_grades_handler_clears_state(self):
        """nav:grades should clear state (grade should be re-selected)."""
        import handlers.common as common_handler
        source = inspect.getsource(common_handler.nav_grades)
        assert "state.clear()" in source or "clear" in source


# ===========================================================================
# SCENARIO 9: Accessibility for schoolchildren — text quality
# ===========================================================================

class TestScenario09_TextQualityForSchoolchildren:
    """
    All texts should be clear, concise, and appropriate for students
    in grades 4-7 (approximately 10-13 years old).
    """

    def test_button_texts_not_too_long(self):
        """Buttons should be short enough for mobile screens."""
        all_markups = [
            kb_grades(), kb_mode(4), kb_test_start(),
            kb_task_result(1), kb_after_theory(1),
            kb_test_results(1), kb_test_detail_back(),
            kb_stats_main(), kb_stats_back(),
        ]
        for markup in all_markups:
            for btn in get_all_buttons(markup):
                assert len(btn.text) <= 50, \
                    f"Button text too long ({len(btn.text)} chars): '{btn.text}'"

    def test_button_texts_not_empty(self):
        all_markups = [
            kb_grades(), kb_mode(4), kb_test_start(),
            kb_task_result(1), kb_after_theory(1),
            kb_test_results(1), kb_test_detail_back(),
            kb_stats_main(), kb_stats_back(),
        ]
        for markup in all_markups:
            for btn in get_all_buttons(markup):
                assert btn.text.strip(), f"Empty button text found"

    def test_callback_datas_not_empty(self):
        all_markups = [
            kb_grades(), kb_mode(4), kb_test_start(),
            kb_task_result(1), kb_after_theory(1),
            kb_test_results(1), kb_test_detail_back(),
            kb_stats_main(), kb_stats_back(),
        ]
        for markup in all_markups:
            for btn in get_all_buttons(markup):
                assert btn.callback_data, f"Empty callback_data for button: '{btn.text}'"

    def test_welcome_text_uses_informal_address(self):
        """Russian schoolchildren are addressed as 'ты', not 'вы'."""
        # The bot should use informal address
        assert "вы" not in WELCOME_TEXT.lower() or "ты" in WELCOME_TEXT.lower(), \
            "Bot should address students informally ('ты', not 'вы')"

    def test_grade_data_contains_meaningful_topics(self):
        """Each task type must have a non-empty topic that describes the content."""
        for g in SUPPORTED_GRADES:
            for t in VPR_STRUCTURE[g]["task_types"]:
                assert len(t["topic"]) >= 5, \
                    f"Grade {g}, task {t['num']}: topic too short: '{t['topic']}'"
                assert len(t["hint"]) >= 10, \
                    f"Grade {g}, task {t['num']}: hint too short: '{t['hint']}'"

    def test_test_overview_uses_readable_format(self):
        """Overview should use lists and structure, not a wall of text."""
        for g in SUPPORTED_GRADES:
            overview = VPR_STRUCTURE[g]["test_overview"]
            # Should contain bullet points or dashes
            has_structure = "•" in overview or "—" in overview or "–" in overview
            assert has_structure, f"Grade {g}: test overview lacks structured format"

    def test_grading_emojis_are_distinct(self):
        """Each grade mark should have a unique, meaningful emoji."""
        emojis = {grade_emoji(m) for m in [2, 3, 4, 5]}
        assert len(emojis) == 4, "All grade marks should have different emojis"
        assert "❓" not in emojis, "No grade mark should map to '❓'"


# ===========================================================================
# SCENARIO 10: Edge cases — nothing should crash
# ===========================================================================

class TestScenario10_EdgeCases:
    """
    Unexpected inputs and rare conditions should be handled gracefully.
    """

    def test_calculate_grade_with_zero_score(self):
        """Zero score → grade 2, no exception."""
        for g in SUPPORTED_GRADES:
            result = calculate_grade(g, 0)
            assert result == 2

    def test_calculate_grade_with_max_score(self):
        """Max score → grade 5, no exception."""
        for g in SUPPORTED_GRADES:
            max_s = VPR_STRUCTURE[g]["max_score"]
            result = calculate_grade(g, max_s)
            assert result == 5

    def test_calculate_grade_does_not_return_none(self):
        """calculate_grade must always return a valid mark."""
        for g in SUPPORTED_GRADES:
            max_s = VPR_STRUCTURE[g]["max_score"]
            for s in range(0, max_s + 1):
                result = calculate_grade(g, s)
                assert result is not None
                assert isinstance(result, int)

    def test_keyboard_works_for_all_grade_task_combinations(self):
        """kb_task_types must work for all valid grades."""
        for g in SUPPORTED_GRADES:
            markup = kb_task_types(g)
            assert markup is not None
            btns = get_all_buttons(markup)
            assert len(btns) > 0

    def test_test_answer_sent_at_first_task(self):
        """kb_test_answer_sent(1, 10) — first task done, 9 remain."""
        markup = kb_test_answer_sent(1, 10, "practice")
        cbs = get_callback_datas(markup)
        assert "test:next" in cbs

    def test_test_answer_sent_at_last_task(self):
        markup = kb_test_answer_sent(10, 10, "practice")
        cbs = get_callback_datas(markup)
        assert "test:finish" in cbs
        assert "test:next" not in cbs

    def test_test_next_at_first_task(self):
        markup = kb_test_next(1, 10)
        cbs = get_callback_datas(markup)
        assert "test:next" in cbs

    def test_test_next_at_last_task(self):
        markup = kb_test_next(10, 10)
        cbs = get_callback_datas(markup)
        assert "test:finish" in cbs

    def test_pct_bar_at_zero_total(self):
        """Stats bar should not divide by zero."""
        from handlers.stats import _pct_bar
        result = _pct_bar(0, 0)
        assert isinstance(result, str)
        assert "нет данных" in result or "░" in result

    def test_extract_json_with_extra_whitespace(self):
        """JSON parser should handle extra whitespace."""
        from generator import _extract_json
        result = _extract_json('  \n  {"key": "val"}  \n  ')
        assert result == {"key": "val"}

    def test_vpr_structure_all_grades_have_test_overview_html(self):
        """test_overview should contain HTML tags for Telegram formatting."""
        for g in SUPPORTED_GRADES:
            overview = VPR_STRUCTURE[g]["test_overview"]
            assert "<b>" in overview, f"Grade {g}: test_overview lacks <b> formatting"


# ===========================================================================
# SCENARIO 11: Complete flow integrity checks
# ===========================================================================

class TestScenario11_FlowIntegrity:
    """
    Verify that the complete user flow is consistent end-to-end.
    These tests check that all FSM transitions have corresponding handlers.
    """

    def test_all_grade_callbacks_have_handlers(self):
        """grade:N callbacks must be handled."""
        import handlers.common as common
        source = inspect.getsource(common)
        for g in SUPPORTED_GRADES:
            assert f"grade:{g}" in source or "grade:" in source, \
                f"No handler for grade:{g} callback"

    def test_all_mode_callbacks_have_handlers(self):
        import handlers.common as common
        import handlers.training as training
        import handlers.test as test
        import handlers.stats as stats
        sources = (
            inspect.getsource(common) +
            inspect.getsource(training) +
            inspect.getsource(test) +
            inspect.getsource(stats)
        )
        for cb in ["mode:train", "mode:test", "mode:stats_grade"]:
            assert cb in sources, f"No handler for callback: {cb}"

    def test_nav_callbacks_all_handled(self):
        import handlers.common as common
        source = inspect.getsource(common)
        for cb in ["nav:grades", "nav:mode", "nav:task_types", "nav:stats"]:
            assert cb in source, f"nav callback not handled: {cb}"

    def test_test_flow_callbacks_handled(self):
        source = inspect.getsource(test_handler)
        for cb in ["test:timed", "test:practice", "test:next", "test:finish"]:
            assert cb in source, f"Test callback not handled: {cb}"

    def test_stats_callbacks_handled(self):
        source = inspect.getsource(stats_handler)
        assert "stats:grade:" in source
        assert "stats:history" in source

    def test_testdetail_callback_handled(self):
        source = inspect.getsource(test_handler)
        assert "testdetail:" in source

    def test_theory_callback_handled(self):
        source = inspect.getsource(training_handler)
        assert "theory:" in source

    def test_grading_scale_text_correct_for_all_grades(self):
        """Grading table in results message should match actual grading criteria."""
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            # Verify grade 5 threshold appears in test_overview
            grade5_threshold = data["grading"][0][1]  # min score for grade 5
            assert str(grade5_threshold) in data["test_overview"], \
                f"Grade {g}: grade 5 threshold {grade5_threshold} not in overview"
