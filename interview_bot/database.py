"""Async PostgreSQL persistence for the interview prep bot."""

import json
import logging
import os
import random
from datetime import datetime

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
            CREATE TABLE IF NOT EXISTS problems (
                id               SERIAL PRIMARY KEY,
                title            TEXT NOT NULL,
                level            TEXT NOT NULL,
                description      TEXT NOT NULL,
                examples         TEXT NOT NULL,
                constraints      TEXT NOT NULL,
                hint1            TEXT NOT NULL,
                hint2            TEXT NOT NULL,
                hint3            TEXT NOT NULL DEFAULT '',
                solution_text    TEXT NOT NULL,
                failing_test     TEXT,
                time_complexity  TEXT,
                space_complexity TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id           BIGINT PRIMARY KEY,
                username          TEXT,
                first_name        TEXT,
                prog_language     TEXT DEFAULT 'Python',
                level             TEXT DEFAULT 'junior',
                bot_language      TEXT DEFAULT 'ru',
                notification_time TEXT DEFAULT '12:00',
                is_active         INTEGER DEFAULT 1,
                created_at        TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_problems (
                id             SERIAL PRIMARY KEY,
                user_id        BIGINT NOT NULL,
                problem_id     INTEGER NOT NULL,
                status         TEXT DEFAULT 'sent',
                hints_used     INTEGER DEFAULT 0,
                solution_shown INTEGER DEFAULT 0,
                sent_at        TIMESTAMPTZ DEFAULT NOW(),
                solved_at      TIMESTAMPTZ,
                FOREIGN KEY (user_id)    REFERENCES users(user_id),
                FOREIGN KEY (problem_id) REFERENCES problems(id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_up_user ON user_problems(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_p_level ON problems(level)")


def _pool_get() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


# ─── Problems ────────────────────────────────────────────────────────────────

async def seed_problems(problems: list[dict]) -> None:
    """Insert problems that are not yet in DB (idempotent by title). Updates hint3 for existing."""
    pool = _pool_get()
    async with pool.acquire() as conn:
        existing = {row["title"] for row in await conn.fetch("SELECT title FROM problems")}
        for p in problems:
            if p["title"] in existing:
                hint3 = p.get("hint3", "")
                if hint3:
                    await conn.execute(
                        "UPDATE problems SET hint3=$1 WHERE title=$2 AND (hint3='' OR hint3 IS NULL)",
                        hint3, p["title"],
                    )
                continue
            await conn.execute(
                """INSERT INTO problems
                   (title, level, description, examples, constraints,
                    hint1, hint2, hint3, solution_text, failing_test,
                    time_complexity, space_complexity)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)""",
                p["title"],
                p["level"],
                p["description"],
                json.dumps(p["examples"], ensure_ascii=False),
                json.dumps(p.get("constraints", []), ensure_ascii=False),
                p["hint1"],
                p["hint2"],
                p.get("hint3", ""),
                p["solution_text"],
                p.get("failing_test"),
                p.get("time_complexity"),
                p.get("space_complexity"),
            )


async def get_problem(problem_id: int) -> dict | None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM problems WHERE id=$1", problem_id)
    if row is None:
        return None
    d = dict(row)
    d["examples"] = json.loads(d["examples"])
    d["constraints"] = json.loads(d["constraints"])
    return d


async def get_next_problem(user_id: int, level: str) -> dict | None:
    """Return a random unseen problem for this user at the given level."""
    pool = _pool_get()
    async with pool.acquire() as conn:
        seen_ids = {
            row["problem_id"]
            for row in await conn.fetch(
                "SELECT problem_id FROM user_problems WHERE user_id=$1", user_id
            )
        }
        candidates = await conn.fetch("SELECT id FROM problems WHERE level=$1", level)

    available = [r["id"] for r in candidates if r["id"] not in seen_ids]
    if not available:
        # All problems at this level seen — reset and start over
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_problems WHERE user_id=$1 AND problem_id IN "
                "(SELECT id FROM problems WHERE level=$2)",
                user_id, level,
            )
        available = [r["id"] for r in candidates]

    if not available:
        return None

    problem_id = random.choice(available)
    return await get_problem(problem_id)


async def problems_count_by_level(level: str) -> int:
    pool = _pool_get()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS cnt FROM problems WHERE level=$1", level)
    return row["cnt"] if row else 0


# ─── Users ───────────────────────────────────────────────────────────────────

async def upsert_user(
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, username, first_name)
               VALUES ($1, $2, $3)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=EXCLUDED.username,
                 first_name=EXCLUDED.first_name""",
            user_id, username, first_name,
        )


async def get_user(user_id: int) -> dict | None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
    return dict(row) if row else None


async def update_user(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    pool = _pool_get()
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    set_clause = ", ".join(f"{k}=${i+1}" for i, k in enumerate(keys))
    n = len(keys) + 1
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {set_clause} WHERE user_id=${n}",
            *vals, user_id,
        )


async def get_all_active_users() -> list[dict]:
    pool = _pool_get()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users WHERE is_active=1")
    return [dict(r) for r in rows]


async def is_setup_complete(user_id: int) -> bool:
    user = await get_user(user_id)
    if user is None:
        return False
    return bool(user.get("prog_language") and user.get("level"))


# ─── User problems ────────────────────────────────────────────────────────────

async def record_problem_sent(user_id: int, problem_id: int) -> int:
    """Record that this problem was sent to the user. Returns new record id."""
    pool = _pool_get()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO user_problems (user_id, problem_id, status) VALUES ($1,$2,'sent') RETURNING id",
            user_id, problem_id,
        )
        return row["id"]


async def update_problem_record(record_id: int, **kwargs) -> None:
    if not kwargs:
        return
    if "status" in kwargs and kwargs["status"] == "solved":
        kwargs.setdefault("solved_at", datetime.utcnow())
    pool = _pool_get()
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    set_clause = ", ".join(f"{k}=${i+1}" for i, k in enumerate(keys))
    n = len(keys) + 1
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE user_problems SET {set_clause} WHERE id=${n}",
            *vals, record_id,
        )


async def get_user_stats(user_id: int) -> dict:
    pool = _pool_get()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT status, COUNT(*) AS cnt FROM user_problems WHERE user_id=$1 GROUP BY status",
            user_id,
        )
    stats = {"sent": 0, "solved": 0, "failed": 0}
    for row in rows:
        stats[row["status"]] = row["cnt"]
    return stats
