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

async def get_admin_dashboard(days: int = 10) -> list[dict]:
    rows = await _fetch(
        """
        SELECT
            d::date AS day,
            (SELECT count(*) FROM users
             WHERE created_at::date <= d::date) AS total_users,
            (SELECT count(*) FROM users
             WHERE created_at::date = d::date) AS new_users,
            (SELECT count(*) FROM sessions
             WHERE started_at::date = d::date
               AND status = 'completed') AS completed,
            (SELECT count(*) FROM sessions
             WHERE started_at::date = d::date
               AND status != 'completed') AS incomplete,
            (SELECT round(coalesce(sum(audio_duration_total), 0) / 60.0, 1)
             FROM sessions
             WHERE started_at::date = d::date
               AND status = 'completed') AS total_minutes,
            (SELECT count(DISTINCT user_id) FROM sessions
             WHERE started_at::date = d::date) AS active_users,
            (SELECT count(DISTINCT s1.user_id)
             FROM sessions s1
             WHERE s1.started_at::date = d::date
               AND EXISTS (
                   SELECT 1 FROM sessions s2
                   WHERE s2.user_id = s1.user_id
                     AND s2.started_at::date = d::date + 1
               )
            ) AS ret_d1,
            (SELECT count(DISTINCT s1.user_id)
             FROM sessions s1
             WHERE s1.started_at::date = d::date
               AND EXISTS (
                   SELECT 1 FROM sessions s2
                   WHERE s2.user_id = s1.user_id
                     AND s2.started_at::date BETWEEN d::date + 1 AND d::date + 3
               )
            ) AS ret_d3,
            (SELECT count(DISTINCT s1.user_id)
             FROM sessions s1
             WHERE s1.started_at::date = d::date
               AND EXISTS (
                   SELECT 1 FROM sessions s2
                   WHERE s2.user_id = s1.user_id
                     AND s2.started_at::date BETWEEN d::date + 1 AND d::date + 7
               )
            ) AS ret_d7
        FROM generate_series(
            (now() - make_interval(days => $1))::date,
            now()::date,
            '1 day'::interval
        ) d
        ORDER BY d::date
        """,
        days,
    )
    return [dict(r) for r in rows]


async def get_admin_user_score_distribution() -> list[dict]:
    rows = await _fetch(
        """
        SELECT
            (floor(avg_band * 2) / 2)::numeric AS band_bucket,
            count(*) AS cnt
        FROM (
            SELECT user_id, avg(overall_band) AS avg_band
            FROM assessments
            GROUP BY user_id
        ) user_avgs
        GROUP BY band_bucket
        ORDER BY band_bucket
        """
    )
    return [dict(r) for r in rows]


async def get_admin_top_users(limit: int = 10) -> list[dict]:
    rows = await _fetch(
        """
        SELECT
            u.id, u.first_name, u.username,
            count(DISTINCT a.id) AS session_count,
            round(avg(a.overall_band)::numeric, 1) AS avg_band,
            max(a.overall_band) AS best_band,
            round(sum(s.audio_duration_total) / 60.0, 1) AS audio_min,
            max(a.created_at) AS last_session
        FROM users u
        JOIN assessments a ON a.user_id = u.id
        JOIN sessions s ON s.id = a.session_id
        GROUP BY u.id, u.first_name, u.username
        ORDER BY session_count DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(r) for r in rows]


async def get_admin_outliers() -> dict:
    power_users = await _fetch(
        """
        SELECT u.first_name, u.username,
               count(DISTINCT a.id) AS sessions,
               round(sum(s.audio_duration_total) / 60.0, 1) AS audio_min,
               round(avg(a.overall_band)::numeric, 1) AS avg_band
        FROM users u
        JOIN assessments a ON a.user_id = u.id
        JOIN sessions s ON s.id = a.session_id
        GROUP BY u.id, u.first_name, u.username
        HAVING count(DISTINCT a.id) >= 5
           OR sum(s.audio_duration_total) > 600
        ORDER BY count(DISTINCT a.id) DESC
        LIMIT 10
        """
    )
    top_scorers = await _fetch(
        """
        SELECT u.first_name, u.username,
               a.overall_band, s.part, s.topic, a.created_at
        FROM assessments a
        JOIN users u ON u.id = a.user_id
        JOIN sessions s ON s.id = a.session_id
        ORDER BY a.overall_band DESC
        LIMIT 5
        """
    )
    dropoffs = await _fetch(
        """
        SELECT u.first_name, u.username,
               count(*) FILTER (WHERE s.status != 'completed') AS failed,
               count(*) AS total,
               round(100.0 * count(*) FILTER (WHERE s.status != 'completed')
                     / count(*), 0) AS fail_pct
        FROM users u
        JOIN sessions s ON s.user_id = u.id
        GROUP BY u.id, u.first_name, u.username
        HAVING count(*) >= 3
           AND count(*) FILTER (WHERE s.status != 'completed') > count(*) / 2
        ORDER BY fail_pct DESC
        LIMIT 5
        """
    )
    return {
        "power_users": [dict(r) for r in power_users],
        "top_scorers": [dict(r) for r in top_scorers],
        "dropoffs": [dict(r) for r in dropoffs],
    }
