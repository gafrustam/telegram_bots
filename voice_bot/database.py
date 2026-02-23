import logging
import os
from pathlib import Path
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


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


async def _execute(query: str, *args: Any) -> None:
    if not _pool:
        return
    try:
        async with _pool.acquire() as conn:
            await conn.execute(query, *args)
    except Exception:
        logger.exception("DB execute error")


async def upsert_user(user_id: int, username: str | None, first_name: str, last_name: str | None) -> None:
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


async def save_transcription(
    user_id: int, chat_id: int,
    file_id: str | None, mime_type: str | None,
    text: str, provider: str,
) -> None:
    await _execute(
        """
        INSERT INTO transcriptions (user_id, chat_id, file_id, mime_type, text, provider)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_id, chat_id, file_id, mime_type, text, provider,
    )
