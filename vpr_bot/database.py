"""
PostgreSQL database layer for VPR Bot (asyncpg).
Tables:
  - users
  - task_attempts   (single-task training history)
  - test_sessions   (full-test history)
  - tasks           (static task bank)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


# ---------------------------------------------------------------------------
# Pool lifecycle
# ---------------------------------------------------------------------------

async def init_db() -> None:
    global _pool
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        logger.warning("DATABASE_URL not set — running without database")
        return
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10, command_timeout=15)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    async with _pool.acquire() as conn:
        await conn.execute(schema_sql)
    logger.info("Database initialized")


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def is_available() -> bool:
    return _pool is not None


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

async def _execute(query: str, *args: Any) -> str:
    if not _pool:
        return ""
    try:
        async with _pool.acquire() as conn:
            return await conn.execute(query, *args)
    except Exception:
        logger.exception("DB execute error")
        return ""


async def _fetchrow(query: str, *args: Any) -> asyncpg.Record | None:
    if not _pool:
        return None
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    except Exception:
        logger.exception("DB fetchrow error")
        return None


async def _fetch(query: str, *args: Any) -> list[asyncpg.Record]:
    if not _pool:
        return []
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch(query, *args)
    except Exception:
        logger.exception("DB fetch error")
        return []


async def _fetchval(query: str, *args: Any) -> Any:
    if not _pool:
        return None
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    except Exception:
        logger.exception("DB fetchval error")
        return None


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    await _execute(
        """
        INSERT INTO users (user_id, username, first_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET
            username   = EXCLUDED.username,
            first_name = EXCLUDED.first_name
        """,
        user_id, username, first_name,
    )


# ---------------------------------------------------------------------------
# Task bank (static pre-made tasks)
# ---------------------------------------------------------------------------

async def get_random_task(grade: int, task_num: int, exclude_ids: list[int] | None = None) -> Optional[dict]:
    """
    Return a random task for the given grade/task_num.
    Optionally exclude already-seen task IDs.
    If all tasks are excluded, ignore the exclusion list (reset).
    """
    excl = exclude_ids or []

    # Try to get a task not yet seen
    if excl:
        row = await _fetchrow(
            """
            SELECT id, grade, task_num, topic, task_text, correct_answer, solution,
                   has_image, image_url, image_file_id
            FROM tasks
            WHERE grade = $1 AND task_num = $2 AND id != ALL($3)
            ORDER BY RANDOM()
            LIMIT 1
            """,
            grade, task_num, excl,
        )
    else:
        row = None

    # Fallback: get any task (reset seen list)
    if row is None:
        row = await _fetchrow(
            """
            SELECT id, grade, task_num, topic, task_text, correct_answer, solution,
                   has_image, image_url, image_file_id
            FROM tasks
            WHERE grade = $1 AND task_num = $2
            ORDER BY RANDOM()
            LIMIT 1
            """,
            grade, task_num,
        )

    return dict(row) if row else None


async def count_tasks(grade: int, task_num: int) -> int:
    """Count available tasks for a grade/task_num combination."""
    val = await _fetchval(
        "SELECT COUNT(*) FROM tasks WHERE grade = $1 AND task_num = $2",
        grade, task_num,
    )
    return int(val) if val else 0


async def update_task_image_file_id(task_id: int, file_id: str) -> None:
    """Cache Telegram file_id after first send."""
    await _execute(
        "UPDATE tasks SET image_file_id = $1 WHERE id = $2",
        file_id, task_id,
    )


# ---------------------------------------------------------------------------
# Task attempts (training mode)
# ---------------------------------------------------------------------------

async def save_task_attempt(
    user_id: int,
    grade: int,
    task_num: int,
    task_topic: str,
    task_text: str,
    correct_answer: str,
    user_answer: str,
    is_correct: bool,
    points_earned: int,
    points_max: int,
) -> None:
    await _execute(
        """
        INSERT INTO task_attempts
            (user_id, grade, task_num, task_topic, task_text,
             correct_answer, user_answer, is_correct, points_earned, points_max)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        user_id, grade, task_num, task_topic, task_text,
        correct_answer, user_answer, is_correct,
        points_earned, points_max,
    )


async def get_task_stats(user_id: int, grade: int) -> list[dict]:
    """Return per-task-type stats: total attempts and correct count."""
    rows = await _fetch(
        """
        SELECT task_num, task_topic,
               COUNT(*)                     AS total,
               SUM(is_correct::int)         AS correct,
               SUM(points_earned)           AS pts_earned,
               SUM(points_max)              AS pts_max
        FROM task_attempts
        WHERE user_id = $1 AND grade = $2
        GROUP BY task_num, task_topic
        ORDER BY task_num
        """,
        user_id, grade,
    )
    return [dict(r) for r in rows]


async def get_overall_task_stats(user_id: int) -> list[dict]:
    """Aggregated stats across all grades."""
    rows = await _fetch(
        """
        SELECT grade,
               COUNT(*)            AS total,
               SUM(is_correct::int) AS correct,
               SUM(points_earned)  AS pts_earned,
               SUM(points_max)     AS pts_max
        FROM task_attempts
        WHERE user_id = $1
        GROUP BY grade
        ORDER BY grade
        """,
        user_id,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Test sessions (full-test mode)
# ---------------------------------------------------------------------------

async def create_test_session(user_id: int, grade: int, mode: str) -> int:
    """Create a new test session and return its id."""
    val = await _fetchval(
        "INSERT INTO test_sessions (user_id, grade, mode) VALUES ($1, $2, $3) RETURNING id",
        user_id, grade, mode,
    )
    return int(val)


async def complete_test_session(
    session_id: int,
    total_score: int,
    max_score: int,
    grade_mark: int,
    tasks: list[dict],
) -> None:
    await _execute(
        """
        UPDATE test_sessions
        SET completed_at = NOW(),
            total_score  = $1,
            max_score    = $2,
            grade_mark   = $3,
            tasks_json   = $4
        WHERE id = $5
        """,
        total_score, max_score, grade_mark,
        json.dumps(tasks, ensure_ascii=False),
        session_id,
    )


async def get_test_history(user_id: int, limit: int = 20) -> list[dict]:
    rows = await _fetch(
        """
        SELECT id, grade, mode, started_at, completed_at,
               total_score, max_score, grade_mark
        FROM test_sessions
        WHERE user_id = $1 AND completed_at IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT $2
        """,
        user_id, limit,
    )
    return [dict(r) for r in rows]


async def get_test_detail(session_id: int) -> Optional[dict]:
    row = await _fetchrow(
        "SELECT * FROM test_sessions WHERE id = $1",
        session_id,
    )
    if row is None:
        return None
    result = dict(row)
    if result.get("tasks_json"):
        raw = result["tasks_json"]
        result["tasks"] = json.loads(raw) if isinstance(raw, str) else raw
    return result
