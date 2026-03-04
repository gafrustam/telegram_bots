"""Async PostgreSQL persistence for question history."""

import json
import logging
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)
_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool
    dsn = os.environ["DATABASE_URL"]
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10, command_timeout=15)
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id       SERIAL PRIMARY KEY,
                level    INTEGER NOT NULL,
                question TEXT NOT NULL,
                options  TEXT NOT NULL,
                correct  TEXT NOT NULL,
                ts       TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_level ON questions (level)"
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    BIGINT PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_visit TIMESTAMPTZ DEFAULT NOW()
            )
        """)


def _pool_get() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


async def upsert_user(user_id: int, username: str | None, first_name: str) -> None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_visit = NOW()
            """,
            user_id, username, first_name,
        )


async def save_question(
    level: int, question: str, options: dict, correct: str
) -> None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO questions (level, question, options, correct) VALUES ($1, $2, $3, $4)",
            level, question, json.dumps(options, ensure_ascii=False), correct,
        )


def _tier_bounds(level: int) -> tuple[int, int]:
    """Return (lo, hi) inclusive bounds for the difficulty tier."""
    if level <= 5:
        return (1, 5)
    elif level <= 10:
        return (6, 10)
    return (11, 99)


async def get_recent_questions(level: int, limit: int = 40) -> list[str]:
    """Return recent question texts within the same difficulty tier."""
    lo, hi = _tier_bounds(level)
    pool = _pool_get()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT question FROM questions WHERE level >= $1 AND level <= $2 "
            "ORDER BY ts DESC LIMIT $3",
            lo, hi, limit,
        )
    return [r["question"] for r in rows]


async def question_count() -> int:
    pool = _pool_get()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS cnt FROM questions")
    return row["cnt"] if row else 0
