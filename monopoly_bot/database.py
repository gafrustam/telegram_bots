"""Async PostgreSQL persistence for Monopoly visit tracking."""

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
            CREATE TABLE IF NOT EXISTS visits (
                id         SERIAL PRIMARY KEY,
                player_id  TEXT NOT NULL,
                visited_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


def _pool_get() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


async def record_visit(player_id: str) -> None:
    pool = _pool_get()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO visits (player_id) VALUES ($1)",
            player_id,
        )
