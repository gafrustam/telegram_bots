"""
Unit tests for database.py.
All asyncpg calls are mocked — no real database needed.
"""

import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fake_pool():
    """Return a mock asyncpg pool where acquire() works as async context manager."""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchval = AsyncMock(return_value=None)

    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------

class TestIsAvailable:
    def test_returns_false_when_pool_is_none(self):
        database._pool = None
        assert database.is_available() is False

    def test_returns_true_when_pool_set(self):
        database._pool = MagicMock()
        assert database.is_available() is True
        database._pool = None  # cleanup


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

class TestLowLevelHelpers:
    @pytest.mark.asyncio
    async def test_execute_returns_empty_when_no_pool(self):
        database._pool = None
        result = await database._execute("SELECT 1")
        assert result == ""

    @pytest.mark.asyncio
    async def test_fetchrow_returns_none_when_no_pool(self):
        database._pool = None
        result = await database._fetchrow("SELECT 1")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_returns_empty_when_no_pool(self):
        database._pool = None
        result = await database._fetch("SELECT 1")
        assert result == []

    @pytest.mark.asyncio
    async def test_fetchval_returns_none_when_no_pool(self):
        database._pool = None
        result = await database._fetchval("SELECT 1")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_calls_pool(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.execute = AsyncMock(return_value="INSERT 0 1")
        result = await database._execute("INSERT INTO users VALUES ($1)", 42)
        conn.execute.assert_called_once_with("INSERT INTO users VALUES ($1)", 42)
        assert result == "INSERT 0 1"
        database._pool = None

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.execute = AsyncMock(side_effect=Exception("DB error"))
        result = await database._execute("BAD SQL")
        assert result == ""
        database._pool = None


# ---------------------------------------------------------------------------
# upsert_user
# ---------------------------------------------------------------------------

class TestUpsertUser:
    @pytest.mark.asyncio
    async def test_upsert_user_calls_execute(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        await database.upsert_user(12345, "testuser", "Иван")
        assert conn.execute.called
        call_args = conn.execute.call_args[0]
        # Verify it's an INSERT ... ON CONFLICT query
        assert "INSERT INTO users" in call_args[0]
        assert call_args[1] == 12345
        assert call_args[2] == "testuser"
        assert call_args[3] == "Иван"
        database._pool = None

    @pytest.mark.asyncio
    async def test_upsert_user_handles_none_username(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        # Should not raise
        await database.upsert_user(99, None, None)
        assert conn.execute.called
        database._pool = None


# ---------------------------------------------------------------------------
# get_random_task
# ---------------------------------------------------------------------------

class TestGetRandomTask:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_tasks(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetchrow = AsyncMock(return_value=None)
        result = await database.get_random_task(4, 1)
        assert result is None
        database._pool = None

    @pytest.mark.asyncio
    async def test_returns_dict_when_task_found(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        fake_row = {
            "id": 1, "grade": 4, "task_num": 1, "topic": "Вычисления",
            "task_text": "Найди 2+2", "correct_answer": "4", "solution": "2+2=4",
            "has_image": False, "image_url": None, "image_file_id": None,
        }
        conn.fetchrow = AsyncMock(return_value=fake_row)
        result = await database.get_random_task(4, 1)
        assert result is not None
        assert result["task_num"] == 1
        assert result["correct_answer"] == "4"
        database._pool = None

    @pytest.mark.asyncio
    async def test_uses_exclusion_list(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        # First call (with exclusion) returns None; fallback returns row
        fake_row = {
            "id": 2, "grade": 4, "task_num": 1, "topic": "Вычисления",
            "task_text": "Найди 3+3", "correct_answer": "6", "solution": "3+3=6",
            "has_image": False, "image_url": None, "image_file_id": None,
        }
        conn.fetchrow = AsyncMock(side_effect=[None, fake_row])
        result = await database.get_random_task(4, 1, exclude_ids=[1])
        # Should have been called twice (exclusion + fallback)
        assert conn.fetchrow.call_count == 2
        assert result["id"] == 2
        database._pool = None

    @pytest.mark.asyncio
    async def test_no_extra_query_without_exclusion(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetchrow = AsyncMock(return_value=None)
        result = await database.get_random_task(4, 1, exclude_ids=[])
        # exclude_ids=[] means no exclusion, so only 1 query (fallback path)
        assert conn.fetchrow.call_count == 1
        database._pool = None


# ---------------------------------------------------------------------------
# count_tasks
# ---------------------------------------------------------------------------

class TestCountTasks:
    @pytest.mark.asyncio
    async def test_returns_zero_when_no_pool(self):
        database._pool = None
        result = await database.count_tasks(4, 1)
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_count(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetchval = AsyncMock(return_value=5)
        result = await database.count_tasks(4, 1)
        assert result == 5
        database._pool = None


# ---------------------------------------------------------------------------
# save_task_attempt
# ---------------------------------------------------------------------------

class TestSaveTaskAttempt:
    @pytest.mark.asyncio
    async def test_saves_correct_attempt(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        await database.save_task_attempt(
            user_id=1, grade=4, task_num=1, task_topic="Вычисления",
            task_text="2+2", correct_answer="4", user_answer="4",
            is_correct=True, points_earned=2, points_max=2,
        )
        assert conn.execute.called
        call_args = conn.execute.call_args[0]
        assert "INSERT INTO task_attempts" in call_args[0]
        # Verify params
        assert 1 in call_args  # user_id
        assert 4 in call_args  # grade
        assert True in call_args  # is_correct
        database._pool = None

    @pytest.mark.asyncio
    async def test_saves_incorrect_attempt(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        await database.save_task_attempt(
            user_id=2, grade=5, task_num=3, task_topic="Дроби",
            task_text="1/2 + 1/3 = ?", correct_answer="5/6",
            user_answer="2/3", is_correct=False, points_earned=0, points_max=2,
        )
        assert conn.execute.called
        call_args = conn.execute.call_args[0]
        assert False in call_args  # is_correct=False
        assert 0 in call_args  # points_earned=0
        database._pool = None


# ---------------------------------------------------------------------------
# get_task_stats
# ---------------------------------------------------------------------------

class TestGetTaskStats:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_data(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetch = AsyncMock(return_value=[])
        result = await database.get_task_stats(1, 4)
        assert result == []
        database._pool = None

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        fake_rows = [
            {"task_num": 1, "task_topic": "Вычисления",
             "total": 10, "correct": 7, "pts_earned": 14, "pts_max": 20},
            {"task_num": 2, "task_topic": "Порядок действий",
             "total": 5, "correct": 3, "pts_earned": 6, "pts_max": 10},
        ]
        conn.fetch = AsyncMock(return_value=fake_rows)
        result = await database.get_task_stats(1, 4)
        assert len(result) == 2
        assert result[0]["task_num"] == 1
        assert result[1]["correct"] == 3
        database._pool = None


# ---------------------------------------------------------------------------
# create_test_session
# ---------------------------------------------------------------------------

class TestCreateTestSession:
    @pytest.mark.asyncio
    async def test_returns_session_id(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetchval = AsyncMock(return_value=42)
        result = await database.create_test_session(user_id=1, grade=4, mode="timed")
        assert result == 42
        database._pool = None

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetchval = AsyncMock(return_value=1)
        await database.create_test_session(user_id=999, grade=6, mode="practice")
        call_args = conn.fetchval.call_args[0]
        assert "INSERT INTO test_sessions" in call_args[0]
        assert 999 in call_args
        assert 6 in call_args
        assert "practice" in call_args
        database._pool = None


# ---------------------------------------------------------------------------
# complete_test_session
# ---------------------------------------------------------------------------

class TestCompleteTestSession:
    @pytest.mark.asyncio
    async def test_updates_session(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        tasks = [{"task_num": 1, "points": 2}, {"task_num": 2, "points": 1}]
        await database.complete_test_session(
            session_id=5, total_score=18, max_score=20, grade_mark=4, tasks=tasks
        )
        assert conn.execute.called
        call_args = conn.execute.call_args[0]
        assert "UPDATE test_sessions" in call_args[0]
        assert 5 in call_args  # session_id
        assert 18 in call_args  # total_score
        assert 4 in call_args   # grade_mark
        database._pool = None

    @pytest.mark.asyncio
    async def test_tasks_serialized_as_json(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        tasks = [{"task_num": 1, "user_answer": "42", "points": 2}]
        await database.complete_test_session(
            session_id=1, total_score=2, max_score=2, grade_mark=5, tasks=tasks
        )
        call_args = conn.execute.call_args[0]
        # The 4th positional arg should be a JSON string
        json_arg = call_args[4]
        assert isinstance(json_arg, str)
        parsed = json.loads(json_arg)
        assert parsed[0]["task_num"] == 1
        assert parsed[0]["user_answer"] == "42"
        database._pool = None


# ---------------------------------------------------------------------------
# get_test_history
# ---------------------------------------------------------------------------

class TestGetTestHistory:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_history(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetch = AsyncMock(return_value=[])
        result = await database.get_test_history(user_id=1)
        assert result == []
        database._pool = None

    @pytest.mark.asyncio
    async def test_returns_list_of_sessions(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        from datetime import datetime
        fake_rows = [
            {
                "id": 10, "grade": 4, "mode": "timed",
                "started_at": datetime(2026, 2, 20, 10, 0),
                "completed_at": datetime(2026, 2, 20, 10, 45),
                "total_score": 18, "max_score": 20, "grade_mark": 4,
            }
        ]
        conn.fetch = AsyncMock(return_value=fake_rows)
        result = await database.get_test_history(user_id=1)
        assert len(result) == 1
        assert result[0]["grade"] == 4
        assert result[0]["total_score"] == 18
        database._pool = None

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetch = AsyncMock(return_value=[])
        await database.get_test_history(user_id=1, limit=5)
        call_args = conn.fetch.call_args[0]
        assert 5 in call_args  # limit
        database._pool = None


# ---------------------------------------------------------------------------
# get_test_detail
# ---------------------------------------------------------------------------

class TestGetTestDetail:
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        conn.fetchrow = AsyncMock(return_value=None)
        result = await database.get_test_detail(session_id=999)
        assert result is None
        database._pool = None

    @pytest.mark.asyncio
    async def test_parses_tasks_json(self):
        pool, conn = make_fake_pool()
        database._pool = pool
        tasks_data = [{"task_num": 1, "points": 2}, {"task_num": 2, "points": 1}]
        fake_row = {
            "id": 7, "grade": 4, "mode": "timed", "total_score": 3,
            "max_score": 4, "grade_mark": 3,
            "tasks_json": json.dumps(tasks_data, ensure_ascii=False),
        }
        conn.fetchrow = AsyncMock(return_value=fake_row)
        result = await database.get_test_detail(session_id=7)
        assert result is not None
        assert "tasks" in result
        assert len(result["tasks"]) == 2
        assert result["tasks"][0]["task_num"] == 1
        database._pool = None

    @pytest.mark.asyncio
    async def test_handles_already_parsed_json(self):
        """tasks_json might come back as a list if asyncpg parses JSONB."""
        pool, conn = make_fake_pool()
        database._pool = pool
        tasks_data = [{"task_num": 1, "points": 2}]
        fake_row = {
            "id": 8, "grade": 5, "mode": "practice", "total_score": 2,
            "max_score": 2, "grade_mark": 5,
            "tasks_json": tasks_data,  # already a list (asyncpg JSONB)
        }
        conn.fetchrow = AsyncMock(return_value=fake_row)
        result = await database.get_test_detail(session_id=8)
        assert result is not None
        assert "tasks" in result
        assert result["tasks"][0]["task_num"] == 1
        database._pool = None
