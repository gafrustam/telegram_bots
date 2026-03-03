"""Async SQLite persistence for Monopoly visit tracking."""

from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "monopoly.db"

_CREATE_VISITS = """
CREATE TABLE IF NOT EXISTS visits (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT    NOT NULL,
    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_VISITS)
        await db.commit()


async def record_visit(player_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO visits (player_id) VALUES (?)",
            (player_id,),
        )
        await db.commit()
