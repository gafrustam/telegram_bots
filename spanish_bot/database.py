import json
import logging
import os
from pathlib import Path
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


# ── Pool lifecycle ──────────────────────────────────────

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


# ── Low-level helpers ───────────────────────────────────

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


# ── User operations ─────────────────────────────────────

async def upsert_user(
    user_id: int, username: str | None, first_name: str, last_name: str | None,
) -> None:
    await _execute(
        """
        INSERT INTO users (id, username, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE SET
            username   = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name  = EXCLUDED.last_name,
            last_active = now()
        """,
        user_id, username, first_name, last_name,
    )


async def get_user_level(user_id: int) -> int:
    val = await _fetchval(
        "SELECT difficulty_level FROM users WHERE id = $1", user_id,
    )
    return val if val is not None else 3


async def set_user_level(user_id: int, level: int) -> None:
    await _execute(
        "UPDATE users SET difficulty_level = $1 WHERE id = $2",
        level, user_id,
    )


# ── Conversation operations ─────────────────────────────

async def create_conversation(
    user_id: int, level: int, topic: str, scenario: str | None,
) -> int | None:
    if not _pool:
        return None
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO conversations (user_id, difficulty_level, scenario_topic, scenario_text)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                user_id, level, topic, scenario,
            )
    except Exception:
        logger.exception("DB create_conversation error")
        return None


async def save_message(
    conversation_id: int | None, role: str, text: str | None,
    audio_file_id: str | None, seq_num: int,
) -> None:
    if conversation_id is None:
        return
    await _execute(
        """
        INSERT INTO messages (conversation_id, role, text_content, audio_file_id, sequence_num)
        VALUES ($1, $2, $3, $4, $5)
        """,
        conversation_id, role, text, audio_file_id, seq_num,
    )


async def complete_conversation(conversation_id: int | None, exchange_count: int) -> None:
    if conversation_id is None:
        return
    await _execute(
        """
        UPDATE conversations
        SET status = 'completed', completed_at = now(), exchange_count = $2
        WHERE id = $1
        """,
        conversation_id, exchange_count,
    )


async def fail_conversation(conversation_id: int | None) -> None:
    if conversation_id is None:
        return
    await _execute(
        "UPDATE conversations SET status = 'failed', completed_at = now() WHERE id = $1",
        conversation_id,
    )


# ── Assessment operations ───────────────────────────────

async def save_assessment(
    conversation_id: int | None, user_id: int, result: dict,
) -> None:
    if conversation_id is None:
        return
    await _execute(
        """
        INSERT INTO assessments
            (conversation_id, user_id, overall_score,
             vocab_use, grammar, fluency, comprehension, pronunciation,
             feedback_text, raw_result)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
        """,
        conversation_id,
        user_id,
        float(result.get("overall_score", 0)),
        float(result.get("vocab_use", {}).get("score", 0)),
        float(result.get("grammar", {}).get("score", 0)),
        float(result.get("fluency", {}).get("score", 0)),
        float(result.get("comprehension", {}).get("score", 0)),
        float(result.get("pronunciation", {}).get("score", 0)),
        result.get("feedback_text", ""),
        json.dumps(result),
    )


# ── Vocabulary operations ───────────────────────────────

async def save_vocabulary(
    user_id: int, conversation_id: int | None, words: list[dict],
) -> None:
    if not _pool or not words:
        return
    try:
        async with _pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO vocabulary (user_id, conversation_id, spanish_word, english_word, example)
                VALUES ($1, $2, $3, $4, $5)
                """,
                [
                    (
                        user_id, conversation_id,
                        w.get("spanish", ""), w.get("english", ""),
                        w.get("example"),
                    )
                    for w in words
                ],
            )
    except Exception:
        logger.exception("DB save_vocabulary error")


# ── Stats ───────────────────────────────────────────────

async def get_user_stats(user_id: int) -> dict | None:
    row = await _fetchrow(
        """
        SELECT
            count(*)                                             AS total_conversations,
            count(*) FILTER (WHERE c.status = 'completed')       AS completed,
            round(avg(a.overall_score)::numeric, 1)              AS avg_score,
            max(a.overall_score)                                 AS best_score,
            round(avg(a.vocab_use)::numeric, 1)                  AS avg_vocab,
            round(avg(a.grammar)::numeric, 1)                    AS avg_grammar,
            round(avg(a.fluency)::numeric, 1)                    AS avg_fluency,
            round(avg(a.comprehension)::numeric, 1)              AS avg_comprehension,
            round(avg(a.pronunciation)::numeric, 1)              AS avg_pronunciation,
            round(avg(a.overall_score) FILTER
                (WHERE a.created_at > now() - interval '7 days')::numeric, 1) AS avg_7d,
            count(*) FILTER
                (WHERE a.created_at > now() - interval '7 days') AS sessions_7d
        FROM conversations c
        LEFT JOIN assessments a ON a.conversation_id = c.id
        WHERE c.user_id = $1
        """,
        user_id,
    )
    if not row or row["total_conversations"] == 0:
        return None
    return dict(row)


async def get_user_recent_assessments(user_id: int, limit: int = 5) -> list[dict]:
    rows = await _fetch(
        """
        SELECT c.scenario_topic, c.difficulty_level, a.overall_score, a.created_at
        FROM assessments a
        JOIN conversations c ON c.id = a.conversation_id
        WHERE a.user_id = $1
        ORDER BY a.created_at DESC
        LIMIT $2
        """,
        user_id, limit,
    )
    return [dict(r) for r in rows]
