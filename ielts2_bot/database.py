import json
import logging
import os
from pathlib import Path
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


# ── Pool lifecycle ───────────────────────────────────────

async def init_db() -> None:
    global _pool
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        logger.warning("DATABASE_URL not set — running without database")
        return
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10, command_timeout=15)
    async with _pool.acquire() as conn:
        await conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    logger.info("Database initialized")


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def is_available() -> bool:
    return _pool is not None


# ── Low-level helpers ────────────────────────────────────

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


# ── Users ────────────────────────────────────────────────

async def upsert_user(
    user_id: int, username: str | None, first_name: str, last_name: str | None,
) -> None:
    await _execute(
        """
        INSERT INTO users (id, username, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE SET
            username    = EXCLUDED.username,
            first_name  = EXCLUDED.first_name,
            last_name   = EXCLUDED.last_name,
            last_active = now()
        """,
        user_id, username, first_name, last_name,
    )


async def get_user_id_by_username(username: str) -> int | None:
    return await _fetchval(
        "SELECT id FROM users WHERE lower(username) = lower($1)",
        username,
    )


# ── Section taps (analytics) ────────────────────────────

async def log_section_tap(user_id: int, section: str) -> None:
    await _execute(
        "INSERT INTO section_taps (user_id, section) VALUES ($1, $2)",
        user_id, section,
    )


# ── Topic bank ───────────────────────────────────────────

async def get_random_topic(part: int, user_id: int) -> dict | None:
    used = await _fetch(
        """
        SELECT DISTINCT topic FROM generated_topics
        WHERE user_id = $1 AND part = $2 AND accepted = TRUE
        """,
        user_id, part,
    )
    used_topics = {r["topic"] for r in used}

    rows = await _fetch(
        "SELECT id, part, topic, weight, cue_card, questions FROM topic_bank WHERE part = $1",
        part,
    )
    if not rows:
        return None

    available = [r for r in rows if r["topic"] not in used_topics] or list(rows)

    import random
    weights = [float(r["weight"]) for r in available]
    return dict(random.choices(available, weights=weights, k=1)[0])


async def get_last_part2_topic(user_id: int) -> str | None:
    return await _fetchval(
        """
        SELECT topic FROM sessions
        WHERE user_id = $1 AND part = 2 AND status = 'completed'
        ORDER BY completed_at DESC LIMIT 1
        """,
        user_id,
    )


# ── Generated topics ─────────────────────────────────────

async def save_generated_topic(
    user_id: int, part: int, topic: str,
    questions: list[str] | None, cue_card: str | None,
) -> int | None:
    if not _pool:
        return None
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO generated_topics (user_id, part, topic, questions, cue_card)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                RETURNING id
                """,
                user_id, part, topic,
                json.dumps(questions) if questions else None,
                cue_card,
            )
    except Exception:
        logger.exception("DB save_generated_topic error")
        return None


async def mark_topic_accepted(topic_id: int | None) -> None:
    if topic_id is None:
        return
    await _execute("UPDATE generated_topics SET accepted = TRUE WHERE id = $1", topic_id)


# ── Sessions ─────────────────────────────────────────────

async def create_session(
    user_id: int, part: int, topic: str,
    questions: list[str] | None, cue_card: str | None,
    topic_id: int | None = None,
) -> int | None:
    if not _pool:
        return None
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO sessions (user_id, part, topic, questions, cue_card, topic_id)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                RETURNING id
                """,
                user_id, part, topic,
                json.dumps(questions) if questions else None,
                cue_card, topic_id,
            )
    except Exception:
        logger.exception("DB create_session error")
        return None


async def complete_session(session_id: int | None, audio_duration_total: float) -> None:
    if session_id is None:
        return
    await _execute(
        """
        UPDATE sessions
        SET status = 'completed', completed_at = now(), audio_duration_total = $2
        WHERE id = $1
        """,
        session_id, audio_duration_total,
    )


async def fail_session(session_id: int | None) -> None:
    if session_id is None:
        return
    await _execute(
        "UPDATE sessions SET status = 'failed', completed_at = now() WHERE id = $1",
        session_id,
    )


# ── Assessments ──────────────────────────────────────────

async def save_assessment(session_id: int | None, user_id: int, result: dict) -> None:
    if session_id is None:
        return
    await _execute(
        """
        INSERT INTO assessments
            (session_id, user_id, overall_band,
             fluency_coherence, lexical_resource,
             grammatical_range_accuracy, pronunciation, raw_result)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        """,
        session_id, user_id,
        float(result.get("overall_band", 0)),
        float(result.get("fluency_coherence", {}).get("band", 0)),
        float(result.get("lexical_resource", {}).get("band", 0)),
        float(result.get("grammatical_range_accuracy", {}).get("band", 0)),
        float(result.get("pronunciation", {}).get("band", 0)),
        json.dumps(result),
    )


# ── User stats ───────────────────────────────────────────

async def get_user_stats(user_id: int) -> dict:
    row = await _fetchrow(
        """
        SELECT
            count(*) FILTER (WHERE status = 'completed')          AS completed_sessions,
            count(*)                                               AS total_sessions,
            count(*) FILTER (WHERE status='completed' AND part=1) AS part1_count,
            count(*) FILTER (WHERE status='completed' AND part=2) AS part2_count,
            count(*) FILTER (WHERE status='completed' AND part=3) AS part3_count,
            max(started_at)                                        AS last_session
        FROM sessions WHERE user_id = $1
        """,
        user_id,
    )
    stats = dict(row) if row else {}

    a_row = await _fetchrow(
        """
        SELECT
            round(avg(a.overall_band)::numeric, 1)                                      AS avg_band,
            max(a.overall_band)                                                          AS best_band,
            round(avg(a.overall_band) FILTER (WHERE s.part=1)::numeric, 1)              AS avg_band_p1,
            round(avg(a.overall_band) FILTER (WHERE s.part=2)::numeric, 1)              AS avg_band_p2,
            round(avg(a.overall_band) FILTER (WHERE s.part=3)::numeric, 1)              AS avg_band_p3
        FROM assessments a
        JOIN sessions s ON s.id = a.session_id
        WHERE a.user_id = $1
        """,
        user_id,
    )
    if a_row:
        stats.update(dict(a_row))

    return stats


# ── Admin stats ──────────────────────────────────────────

async def get_admin_stats() -> dict:
    row = await _fetchrow(
        """
        SELECT
            count(*) FILTER (WHERE created_at > now() - interval '1 day')   AS new_1d,
            count(*) FILTER (WHERE created_at > now() - interval '7 days')  AS new_7d,
            count(*) FILTER (WHERE created_at > now() - interval '30 days') AS new_30d,
            count(*)                                                          AS total_users
        FROM users
        """,
    )
    stats = dict(row) if row else {}

    row2 = await _fetchrow(
        """
        SELECT
            count(DISTINCT user_id) FILTER (WHERE started_at > now() - interval '1 day')   AS active_1d,
            count(DISTINCT user_id) FILTER (WHERE started_at > now() - interval '7 days')  AS active_7d,
            count(DISTINCT user_id) FILTER (WHERE started_at > now() - interval '30 days') AS active_30d,
            count(*) FILTER (WHERE status='completed' AND started_at > now() - interval '1 day')   AS sessions_1d,
            count(*) FILTER (WHERE status='completed' AND started_at > now() - interval '7 days')  AS sessions_7d,
            count(*) FILTER (WHERE status='completed' AND started_at > now() - interval '30 days') AS sessions_30d
        FROM sessions
        """,
    )
    if row2:
        stats.update(dict(row2))

    a_row = await _fetchrow(
        """
        SELECT
            round(avg(overall_band)::numeric, 1) AS avg_band_30d,
            count(*)                             AS total_assessments_30d
        FROM assessments
        WHERE created_at > now() - interval '30 days'
        """,
    )
    if a_row:
        stats.update(dict(a_row))

    taps = await _fetch(
        """
        SELECT section, count(*) AS cnt
        FROM section_taps
        WHERE tapped_at > now() - interval '7 days'
        GROUP BY section ORDER BY cnt DESC
        """,
    )
    stats["section_taps_7d"] = {r["section"]: r["cnt"] for r in taps}

    return stats
