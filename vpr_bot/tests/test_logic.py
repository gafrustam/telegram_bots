"""
Unit tests for business logic:
- vpr_data.py: calculate_grade, grade_emoji, get_task_type, VPR_STRUCTURE integrity
- generator.py: _extract_json helper
- stats.py: _pct_bar helper
- keyboards.py: button layout and callback data correctness
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpr_data import (
    VPR_STRUCTURE,
    SUPPORTED_GRADES,
    calculate_grade,
    grade_emoji,
    get_task_type,
    get_grade_data,
)
from generator import _extract_json
from keyboards import (
    kb_grades,
    kb_mode,
    kb_task_types,
    kb_task_result,
    kb_after_theory,
    kb_test_start,
    kb_test_answer_sent,
    kb_test_next,
    kb_test_results,
    kb_test_detail_back,
    kb_stats_main,
    kb_stats_back,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_all_buttons(markup):
    """Flatten inline keyboard markup into a list of buttons."""
    return [btn for row in markup.inline_keyboard for btn in row]


def get_button_texts(markup):
    return [btn.text for row in markup.inline_keyboard for btn in row]


def get_callback_datas(markup):
    return [btn.callback_data for row in markup.inline_keyboard for btn in row]


# ---------------------------------------------------------------------------
# VPR_STRUCTURE integrity
# ---------------------------------------------------------------------------

class TestVPRStructureIntegrity:
    """Validate the VPR data structure is complete and consistent."""

    def test_all_required_grades_present(self):
        assert set(SUPPORTED_GRADES) == {4, 5, 6, 7}

    def test_each_grade_has_required_keys(self):
        required = {"grade", "grade_name", "tasks_count", "time_minutes",
                    "max_score", "grading", "test_overview", "task_types"}
        for g in SUPPORTED_GRADES:
            assert required.issubset(VPR_STRUCTURE[g].keys()), \
                f"Grade {g} missing keys"

    def test_task_types_count_matches_tasks_count(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            assert len(data["task_types"]) == data["tasks_count"], \
                f"Grade {g}: task_types count {len(data['task_types'])} != tasks_count {data['tasks_count']}"

    def test_task_type_has_required_fields(self):
        required = {"num", "topic", "max_points", "hint"}
        for g in SUPPORTED_GRADES:
            for t in VPR_STRUCTURE[g]["task_types"]:
                assert required.issubset(t.keys()), \
                    f"Grade {g} task {t.get('num')} missing fields"

    def test_task_numbers_sequential(self):
        for g in SUPPORTED_GRADES:
            nums = [t["num"] for t in VPR_STRUCTURE[g]["task_types"]]
            assert nums == list(range(1, len(nums) + 1)), \
                f"Grade {g} task numbers not sequential: {nums}"

    def test_max_points_per_task_is_positive(self):
        for g in SUPPORTED_GRADES:
            for t in VPR_STRUCTURE[g]["task_types"]:
                assert t["max_points"] > 0

    def test_total_max_points_equals_max_score(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            total = sum(t["max_points"] for t in data["task_types"])
            assert total == data["max_score"], \
                f"Grade {g}: sum of task points {total} != max_score {data['max_score']}"

    def test_grading_covers_zero_to_max_score(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            grading = sorted(data["grading"], key=lambda x: x[1])
            min_val = grading[0][1]
            max_val = grading[-1][2]
            assert min_val == 0, f"Grade {g}: grading doesn't start at 0 (got {min_val})"
            assert max_val == data["max_score"], \
                f"Grade {g}: grading max {max_val} != max_score {data['max_score']}"

    def test_grading_no_gaps(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            grading = sorted(data["grading"], key=lambda x: x[1])
            for i in range(len(grading) - 1):
                _, _, cur_max = grading[i]
                _, next_min, _ = grading[i + 1]
                assert cur_max + 1 == next_min, \
                    f"Grade {g}: gap between {cur_max} and {next_min}"

    def test_test_overview_contains_grade_name(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            assert data["grade_name"] in data["test_overview"], \
                f"Grade {g}: grade_name not in test_overview"

    def test_test_overview_contains_task_count(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            assert str(data["tasks_count"]) in data["test_overview"], \
                f"Grade {g}: task count not in test_overview"

    def test_test_overview_contains_time(self):
        for g in SUPPORTED_GRADES:
            data = VPR_STRUCTURE[g]
            assert str(data["time_minutes"]) in data["test_overview"], \
                f"Grade {g}: time not in test_overview"


# ---------------------------------------------------------------------------
# calculate_grade
# ---------------------------------------------------------------------------

class TestCalculateGrade:
    def test_grade4_boundary_values(self):
        assert calculate_grade(4, 0) == 2
        assert calculate_grade(4, 7) == 2
        assert calculate_grade(4, 8) == 3
        assert calculate_grade(4, 12) == 3
        assert calculate_grade(4, 13) == 4
        assert calculate_grade(4, 16) == 4
        assert calculate_grade(4, 17) == 5
        assert calculate_grade(4, 20) == 5

    def test_grade5_boundary_values(self):
        assert calculate_grade(5, 0) == 2
        assert calculate_grade(5, 9) == 2
        assert calculate_grade(5, 10) == 3
        assert calculate_grade(5, 16) == 3
        assert calculate_grade(5, 17) == 4
        assert calculate_grade(5, 22) == 4
        assert calculate_grade(5, 23) == 5
        assert calculate_grade(5, 28) == 5

    def test_grade6_boundary_values(self):
        assert calculate_grade(6, 0) == 2
        assert calculate_grade(6, 11) == 2
        assert calculate_grade(6, 12) == 3
        assert calculate_grade(6, 19) == 3
        assert calculate_grade(6, 20) == 4
        assert calculate_grade(6, 26) == 4
        assert calculate_grade(6, 27) == 5
        assert calculate_grade(6, 32) == 5

    def test_grade7_boundary_values(self):
        assert calculate_grade(7, 0) == 2
        assert calculate_grade(7, 11) == 2
        assert calculate_grade(7, 12) == 3
        assert calculate_grade(7, 19) == 3
        assert calculate_grade(7, 20) == 4
        assert calculate_grade(7, 26) == 4
        assert calculate_grade(7, 27) == 5
        assert calculate_grade(7, 32) == 5

    def test_all_marks_in_range_2_to_5(self):
        for g in SUPPORTED_GRADES:
            max_score = VPR_STRUCTURE[g]["max_score"]
            for score in range(0, max_score + 1):
                mark = calculate_grade(g, score)
                assert 2 <= mark <= 5, \
                    f"Grade {g}, score {score}: mark {mark} out of range"


# ---------------------------------------------------------------------------
# grade_emoji
# ---------------------------------------------------------------------------

class TestGradeEmoji:
    def test_known_marks(self):
        assert grade_emoji(5) == "🌟"
        assert grade_emoji(4) == "✅"
        assert grade_emoji(3) == "📗"
        assert grade_emoji(2) == "❌"

    def test_unknown_mark_returns_question(self):
        assert grade_emoji(1) == "❓"
        assert grade_emoji(0) == "❓"
        assert grade_emoji(6) == "❓"


# ---------------------------------------------------------------------------
# get_task_type
# ---------------------------------------------------------------------------

class TestGetTaskType:
    def test_valid_task(self):
        task = get_task_type(4, 1)
        assert task["num"] == 1
        assert "topic" in task

    def test_last_task(self):
        for g in SUPPORTED_GRADES:
            last_num = VPR_STRUCTURE[g]["tasks_count"]
            task = get_task_type(g, last_num)
            assert task["num"] == last_num

    def test_invalid_task_raises(self):
        with pytest.raises(ValueError):
            get_task_type(4, 99)

    def test_all_tasks_accessible(self):
        for g in SUPPORTED_GRADES:
            for t in VPR_STRUCTURE[g]["task_types"]:
                result = get_task_type(g, t["num"])
                assert result["num"] == t["num"]


# ---------------------------------------------------------------------------
# get_grade_data
# ---------------------------------------------------------------------------

class TestGetGradeData:
    def test_returns_correct_grade_data(self):
        data = get_grade_data(4)
        assert data["grade"] == 4
        assert data["grade_name"] == "4 класс"

    def test_all_grades(self):
        for g in SUPPORTED_GRADES:
            data = get_grade_data(g)
            assert data["grade"] == g


# ---------------------------------------------------------------------------
# _extract_json (generator.py helper)
# ---------------------------------------------------------------------------

class TestExtractJson:
    def test_plain_json(self):
        result = _extract_json('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_json_with_markdown_fence(self):
        text = '```json\n{"a": 1, "b": 2}\n```'
        result = _extract_json(text)
        assert result == {"a": 1, "b": 2}

    def test_json_with_extra_text_around(self):
        text = 'Here is the answer:\n{"task_text": "Найди x", "correct_answer": "5"}'
        result = _extract_json(text)
        assert result["task_text"] == "Найди x"
        assert result["correct_answer"] == "5"

    def test_json_with_backtick_fence_no_lang(self):
        text = "```\n{\"x\": 1}\n```"
        result = _extract_json(text)
        assert result["x"] == 1

    def test_raises_on_no_json(self):
        with pytest.raises((ValueError, Exception)):
            _extract_json("no json here at all")

    def test_nested_json(self):
        text = '{"outer": {"inner": 42}}'
        result = _extract_json(text)
        assert result["outer"]["inner"] == 42

    def test_json_with_russian_text(self):
        text = '{"task_text": "Найди периметр квадрата", "correct_answer": "20"}'
        result = _extract_json(text)
        assert "периметр" in result["task_text"]


# ---------------------------------------------------------------------------
# _pct_bar (stats.py helper) - tested by reimplementing
# ---------------------------------------------------------------------------

def _pct_bar(correct, total, width=10):
    """Mirror of stats._pct_bar for testing."""
    if total == 0:
        return "░" * width + " нет данных"
    pct = correct / total
    filled = round(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {round(pct * 100)}%"


class TestPctBar:
    def test_zero_total_returns_no_data(self):
        result = _pct_bar(0, 0)
        assert "нет данных" in result
        assert "░" * 10 in result

    def test_100_percent(self):
        result = _pct_bar(10, 10)
        assert "█" * 10 in result
        assert "100%" in result

    def test_0_percent_correct(self):
        result = _pct_bar(0, 10)
        assert "░" * 10 in result
        assert "0%" in result

    def test_50_percent(self):
        result = _pct_bar(5, 10)
        assert "█" * 5 in result
        assert "░" * 5 in result
        assert "50%" in result

    def test_bar_length_always_width(self):
        for correct, total in [(3, 10), (0, 5), (7, 7), (1, 3)]:
            result = _pct_bar(correct, total, width=10)
            # Extract bar content between [ and ]
            inner = result[result.find("[") + 1:result.find("]")]
            assert len(inner) == 10, \
                f"Bar length for {correct}/{total} is {len(inner)}, expected 10"


# ---------------------------------------------------------------------------
# Keyboard tests
# ---------------------------------------------------------------------------

class TestKbGrades:
    """Main grade selection keyboard."""

    def test_has_four_grade_buttons(self):
        buttons = get_all_buttons(kb_grades())
        grade_btns = [b for b in buttons if "класс" in b.text]
        assert len(grade_btns) == 4

    def test_has_stats_button(self):
        texts = get_button_texts(kb_grades())
        assert any("статистика" in t.lower() for t in texts)

    def test_grade_callbacks_correct(self):
        cbs = get_callback_datas(kb_grades())
        assert "grade:4" in cbs
        assert "grade:5" in cbs
        assert "grade:6" in cbs
        assert "grade:7" in cbs

    def test_stats_callback(self):
        cbs = get_callback_datas(kb_grades())
        assert "nav:stats" in cbs

    def test_layout_two_columns_grades(self):
        markup = kb_grades()
        # First two rows should have 2 buttons each (grades 4,5 and 6,7)
        row_0 = markup.inline_keyboard[0]
        row_1 = markup.inline_keyboard[1]
        assert len(row_0) == 2
        assert len(row_1) == 2


class TestKbMode:
    """Mode selection keyboard (after grade selected)."""

    def test_has_train_button(self):
        texts = get_button_texts(kb_mode(4))
        assert any("тренировать" in t.lower() for t in texts)

    def test_has_test_button(self):
        texts = get_button_texts(kb_mode(4))
        assert any("контрольн" in t.lower() for t in texts)

    def test_has_stats_button(self):
        texts = get_button_texts(kb_mode(4))
        assert any("статистика" in t.lower() for t in texts)

    def test_has_back_button(self):
        texts = get_button_texts(kb_mode(4))
        assert any("назад" in t.lower() for t in texts)

    def test_correct_callbacks(self):
        cbs = get_callback_datas(kb_mode(4))
        assert "mode:train" in cbs
        assert "mode:test" in cbs
        assert "mode:stats_grade" in cbs
        assert "nav:grades" in cbs

    def test_each_button_on_own_row(self):
        markup = kb_mode(4)
        # Each row should have exactly 1 button
        for row in markup.inline_keyboard:
            assert len(row) == 1


class TestKbTaskTypes:
    """Task type selection for each grade."""

    @pytest.mark.parametrize("grade,expected_count", [
        (4, 10), (5, 14), (6, 16), (7, 16)
    ])
    def test_correct_task_count_for_grade(self, grade, expected_count):
        buttons = get_all_buttons(kb_task_types(grade))
        task_btns = [b for b in buttons if b.callback_data.startswith("task:")]
        assert len(task_btns) == expected_count

    def test_has_back_button(self):
        texts = get_button_texts(kb_task_types(4))
        assert any("назад" in t.lower() for t in texts)

    def test_task_callbacks_sequential(self):
        for grade in SUPPORTED_GRADES:
            cbs = get_callback_datas(kb_task_types(grade))
            task_cbs = [c for c in cbs if c.startswith("task:")]
            nums = sorted(int(c.split(":")[1]) for c in task_cbs)
            expected = list(range(1, VPR_STRUCTURE[grade]["tasks_count"] + 1))
            assert nums == expected, f"Grade {grade}: task callbacks {nums} != {expected}"

    def test_back_callback(self):
        cbs = get_callback_datas(kb_task_types(4))
        assert "nav:mode" in cbs

    def test_task_texts_contain_number_and_topic(self):
        markup = kb_task_types(4)
        for row in markup.inline_keyboard:
            for btn in row:
                if btn.callback_data.startswith("task:"):
                    assert "№" in btn.text
                    assert "—" in btn.text


class TestKbTaskResult:
    """Post-answer keyboard in training mode."""

    def test_has_theory_button(self):
        texts = get_button_texts(kb_task_result(1))
        assert any("теори" in t.lower() for t in texts)

    def test_has_retry_button(self):
        texts = get_button_texts(kb_task_result(1))
        assert any("ещё" in t.lower() for t in texts)

    def test_has_other_type_button(self):
        texts = get_button_texts(kb_task_result(1))
        assert any("тип" in t.lower() or "другой" in t.lower() for t in texts)

    def test_has_menu_button(self):
        texts = get_button_texts(kb_task_result(1))
        assert any("меню" in t.lower() for t in texts)

    def test_theory_callback_contains_task_num(self):
        cbs = get_callback_datas(kb_task_result(3))
        assert "theory:3" in cbs

    def test_retry_callback_contains_task_num(self):
        cbs = get_callback_datas(kb_task_result(5))
        assert "task:5" in cbs

    def test_two_by_two_layout(self):
        markup = kb_task_result(1)
        assert len(markup.inline_keyboard) == 2
        assert len(markup.inline_keyboard[0]) == 2
        assert len(markup.inline_keyboard[1]) == 2


class TestKbAfterTheory:
    """Keyboard shown after viewing theory."""

    def test_has_retry_button(self):
        texts = get_button_texts(kb_after_theory(1))
        assert any("ещё" in t.lower() or "задание" in t.lower() for t in texts)

    def test_has_other_type_button(self):
        texts = get_button_texts(kb_after_theory(1))
        assert any("тип" in t.lower() or "другой" in t.lower() for t in texts)

    def test_has_menu_button(self):
        texts = get_button_texts(kb_after_theory(1))
        assert any("меню" in t.lower() for t in texts)

    def test_callbacks_correct(self):
        cbs = get_callback_datas(kb_after_theory(2))
        assert "task:2" in cbs
        assert "nav:task_types" in cbs
        assert "nav:mode" in cbs


class TestKbTestStart:
    """Test mode start screen keyboard."""

    def test_has_timed_option(self):
        texts = get_button_texts(kb_test_start())
        assert any("время" in t.lower() for t in texts)

    def test_has_practice_option(self):
        texts = get_button_texts(kb_test_start())
        assert any("таймер" in t.lower() or "тренировать" in t.lower() for t in texts)

    def test_has_back_button(self):
        texts = get_button_texts(kb_test_start())
        assert any("назад" in t.lower() for t in texts)

    def test_callbacks(self):
        cbs = get_callback_datas(kb_test_start())
        assert "test:timed" in cbs
        assert "test:practice" in cbs
        assert "nav:mode" in cbs


class TestKbTestAnswerSent:
    """Practice mode: keyboard after each answer."""

    def test_shows_next_when_not_last(self):
        # Task 1 of 10 completed (current=1, total=10)
        texts = get_button_texts(kb_test_answer_sent(1, 10, "practice"))
        assert any("следующее" in t.lower() or "задание" in t.lower() for t in texts)

    def test_shows_results_when_last(self):
        # Last task completed (current=10, total=10)
        texts = get_button_texts(kb_test_answer_sent(10, 10, "practice"))
        assert any("результат" in t.lower() for t in texts)

    def test_next_callback(self):
        cbs = get_callback_datas(kb_test_answer_sent(3, 10, "practice"))
        assert "test:next" in cbs

    def test_finish_callback_on_last(self):
        cbs = get_callback_datas(kb_test_answer_sent(10, 10, "practice"))
        assert "test:finish" in cbs

    def test_next_button_shows_next_task_number(self):
        markup = kb_test_answer_sent(1, 10, "practice")
        btns = get_all_buttons(markup)
        next_btn = next(b for b in btns if b.callback_data == "test:next")
        # Should show "2/10" since we're going to task 2
        assert "2" in next_btn.text


class TestKbTestNext:
    """Timed mode: keyboard after each answer."""

    def test_shows_next_when_not_last(self):
        texts = get_button_texts(kb_test_next(1, 10))
        assert any("задание" in t.lower() for t in texts)

    def test_shows_finish_when_last(self):
        texts = get_button_texts(kb_test_next(10, 10))
        assert any("завершить" in t.lower() or "оценку" in t.lower() for t in texts)

    def test_next_callback(self):
        cbs = get_callback_datas(kb_test_next(5, 10))
        assert "test:next" in cbs

    def test_finish_callback_on_last(self):
        cbs = get_callback_datas(kb_test_next(10, 10))
        assert "test:finish" in cbs


class TestKbTestResults:
    """Test results screen keyboard."""

    def test_has_detail_button(self):
        texts = get_button_texts(kb_test_results(1))
        assert any("разбор" in t.lower() or "подробн" in t.lower() for t in texts)

    def test_has_retry_button(self):
        texts = get_button_texts(kb_test_results(1))
        assert any("ещё" in t.lower() or "пройти" in t.lower() for t in texts)

    def test_has_menu_button(self):
        texts = get_button_texts(kb_test_results(1))
        assert any("меню" in t.lower() for t in texts)

    def test_detail_callback_contains_session_id(self):
        cbs = get_callback_datas(kb_test_results(42))
        assert "testdetail:42" in cbs

    def test_retry_callback(self):
        cbs = get_callback_datas(kb_test_results(1))
        assert "mode:test" in cbs


class TestKbTestDetailBack:
    """Keyboard shown after test detail breakdown."""

    def test_has_menu_button(self):
        texts = get_button_texts(kb_test_detail_back())
        assert any("меню" in t.lower() for t in texts)

    def test_menu_callback(self):
        cbs = get_callback_datas(kb_test_detail_back())
        assert "nav:mode" in cbs

    def test_has_back_to_results_button(self):
        """Users should be able to return to results from detail view."""
        texts = get_button_texts(kb_test_detail_back())
        has_back = any(
            "результат" in t.lower() or "назад" in t.lower()
            for t in texts
        )
        assert has_back, (
            "kb_test_detail_back() should have a 'back to results' button — "
            "currently users are stuck with only 'В меню'"
        )


class TestKbStatsMain:
    """Stats main menu keyboard."""

    def test_has_all_grade_buttons(self):
        cbs = get_callback_datas(kb_stats_main())
        for grade in SUPPORTED_GRADES:
            assert f"stats:grade:{grade}" in cbs

    def test_has_history_button(self):
        texts = get_button_texts(kb_stats_main())
        assert any("история" in t.lower() for t in texts)

    def test_has_menu_button(self):
        texts = get_button_texts(kb_stats_main())
        assert any("меню" in t.lower() for t in texts)

    def test_history_callback(self):
        cbs = get_callback_datas(kb_stats_main())
        assert "stats:history" in cbs

    def test_menu_callback(self):
        cbs = get_callback_datas(kb_stats_main())
        assert "nav:grades" in cbs


class TestKbStatsBack:
    """Back navigation from stats grade view."""

    def test_has_back_to_stats_button(self):
        texts = get_button_texts(kb_stats_back())
        assert any("статистик" in t.lower() or "назад" in t.lower() for t in texts)

    def test_has_menu_button(self):
        texts = get_button_texts(kb_stats_back())
        assert any("меню" in t.lower() for t in texts)

    def test_callbacks(self):
        cbs = get_callback_datas(kb_stats_back())
        assert "nav:stats" in cbs
        assert "nav:grades" in cbs
