"""
Unit tests for formatter.py — user stats and admin panel formatting.
"""
import sys
import os
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formatter import (
    _band_emoji,
    _format_band_bar,
    _val,
    format_assessment,
    format_error,
    format_user_stats,
    format_admin_summary,
)


# ── _band_emoji ──────────────────────────────────────────

class TestBandEmoji:
    def test_diamond_for_9(self):
        assert _band_emoji(9.0) == "💎"

    def test_green_for_high_bands(self):
        for band in (8.5, 8.0, 7.5, 7.0):
            assert _band_emoji(band) == "🟢", f"Expected 🟢 for band {band}"

    def test_yellow_for_b2(self):
        for band in (6.5, 6.0, 5.5):
            assert _band_emoji(band) == "🟡", f"Expected 🟡 for band {band}"

    def test_orange_for_b1(self):
        for band in (5.0, 4.5, 4.0):
            assert _band_emoji(band) == "🟠", f"Expected 🟠 for band {band}"

    def test_red_for_low_bands(self):
        for band in (3.5, 3.0, 2.0, 1.0, 0.0):
            assert _band_emoji(band) == "🔴", f"Expected 🔴 for band {band}"

    def test_white_for_unknown_band(self):
        # 9.5 is not in the BAND_EMOJI dict
        assert _band_emoji(9.5) == "⚪"

    def test_rounds_to_nearest_half(self):
        # 6.7 * 2 = 13.4 → round to 13 → 6.5 → 🟡
        assert _band_emoji(6.7) == "🟡"
        # 6.8 * 2 = 13.6 → round to 14 → 7.0 → 🟢
        assert _band_emoji(6.8) == "🟢"
        # 6.2 * 2 = 12.4 → round to 12 → 6.0 → 🟡
        assert _band_emoji(6.2) == "🟡"


# ── _format_band_bar ─────────────────────────────────────

class TestFormatBandBar:
    def test_zero_band(self):
        bar = _format_band_bar(0.0)
        assert bar == "░" * 9

    def test_full_band(self):
        bar = _format_band_bar(9.0)
        assert bar == "▓" * 9

    def test_integer_band(self):
        bar = _format_band_bar(5.0)
        assert bar == "▓" * 5 + "░" * 4

    def test_half_band(self):
        bar = _format_band_bar(5.5)
        assert bar == "▓" * 5 + "▒" + "░" * 3

    def test_length_always_9(self):
        for band in (0.0, 1.5, 4.0, 6.5, 9.0):
            bar = _format_band_bar(band)
            # Count characters (each is 1 char)
            assert len(bar) == 9, f"Bar length should be 9 for band {band}"


# ── _val ─────────────────────────────────────────────────

class TestVal:
    def test_none_returns_dash(self):
        assert _val(None) == "—"

    def test_custom_default(self):
        assert _val(None, default="n/a") == "n/a"

    def test_float_value(self):
        assert _val(7.0) == "7.0"

    def test_string_value(self):
        assert _val("hello") == "hello"

    def test_zero_is_not_default(self):
        assert _val(0) == "0"


# ── format_assessment ────────────────────────────────────

class TestFormatAssessment:
    FULL_DATA = {
        "overall_band": 7.0,
        "fluency_coherence": {
            "band": 7.0,
            "explanation": "Speaks at length with minor hesitations.",
            "examples": ["I was going... erm... to the store", "Well, basically"],
        },
        "lexical_resource": {
            "band": 6.5,
            "explanation": "Good range of vocabulary.",
            "examples": [],
        },
        "grammatical_range_accuracy": {
            "band": 7.0,
            "explanation": "Complex structures used.",
            "examples": ["If I had known, I would have gone"],
        },
        "pronunciation": {
            "band": 6.5,
            "explanation": "Generally clear.",
            "examples": [],
        },
    }

    def test_error_key_shows_warning(self):
        result = format_assessment({"error": "Connection failed"})
        assert "⚠️" in result
        assert "Connection failed" in result

    def test_overall_band_in_output(self):
        result = format_assessment(self.FULL_DATA)
        assert "7.0" in result
        assert "Overall Band Score" in result

    def test_all_criteria_present(self):
        result = format_assessment(self.FULL_DATA)
        assert "Fluency & Coherence" in result
        assert "Lexical Resource" in result
        assert "Grammatical Range & Accuracy" in result
        assert "Pronunciation" in result

    def test_html_escaping_in_examples(self):
        data = dict(self.FULL_DATA)
        data["fluency_coherence"] = {
            "band": 7.0,
            "explanation": "Good <progress> & effort",
            "examples": ["Use of <b>tags</b> & ampersand"],
        }
        result = format_assessment(data)
        assert "<b>tags</b>" not in result  # should be escaped
        assert "&amp;" in result or "&lt;" in result

    def test_returns_string(self):
        assert isinstance(format_assessment(self.FULL_DATA), str)


# ── format_error ─────────────────────────────────────────

class TestFormatError:
    def test_contains_error_text(self):
        result = format_error("Something went wrong")
        assert "Something went wrong" in result

    def test_contains_error_marker(self):
        result = format_error("timeout")
        assert "❌" in result

    def test_html_escaping(self):
        result = format_error("Error: <unknown> & bad")
        assert "<unknown>" not in result
        assert "&lt;" in result or "&amp;" in result


# ── format_user_stats ────────────────────────────────────

class TestFormatUserStats:
    BASE_STATS = {
        "total_sessions": 10,
        "completed": 8,
        "avg_overall": 6.5,
        "best_overall": 7.5,
        "sessions_7d": 3,
        "avg_7d": 7.0,
        "part1_count": 4,
        "part2_count": 2,
        "part3_count": 2,
        "avg_part1": 6.5,
        "avg_part2": 6.0,
        "avg_part3": 7.0,
        "avg_fc": 6.5,
        "avg_lr": 6.0,
        "avg_gra": 6.5,
        "avg_pron": 7.0,
    }

    def test_total_sessions_shown(self):
        result = format_user_stats(self.BASE_STATS, [])
        assert "10" in result

    def test_completed_sessions_shown(self):
        result = format_user_stats(self.BASE_STATS, [])
        assert "8" in result

    def test_average_band_shown(self):
        result = format_user_stats(self.BASE_STATS, [])
        assert "6.5" in result

    def test_part_counts_shown(self):
        result = format_user_stats(self.BASE_STATS, [])
        assert "Part 1" in result
        assert "Part 2" in result
        assert "Part 3" in result

    def test_criteria_averages_shown(self):
        result = format_user_stats(self.BASE_STATS, [])
        assert "Fluency & Coherence" in result
        assert "Lexical Resource" in result

    def test_recent_results_section_shown(self):
        recent = [
            {
                "part": 1,
                "topic": "Travel",
                "overall_band": 7.0,
                "created_at": datetime(2026, 2, 10, 12, 0, 0),
            }
        ]
        result = format_user_stats(self.BASE_STATS, recent)
        assert "Последние результаты" in result
        assert "Travel" in result
        assert "7.0" in result

    def test_no_recent_section_when_empty(self):
        result = format_user_stats(self.BASE_STATS, [])
        assert "Последние результаты" not in result

    def test_none_values_shown_as_dash(self):
        stats = dict(self.BASE_STATS)
        stats["avg_overall"] = None
        stats["avg_fc"] = None
        result = format_user_stats(stats, [])
        assert "—" in result


# ── format_admin_summary ─────────────────────────────────

class TestFormatAdminSummary:
    BASE_STATS = {
        "total_users": 150,
        "new_1d": 5,   "new_2d": 8,   "new_3d": 10,
        "new_7d": 30,  "new_14d": 55, "new_30d": 90,
        "active_1d": 12,  "active_2d": 20,  "active_3d": 25,
        "active_7d": 60,  "active_14d": 90, "active_30d": 130,
        "completed_users_1d": 8,  "completed_users_2d": 15,
        "completed_users_3d": 18, "completed_users_7d": 45,
        "completed_users_14d": 70,"completed_users_30d": 110,
        "sessions_1d": 15,  "sessions_2d": 28,  "sessions_3d": 35,
        "sessions_7d": 90,  "sessions_14d": 150,"sessions_30d": 250,
        "minutes_1d": 22.5, "minutes_2d": 42.0, "minutes_3d": 55.0,
        "minutes_7d": 130.0,"minutes_14d": 220.0,"minutes_30d": 370.0,
    }

    BASE_RETENTION = {
        "cohort_size": 100,
        "ret_d1": 60,
        "ret_d3": 40,
        "ret_d7": 25,
        "ret_d14": 15,
        "ret_d30": 8,
    }

    def test_empty_stats_returns_no_data_message(self):
        result = format_admin_summary({}, {})
        assert "Нет данных" in result

    def test_total_users_shown(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "150" in result

    def test_new_users_row_present(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "Новые" in result

    def test_active_users_row_present(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "Активные" in result

    def test_sessions_row_present(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "Сессий" in result

    def test_minutes_row_present(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "Минуты" in result

    def test_retention_shown_when_cohort_nonzero(self):
        result = format_admin_summary(self.BASE_STATS, self.BASE_RETENTION)
        assert "Ретеншн" in result
        assert "D1" in result
        assert "D30" in result

    def test_retention_percentages_calculated(self):
        result = format_admin_summary(self.BASE_STATS, self.BASE_RETENTION)
        # D1: 60/100 = 60%
        assert "60%" in result
        # D7: 25/100 = 25%
        assert "25%" in result

    def test_no_retention_section_when_empty(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "Ретеншн" not in result

    def test_no_retention_when_cohort_zero(self):
        retention = {"cohort_size": 0, "ret_d1": 0}
        result = format_admin_summary(self.BASE_STATS, retention)
        assert "Ретеншн" not in result

    def test_missing_stat_keys_use_zero_default(self):
        # Only provide total_users, rest missing
        result = format_admin_summary({"total_users": 5}, {})
        # Should not raise; missing keys default to "0"
        assert "5" in result

    def test_returns_html_with_bold_tags(self):
        result = format_admin_summary(self.BASE_STATS, {})
        assert "<b>" in result

    def test_returns_string(self):
        assert isinstance(format_admin_summary(self.BASE_STATS, self.BASE_RETENTION), str)
