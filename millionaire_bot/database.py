"""Async SQLite persistence for question history."""

import json
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "millionaire.db"

_CREATE = """
CREATE TABLE IF NOT EXISTS questions (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    level    INTEGER NOT NULL,
    question TEXT    NOT NULL,
    options  TEXT    NOT NULL,
    correct  TEXT    NOT NULL,
    ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# Index for fast lookups by level
_CREATE_IDX = "CREATE INDEX IF NOT EXISTS idx_level ON questions (level)"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE)
        await db.execute(_CREATE_IDX)
        await db.commit()


async def save_question(
    level: int, question: str, options: dict, correct: str
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO questions (level, question, options, correct) VALUES (?, ?, ?, ?)",
            (level, question, json.dumps(options, ensure_ascii=False), correct),
        )
        await db.commit()


def _tier_filter(level: int) -> str:
    """Return WHERE clause for the difficulty tier of a given level."""
    if level <= 5:
        return "level <= 5"
    elif level <= 10:
        return "level BETWEEN 6 AND 10"
    return "level > 10"


async def get_recent_questions(level: int, limit: int = 40) -> list[str]:
    """Return recent question texts within the same difficulty tier."""
    where = _tier_filter(level)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT question FROM questions WHERE {where} ORDER BY ts DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]


async def question_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM questions") as cur:
            row = await cur.fetchone()
    return row[0] if row else 0
