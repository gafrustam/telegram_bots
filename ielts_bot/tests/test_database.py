"""
Unit tests for database.py — stats queries and admin panel DB functions.

All tests use mocks so no real database connection is required.
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database


# ── is_available ─────────────────────────────────────────

class TestIsAvailable:
    def test_false_when_pool_is_none(self):
        with patch.object(database, "_pool", None):
            assert database.is_available() is False

    def test_true_when_pool_set(self):
        with patch.object(database, "_pool", MagicMock()):
            assert database.is_available() is True


# ── Low-level helpers ────────────────────────────────────

class TestLowLevelHelpers:
    @pytest.mark.asyncio
    async def test_execute_returns_empty_when_no_pool(self):
        with patch.object(database, "_pool", None):
            result = await database._execute("SELECT 1")
            assert result == ""

    @pytest.mark.asyncio
    async def test_fetchrow_returns_none_when_no_pool(self):
        with patch.object(database, "_pool", None):
            result = await database._fetchrow("SELECT 1")
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_returns_empty_list_when_no_pool(self):
        with patch.object(database, "_pool", None):
            result = await database._fetch("SELECT 1")
            assert result == []

    @pytest.mark.asyncio
    async def test_fetchval_returns_none_when_no_pool(self):
        with patch.object(database, "_pool", None):
            result = await database._fetchval("SELECT 1")
            assert result is None


# ── get_user_stats ───────────────────────────────────────

class TestGetUserStats:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_sessions(self):
        row = {"total_sessions": 0}
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=row):
            result = await database.get_user_stats(123)
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_row_is_none(self):
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=None):
            result = await database.get_user_stats(123)
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_dict_with_valid_data(self):
        row = {
            "total_sessions": 5,
            "completed": 4,
            "avg_overall": 6.5,
            "avg_fc": 6.0,
            "avg_lr": 6.5,
            "avg_gra": 6.0,
            "avg_pron": 7.0,
            "best_overall": 7.0,
            "avg_7d": 6.5,
            "sessions_7d": 2,
            "part1_count": 2,
            "part2_count": 1,
            "part3_count": 1,
            "avg_part1": 6.5,
            "avg_part2": 6.0,
            "avg_part3": 7.0,
        }
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=row):
            result = await database.get_user_stats(123)
            assert result is not None
            assert result["total_sessions"] == 5
            assert result["avg_overall"] == 6.5

    @pytest.mark.asyncio
    async def test_passes_user_id_to_query(self):
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=None) as mock_fr:
            await database.get_user_stats(999)
            call_args = mock_fr.call_args
            # user_id 999 should appear in the args
            assert 999 in call_args.args


# ── get_user_recent_assessments ──────────────────────────

class TestGetUserRecentAssessments:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_data(self):
        with patch("database._fetch", new_callable=AsyncMock, return_value=[]):
            result = await database.get_user_recent_assessments(123)
            assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self):
        from datetime import datetime
        rows = [
            {"part": 1, "topic": "Work", "overall_band": 6.5,
             "created_at": datetime(2026, 2, 1)},
            {"part": 2, "topic": "Travel", "overall_band": 7.0,
             "created_at": datetime(2026, 2, 5)},
        ]
        with patch("database._fetch", new_callable=AsyncMock, return_value=rows):
            result = await database.get_user_recent_assessments(123)
            assert len(result) == 2
            assert result[0]["topic"] == "Work"
            assert result[1]["overall_band"] == 7.0

    @pytest.mark.asyncio
    async def test_default_limit_is_5(self):
        with patch("database._fetch", new_callable=AsyncMock, return_value=[]) as mock_f:
            await database.get_user_recent_assessments(123)
            call_args = mock_f.call_args
            assert 5 in call_args.args


# ── get_admin_summary_stats ──────────────────────────────

class TestGetAdminSummaryStats:
    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_pool(self):
        with patch.object(database, "_pool", None):
            result = await database.get_admin_summary_stats()
            assert result == {}

    @pytest.mark.asyncio
    async def test_merges_two_rows(self):
        row1 = {
            "new_1d": 5, "new_2d": 10, "new_3d": 12,
            "new_7d": 30, "new_14d": 50, "new_30d": 80,
            "total_users": 200,
        }
        row2 = {
            "active_1d": 15, "active_2d": 25, "active_3d": 30,
            "active_7d": 70, "active_14d": 110, "active_30d": 180,
            "completed_users_1d": 10, "completed_users_2d": 18,
            "completed_users_3d": 22, "completed_users_7d": 55,
            "completed_users_14d": 85, "completed_users_30d": 150,
            "sessions_1d": 20, "sessions_2d": 35, "sessions_3d": 45,
            "sessions_7d": 100, "sessions_14d": 170, "sessions_30d": 280,
            "minutes_1d": 30.0, "minutes_2d": 55.0, "minutes_3d": 70.0,
            "minutes_7d": 160.0, "minutes_14d": 270.0, "minutes_30d": 450.0,
        }
        with patch("database._fetchrow", new_callable=AsyncMock, side_effect=[row1, row2]):
            result = await database.get_admin_summary_stats()
            assert result["total_users"] == 200
            assert result["active_1d"] == 15
            assert result["sessions_7d"] == 100
            assert result["minutes_30d"] == 450.0

    @pytest.mark.asyncio
    async def test_handles_none_row(self):
        with patch("database._fetchrow", new_callable=AsyncMock, side_effect=[None, None]):
            result = await database.get_admin_summary_stats()
            assert result == {}


# ── get_admin_retention ──────────────────────────────────

class TestGetAdminRetention:
    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_pool(self):
        with patch.object(database, "_pool", None):
            result = await database.get_admin_retention()
            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_row_is_none(self):
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=None):
            result = await database.get_admin_retention()
            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_retention_dict(self):
        row = {
            "cohort_size": 100,
            "ret_d1": 65,
            "ret_d3": 45,
            "ret_d7": 30,
            "ret_d14": 18,
            "ret_d30": 9,
        }
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=row):
            result = await database.get_admin_retention()
            assert result["cohort_size"] == 100
            assert result["ret_d1"] == 65
            assert result["ret_d30"] == 9

    @pytest.mark.asyncio
    async def test_all_retention_keys_present(self):
        row = {
            "cohort_size": 50,
            "ret_d1": 30, "ret_d3": 20,
            "ret_d7": 10, "ret_d14": 5, "ret_d30": 2,
        }
        with patch("database._fetchrow", new_callable=AsyncMock, return_value=row):
            result = await database.get_admin_retention()
            for key in ("cohort_size", "ret_d1", "ret_d3", "ret_d7", "ret_d14", "ret_d30"):
                assert key in result


# ── save_assessment ──────────────────────────────────────

class TestSaveAssessment:
    @pytest.mark.asyncio
    async def test_skips_when_session_id_is_none(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.save_assessment(None, 1, {"overall_band": 7.0})
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_execute_with_valid_session(self):
        result_data = {
            "overall_band": 7.0,
            "fluency_coherence": {"band": 7.0},
            "lexical_resource": {"band": 6.5},
            "grammatical_range_accuracy": {"band": 7.0},
            "pronunciation": {"band": 6.5},
        }
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.save_assessment(42, 123, result_data)
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args.args
            # session_id=42, user_id=123, overall_band=7.0
            assert 42 in call_args
            assert 123 in call_args
            assert 7.0 in call_args

    @pytest.mark.asyncio
    async def test_defaults_missing_bands_to_zero(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.save_assessment(1, 1, {"overall_band": 6.0})
            call_args = mock_exec.call_args.args
            # Missing criteria bands should default to 0.0
            assert 0.0 in call_args


# ── complete_session ─────────────────────────────────────

class TestCompleteSession:
    @pytest.mark.asyncio
    async def test_skips_when_session_id_is_none(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.complete_session(None, 120.0)
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_execute_with_session_id(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.complete_session(7, 90.5)
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args.args
            assert 7 in call_args
            assert 90.5 in call_args


# ── fail_session ─────────────────────────────────────────

class TestFailSession:
    @pytest.mark.asyncio
    async def test_skips_when_session_id_is_none(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.fail_session(None)
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_execute_with_session_id(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.fail_session(5)
            mock_exec.assert_called_once()
            assert 5 in mock_exec.call_args.args


# ── mark_topic_accepted ──────────────────────────────────

class TestMarkTopicAccepted:
    @pytest.mark.asyncio
    async def test_skips_when_topic_id_is_none(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.mark_topic_accepted(None)
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_execute_with_topic_id(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.mark_topic_accepted(99)
            mock_exec.assert_called_once()
            assert 99 in mock_exec.call_args.args


# ── get_random_topic ─────────────────────────────────────

class TestGetRandomTopic:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_bank_topics(self):
        with patch("database._fetch", new_callable=AsyncMock, side_effect=[[], []]):
            result = await database.get_random_topic(1, 123)
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_dict_from_bank(self):
        bank = [
            {"id": 1, "part": 1, "topic": "Travel", "weight": 1.0,
             "cue_card": None, "questions": None},
        ]
        # used_topics: no prior accepted topics
        with patch("database._fetch", new_callable=AsyncMock, side_effect=[[], bank]):
            result = await database.get_random_topic(1, 123)
            assert result is not None
            assert result["topic"] == "Travel"

    @pytest.mark.asyncio
    async def test_avoids_recently_used_topics(self):
        used = [{"topic": "Travel"}]
        bank = [
            {"id": 1, "part": 1, "topic": "Travel", "weight": 1.0,
             "cue_card": None, "questions": None},
            {"id": 2, "part": 1, "topic": "Work", "weight": 1.0,
             "cue_card": None, "questions": None},
        ]
        with patch("database._fetch", new_callable=AsyncMock, side_effect=[used, bank]):
            # Run multiple times to confirm "Travel" is avoided
            results = set()
            for _ in range(10):
                with patch("database._fetch", new_callable=AsyncMock, side_effect=[used, bank]):
                    r = await database.get_random_topic(1, 123)
                    results.add(r["topic"])
            assert "Work" in results
            # Travel should not appear since it's the only used one
            # (with 2 topics, Work is always chosen when Travel is filtered)
            assert "Travel" not in results

    @pytest.mark.asyncio
    async def test_falls_back_to_all_when_all_used(self):
        used = [{"topic": "Travel"}]
        bank = [
            {"id": 1, "part": 1, "topic": "Travel", "weight": 1.0,
             "cue_card": None, "questions": None},
        ]
        # When all topics are used, it should fall back to allowing all
        with patch("database._fetch", new_callable=AsyncMock, side_effect=[used, bank]):
            result = await database.get_random_topic(1, 123)
            assert result is not None
            assert result["topic"] == "Travel"


# ── upsert_user ──────────────────────────────────────────

class TestUpsertUser:
    @pytest.mark.asyncio
    async def test_calls_execute(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.upsert_user(1, "alice", "Alice", "Smith")
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_user_params(self):
        with patch("database._execute", new_callable=AsyncMock) as mock_exec:
            await database.upsert_user(42, "bob", "Bob", None)
            args = mock_exec.call_args.args
            assert 42 in args
            assert "bob" in args
            assert "Bob" in args


# ── get_user_id_by_username ──────────────────────────────

class TestGetUserIdByUsername:
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        with patch("database._fetchval", new_callable=AsyncMock, return_value=None):
            result = await database.get_user_id_by_username("unknown")
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_user_id_when_found(self):
        with patch("database._fetchval", new_callable=AsyncMock, return_value=777):
            result = await database.get_user_id_by_username("alice")
            assert result == 777
