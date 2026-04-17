import asyncpg
import logging
from datetime import datetime, timezone
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(Config.DATABASE_URL, min_size=2, max_size=5)
    return _pool


async def create_tables(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id              SERIAL PRIMARY KEY,
                symbol          VARCHAR(20)  NOT NULL,
                name            VARCHAR(100) NOT NULL,
                coingecko_id    VARCHAR(100) NOT NULL UNIQUE,
                cmc_url         TEXT,
                target_price    NUMERIC(24, 10),
                last_biweekly_price NUMERIC(24, 10),
                last_biweekly_at    TIMESTAMPTZ,
                is_active       BOOLEAN DEFAULT true,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id          SERIAL PRIMARY KEY,
                token_id    INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
                price_usd   NUMERIC(24, 10) NOT NULL,
                recorded_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # Keep only last 30 days of history (prune old rows)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_history_token_time
            ON price_history(token_id, recorded_at DESC)
        """)
    logger.info("Tables ready")


async def get_active_tokens(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tokens WHERE is_active = true ORDER BY id")
        return [dict(r) for r in rows]


async def get_token_by_coingecko_id(pool: asyncpg.Pool, coingecko_id: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tokens WHERE coingecko_id = $1", coingecko_id
        )
        return dict(row) if row else None


async def upsert_token(
    pool: asyncpg.Pool,
    symbol: str,
    name: str,
    coingecko_id: str,
    cmc_url: str,
    target_price: Optional[float],
) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tokens (symbol, name, coingecko_id, cmc_url, target_price)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (coingecko_id) DO NOTHING
            RETURNING *
            """,
            symbol, name, coingecko_id, cmc_url, target_price,
        )
        if row is None:
            row = await conn.fetchrow(
                "SELECT * FROM tokens WHERE coingecko_id = $1", coingecko_id
            )
        return dict(row)


async def update_target_price(pool: asyncpg.Pool, token_id: int, new_target: float) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE tokens SET target_price = $1 WHERE id = $2",
            new_target, token_id,
        )


async def update_biweekly_snapshot(
    pool: asyncpg.Pool, token_id: int, current_price: float
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tokens
            SET last_biweekly_price = $1, last_biweekly_at = NOW()
            WHERE id = $2
            """,
            current_price, token_id,
        )


async def record_price(pool: asyncpg.Pool, token_id: int, price_usd: float) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO price_history (token_id, price_usd) VALUES ($1, $2)",
            token_id, price_usd,
        )
        # Prune rows older than 60 days to keep DB lean
        await conn.execute(
            """
            DELETE FROM price_history
            WHERE token_id = $1 AND recorded_at < NOW() - INTERVAL '60 days'
            """,
            token_id,
        )
