"""SQLite persistence for poker game sessions."""

import json
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent / "poker.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                user_id   TEXT PRIMARY KEY,
                game_json TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                user_id    TEXT PRIMARY KEY,
                hands_won  INTEGER DEFAULT 0,
                hands_lost INTEGER DEFAULT 0,
                biggest_pot INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_game(user_id: str, game_dict: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO game_sessions (user_id, game_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                game_json  = excluded.game_json,
                updated_at = CURRENT_TIMESTAMP
        """, (str(user_id), json.dumps(game_dict)))
        await db.commit()


async def load_game(user_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT game_json FROM game_sessions WHERE user_id = ?",
            (str(user_id),)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return json.loads(row[0])
    return None


async def delete_game(user_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM game_sessions WHERE user_id = ?",
            (str(user_id),)
        )
        await db.commit()


async def update_stats(user_id: str, won: bool, pot: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO stats (user_id, hands_won, hands_lost, biggest_pot, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                hands_won   = hands_won   + ?,
                hands_lost  = hands_lost  + ?,
                biggest_pot = MAX(biggest_pot, ?),
                updated_at  = CURRENT_TIMESTAMP
        """, (
            str(user_id),
            1 if won else 0,
            0 if won else 1,
            pot,
            1 if won else 0,
            0 if won else 1,
            pot,
        ))
        await db.commit()
