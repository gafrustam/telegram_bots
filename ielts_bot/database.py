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


# ── Session operations ──────────────────────────────────

async def create_session(
    user_id: int, part: int, topic: str,
    questions: list[str] | None, cue_card: str | None,
) -> int | None:
    if not _pool:
        return None
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO sessions (user_id, part, topic, questions, cue_card)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                RETURNING id
                """,
                user_id, part, topic,
                json.dumps(questions) if questions else None,
                cue_card,
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
            count(*) FILTER (WHERE s.part = 3 AND s.status = 'completed') AS part3_count
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


# ── Admin queries ───────────────────────────────────────

async def get_admin_overview() -> dict | None:
    row = await _fetchrow(
        """
        SELECT
            (SELECT count(*) FROM users)                                       AS total_users,
            (SELECT count(*) FROM users
             WHERE last_active > now() - interval '7 days')                    AS active_7d,
            (SELECT count(*) FROM users
             WHERE last_active > now() - interval '24 hours')                  AS active_24h,
            (SELECT count(*) FROM sessions)                                    AS total_sessions,
            (SELECT count(*) FROM sessions WHERE status = 'completed')         AS completed_sessions,
            (SELECT count(*) FROM assessments)                                 AS total_assessments,
            (SELECT round(avg(overall_band)::numeric, 1) FROM assessments)     AS global_avg_band
        """
    )
    return dict(row) if row else None


async def get_admin_daily_stats(days: int = 7) -> list[dict]:
    rows = await _fetch(
        """
        SELECT
            d::date                        AS day,
            count(DISTINCT s.user_id)      AS unique_users,
            count(DISTINCT s.id)           AS sessions,
            count(DISTINCT a.id)           AS assessments,
            round(avg(a.overall_band)::numeric, 1) AS avg_band
        FROM generate_series(
            (now() - make_interval(days => $1))::date,
            now()::date,
            '1 day'::interval
        ) d
        LEFT JOIN sessions s   ON s.started_at::date = d::date
        LEFT JOIN assessments a ON a.session_id = s.id
        GROUP BY d::date
        ORDER BY d::date
        """,
        days,
    )
    return [dict(r) for r in rows]


async def get_admin_top_users(limit: int = 10) -> list[dict]:
    rows = await _fetch(
        """
        SELECT
            u.id, u.first_name, u.username,
            count(a.id)                                   AS session_count,
            round(avg(a.overall_band)::numeric, 1)        AS avg_band,
            max(a.overall_band)                           AS best_band
        FROM users u
        JOIN assessments a ON a.user_id = u.id
        GROUP BY u.id, u.first_name, u.username
        ORDER BY session_count DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(r) for r in rows]


async def get_admin_part_distribution() -> list[dict]:
    rows = await _fetch(
        """
        SELECT
            s.part,
            count(*)                                      AS cnt,
            round(avg(a.overall_band)::numeric, 1)        AS avg_band
        FROM sessions s
        LEFT JOIN assessments a ON a.session_id = s.id
        WHERE s.status = 'completed'
        GROUP BY s.part
        ORDER BY s.part
        """
    )
    return [dict(r) for r in rows]
