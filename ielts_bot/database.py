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


# ── Topic bank operations ──────────────────────────────

async def get_random_topic(part: int, user_id: int) -> dict | None:
    """Pick a weighted-random topic from the bank, avoiding recently used ones."""
    # Get topics this user has already used (by topic name)
    used = await _fetch(
        """
        SELECT DISTINCT topic FROM generated_topics
        WHERE user_id = $1 AND part = $2 AND accepted = TRUE
        """,
        user_id, part,
    )
    used_topics = {r["topic"] for r in used}

    # Get all bank topics for this part
    rows = await _fetch(
        "SELECT id, part, topic, weight, cue_card, questions FROM topic_bank WHERE part = $1",
        part,
    )
    if not rows:
        return None

    # Filter out used topics; if all used, reset (allow all)
    available = [r for r in rows if r["topic"] not in used_topics]
    if not available:
        available = list(rows)

    # Weighted random selection
    import random
    weights = [float(r["weight"]) for r in available]
    chosen = random.choices(available, weights=weights, k=1)[0]
    return dict(chosen)


async def get_last_part2_topic(user_id: int) -> str | None:
    """Get the topic of the user's most recent completed Part 2 session."""
    return await _fetchval(
        """
        SELECT s.topic FROM sessions s
        WHERE s.user_id = $1 AND s.part = 2 AND s.status = 'completed'
        ORDER BY s.completed_at DESC
        LIMIT 1
        """,
        user_id,
    )


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


# ── Generated topics ───────────────────────────────────

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
    await _execute(
        "UPDATE generated_topics SET accepted = TRUE WHERE id = $1",
        topic_id,
    )


# ── Session operations ──────────────────────────────────

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
                cue_card,
                topic_id,
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


# ── Assessment operations ───────────────────────────────

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
        session_id,
        user_id,
        float(result.get("overall_band", 0)),
        float(result.get("fluency_coherence", {}).get("band", 0)),
        float(result.get("lexical_resource", {}).get("band", 0)),
        float(result.get("grammatical_range_accuracy", {}).get("band", 0)),
        float(result.get("pronunciation", {}).get("band", 0)),
        json.dumps(result),
    )


# ── User stats queries ──────────────────────────────────

async def get_user_stats(user_id: int) -> dict | None:
    row = await _fetchrow(
        """
        SELECT
            count(*)                                              AS total_sessions,
            count(*) FILTER (WHERE s.status = 'completed')        AS completed,
            round(avg(a.overall_band)::numeric, 1)                AS avg_overall,
            round(avg(a.fluency_coherence)::numeric, 1)           AS avg_fc,
            round(avg(a.lexical_resource)::numeric, 1)            AS avg_lr,
            round(avg(a.grammatical_range_accuracy)::numeric, 1)  AS avg_gra,
            round(avg(a.pronunciation)::numeric, 1)               AS avg_pron,
            max(a.overall_band)                                   AS best_overall,
            round(avg(a.overall_band) FILTER
                (WHERE a.created_at > now() - interval '7 days')::numeric, 1) AS avg_7d,
            count(*) FILTER
                (WHERE a.created_at > now() - interval '7 days')  AS sessions_7d,
            count(*) FILTER (WHERE s.part = 1 AND s.status = 'completed') AS part1_count,
            count(*) FILTER (WHERE s.part = 2 AND s.status = 'completed') AS part2_count,
            count(*) FILTER (WHERE s.part = 3 AND s.status = 'completed') AS part3_count,
            round(avg(a.overall_band) FILTER (WHERE s.part = 1)::numeric, 1) AS avg_part1,
            round(avg(a.overall_band) FILTER (WHERE s.part = 2)::numeric, 1) AS avg_part2,
            round(avg(a.overall_band) FILTER (WHERE s.part = 3)::numeric, 1) AS avg_part3
        FROM sessions s
        LEFT JOIN assessments a ON a.session_id = s.id
        WHERE s.user_id = $1
        """,
        user_id,
    )
    if not row or row["total_sessions"] == 0:
        return None
    return dict(row)


async def get_user_recent_assessments(user_id: int, limit: int = 5) -> list[dict]:
    rows = await _fetch(
        """
        SELECT s.part, s.topic, a.overall_band, a.created_at
        FROM assessments a
        JOIN sessions s ON s.id = a.session_id
        WHERE a.user_id = $1
        ORDER BY a.created_at DESC
        LIMIT $2
        """,
        user_id, limit,
    )
    return [dict(r) for r in rows]


async def get_user_id_by_username(username: str) -> int | None:
    return await _fetchval(
        "SELECT id FROM users WHERE lower(username) = lower($1)",
        username,
    )


# ── Admin queries ───────────────────────────────────────

async def get_admin_summary_stats() -> dict:
    """Return new/active/completed users, sessions, minutes for 3d/7d/30d windows."""
    row = await _fetchrow(
        """
        SELECT
            count(*) FILTER (WHERE u.created_at > now() - interval '3 days')  AS new_3d,
            count(*) FILTER (WHERE u.created_at > now() - interval '7 days')  AS new_7d,
            count(*) FILTER (WHERE u.created_at > now() - interval '30 days') AS new_30d,
            count(*)                                                           AS total_users
        FROM users u
        """
    )
    stats = dict(row) if row else {}

    row2 = await _fetchrow(
        """
        SELECT
            count(DISTINCT user_id) FILTER (WHERE started_at > now() - interval '3 days')  AS active_3d,
            count(DISTINCT user_id) FILTER (WHERE started_at > now() - interval '7 days')  AS active_7d,
            count(DISTINCT user_id) FILTER (WHERE started_at > now() - interval '30 days') AS active_30d,

            count(DISTINCT user_id) FILTER (WHERE status='completed' AND started_at > now() - interval '3 days')  AS completed_users_3d,
            count(DISTINCT user_id) FILTER (WHERE status='completed' AND started_at > now() - interval '7 days')  AS completed_users_7d,
            count(DISTINCT user_id) FILTER (WHERE status='completed' AND started_at > now() - interval '30 days') AS completed_users_30d,

            count(*) FILTER (WHERE started_at > now() - interval '3 days')  AS sessions_3d,
            count(*) FILTER (WHERE started_at > now() - interval '7 days')  AS sessions_7d,
            count(*) FILTER (WHERE started_at > now() - interval '30 days') AS sessions_30d,

            round(coalesce(sum(audio_duration_total) FILTER (WHERE status='completed' AND started_at > now() - interval '3 days'), 0) / 60.0, 1) AS minutes_3d,
            round(coalesce(sum(audio_duration_total) FILTER (WHERE status='completed' AND started_at > now() - interval '7 days'), 0) / 60.0, 1) AS minutes_7d,
            round(coalesce(sum(audio_duration_total) FILTER (WHERE status='completed' AND started_at > now() - interval '30 days'), 0) / 60.0, 1) AS minutes_30d
        FROM sessions
        """
    )
    if row2:
        stats.update(dict(row2))
    return stats


async def get_admin_retention() -> dict:
    """Return D1/D3/D7/D14/D30 retention rates."""
    row = await _fetchrow(
        """
        WITH first_seen AS (
            SELECT user_id, min(started_at::date) AS first_day
            FROM sessions GROUP BY user_id
        ),
        cohort AS (
            SELECT fs.user_id, fs.first_day
            FROM first_seen fs
            WHERE fs.first_day <= now()::date - 1
        )
        SELECT
            count(DISTINCT c.user_id) AS cohort_size,
            count(DISTINCT c.user_id) FILTER (WHERE EXISTS (
                SELECT 1 FROM sessions s WHERE s.user_id = c.user_id
                  AND s.started_at::date >= c.first_day + 1
            )) AS ret_d1,
            count(DISTINCT c.user_id) FILTER (WHERE EXISTS (
                SELECT 1 FROM sessions s WHERE s.user_id = c.user_id
                  AND s.started_at::date >= c.first_day + 3
            )) AS ret_d3,
            count(DISTINCT c.user_id) FILTER (WHERE EXISTS (
                SELECT 1 FROM sessions s WHERE s.user_id = c.user_id
                  AND s.started_at::date >= c.first_day + 7
            )) AS ret_d7,
            count(DISTINCT c.user_id) FILTER (WHERE EXISTS (
                SELECT 1 FROM sessions s WHERE s.user_id = c.user_id
                  AND s.started_at::date >= c.first_day + 14
            )) AS ret_d14,
            count(DISTINCT c.user_id) FILTER (WHERE EXISTS (
                SELECT 1 FROM sessions s WHERE s.user_id = c.user_id
                  AND s.started_at::date >= c.first_day + 30
            )) AS ret_d30
        FROM cohort c
        """
    )
    return dict(row) if row else {}
