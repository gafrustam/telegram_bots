-- PostgreSQL schema for VPR Bot
-- Tables: users, task_attempts, test_sessions, tasks

CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_attempts (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id),
    grade           INT NOT NULL,
    task_num        INT NOT NULL,
    task_topic      TEXT NOT NULL,
    task_text       TEXT NOT NULL,
    correct_answer  TEXT NOT NULL,
    user_answer     TEXT NOT NULL,
    is_correct      BOOL NOT NULL,
    points_earned   INT NOT NULL,
    points_max      INT NOT NULL,
    attempted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attempts_user_grade ON task_attempts(user_id, grade);

CREATE TABLE IF NOT EXISTS test_sessions (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id),
    grade           INT NOT NULL,
    mode            TEXT NOT NULL,      -- 'timed' | 'practice'
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    total_score     INT,
    max_score       INT,
    grade_mark      INT,                -- 2..5
    tasks_json      JSONB               -- list of task result objects
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON test_sessions(user_id);

-- Static task bank: pre-made VPR tasks for offline use
CREATE TABLE IF NOT EXISTS tasks (
    id              SERIAL PRIMARY KEY,
    grade           INT NOT NULL,
    task_num        INT NOT NULL,
    topic           TEXT NOT NULL,
    task_text       TEXT NOT NULL,
    correct_answer  TEXT NOT NULL,
    solution        TEXT NOT NULL DEFAULT '',
    has_image       BOOL NOT NULL DEFAULT FALSE,
    image_url       TEXT,               -- external URL to image (if any)
    image_file_id   TEXT,               -- Telegram file_id after first send
    source          TEXT,               -- 'manual' | 'fipi' | 'sdamgia' etc.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_grade_num ON tasks(grade, task_num);
