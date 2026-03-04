"""PostgreSQL persistence for poker game sessions."""

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
            CREATE TABLE IF NOT EXISTS game_sessions (
                user_id    TEXT PRIMARY KEY,
                game_json  TEXT NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                user_id     TEXT PRIMARY KEY,
                hands_won   INTEGER DEFAULT 0,
                hands_lost  INTEGER DEFAULT 0,
                biggest_pot INTEGER DEFAULT 0,
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)


def _pool_get() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


async def save_game(user_id: str, game_dict: dict) -> None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO game_sessions (user_id, game_json, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT(user_id) DO UPDATE SET
                game_json  = EXCLUDED.game_json,
                updated_at = NOW()
        """, str(user_id), json.dumps(game_dict))


async def load_game(user_id: str) -> dict | None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT game_json FROM game_sessions WHERE user_id=$1",
            str(user_id),
        )
    if row:
        return json.loads(row["game_json"])
    return None


async def delete_game(user_id: str) -> None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM game_sessions WHERE user_id=$1",
            str(user_id),
        )


async def update_stats(user_id: str, won: bool, pot: int) -> None:
    pool = _pool_get()
    won_inc = 1 if won else 0
    lost_inc = 0 if won else 1
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO stats (user_id, hands_won, hands_lost, biggest_pot, updated_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT(user_id) DO UPDATE SET
                hands_won   = stats.hands_won   + $2,
                hands_lost  = stats.hands_lost  + $3,
                biggest_pot = GREATEST(stats.biggest_pot, $4),
                updated_at  = NOW()
        """, str(user_id), won_inc, lost_inc, pot)
