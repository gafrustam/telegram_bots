import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "interview.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS problems (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT    NOT NULL,
                level           TEXT    NOT NULL,
                description     TEXT    NOT NULL,
                examples        TEXT    NOT NULL,  -- JSON
                constraints     TEXT    NOT NULL,  -- JSON
                hint1           TEXT    NOT NULL,
                hint2           TEXT    NOT NULL,
                hint3           TEXT    NOT NULL DEFAULT '',
                solution_text   TEXT    NOT NULL,
                failing_test    TEXT,
                time_complexity TEXT,
                space_complexity TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id           INTEGER PRIMARY KEY,
                username          TEXT,
                first_name        TEXT,
                prog_language     TEXT    DEFAULT 'Python',
                level             TEXT    DEFAULT 'junior',
                bot_language      TEXT    DEFAULT 'ru',
                notification_time TEXT    DEFAULT '12:00',
                is_active         INTEGER DEFAULT 1,
                created_at        TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS user_problems (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                problem_id   INTEGER NOT NULL,
                status       TEXT    DEFAULT 'sent',
                hints_used   INTEGER DEFAULT 0,
                solution_shown INTEGER DEFAULT 0,
                sent_at      TEXT    DEFAULT (datetime('now')),
                solved_at    TEXT,
                FOREIGN KEY (user_id)    REFERENCES users(user_id),
                FOREIGN KEY (problem_id) REFERENCES problems(id)
            );

            CREATE INDEX IF NOT EXISTS idx_up_user ON user_problems(user_id);
            CREATE INDEX IF NOT EXISTS idx_p_level ON problems(level);
        """)
        # Migration: add hint3 if not exists
        cols = {row[1] for row in conn.execute("PRAGMA table_info(problems)")}
        if "hint3" not in cols:
            conn.execute("ALTER TABLE problems ADD COLUMN hint3 TEXT NOT NULL DEFAULT ''")


# ─── Problems ────────────────────────────────────────────────────────────────

def seed_problems(problems: list[dict]) -> None:
    """Insert problems that are not yet in DB (idempotent by title). Updates hint3 for existing."""
    with get_conn() as conn:
        existing = {row["title"] for row in conn.execute("SELECT title FROM problems")}
        for p in problems:
            if p["title"] in existing:
                # Update hint3 if provided and not yet set
                hint3 = p.get("hint3", "")
                if hint3:
                    conn.execute(
                        "UPDATE problems SET hint3=? WHERE title=? AND (hint3='' OR hint3 IS NULL)",
                        (hint3, p["title"]),
                    )
                continue
            conn.execute(
                """INSERT INTO problems
                   (title, level, description, examples, constraints,
                    hint1, hint2, hint3, solution_text, failing_test,
                    time_complexity, space_complexity)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
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
                ),
            )


def get_problem(problem_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM problems WHERE id=?", (problem_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["examples"] = json.loads(d["examples"])
    d["constraints"] = json.loads(d["constraints"])
    return d


def get_next_problem(user_id: int, level: str) -> dict | None:
    """Return a random unseen problem for this user at the given level."""
    with get_conn() as conn:
        seen_ids = {
            row["problem_id"]
            for row in conn.execute(
                "SELECT problem_id FROM user_problems WHERE user_id=?", (user_id,)
            )
        }
        candidates = conn.execute(
            "SELECT id FROM problems WHERE level=?", (level,)
        ).fetchall()

    available = [r["id"] for r in candidates if r["id"] not in seen_ids]
    if not available:
        # All problems at this level have been seen — reset and start over
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM user_problems WHERE user_id=? AND problem_id IN "
                "(SELECT id FROM problems WHERE level=?)",
                (user_id, level),
            )
        available = [r["id"] for r in candidates]

    if not available:
        return None

    import random
    problem_id = random.choice(available)
    return get_problem(problem_id)


def problems_count_by_level(level: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM problems WHERE level=?", (level,)
        ).fetchone()
    return row["cnt"] if row else 0


# ─── Users ───────────────────────────────────────────────────────────────────

def upsert_user(
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO users (user_id, username, first_name)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username,
                 first_name=excluded.first_name""",
            (user_id, username, first_name),
        )


def get_user(user_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_user(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {cols} WHERE user_id=?", vals)


def get_all_active_users() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active=1"
        ).fetchall()
    return [dict(r) for r in rows]


def is_setup_complete(user_id: int) -> bool:
    user = get_user(user_id)
    if user is None:
        return False
    return bool(user.get("prog_language") and user.get("level"))


# ─── User problems ────────────────────────────────────────────────────────────

def record_problem_sent(user_id: int, problem_id: int) -> int:
    """Record that this problem was sent to the user. Returns new record id."""
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO user_problems (user_id, problem_id, status) VALUES (?,?,'sent')",
            (user_id, problem_id),
        )
        return cursor.lastrowid


def update_problem_record(record_id: int, **kwargs) -> None:
    if not kwargs:
        return
    if "status" in kwargs and kwargs["status"] == "solved":
        kwargs.setdefault("solved_at", datetime.utcnow().isoformat())
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [record_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE user_problems SET {cols} WHERE id=?", vals)


def get_user_stats(user_id: int) -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM user_problems WHERE user_id=? GROUP BY status",
            (user_id,),
        ).fetchall()
    stats = {"sent": 0, "solved": 0, "failed": 0}
    for row in rows:
        stats[row["status"]] = row["cnt"]
    return stats
