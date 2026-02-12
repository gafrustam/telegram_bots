-- IELTS Bot Database Schema

CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY,              -- Telegram user_id
    username    TEXT,
    first_name  TEXT NOT NULL,
    last_name   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id                   SERIAL PRIMARY KEY,
    user_id              BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    part                 SMALLINT NOT NULL CHECK (part IN (1, 2, 3)),
    topic                TEXT NOT NULL,
    questions            JSONB,                   -- list of question strings (Parts 1 & 3)
    cue_card             TEXT,                     -- cue card text (Part 2)
    status               TEXT NOT NULL DEFAULT 'started'
                           CHECK (status IN ('started', 'completed', 'failed')),
    started_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at         TIMESTAMPTZ,
    audio_duration_total REAL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user_part ON sessions(user_id, part);

CREATE TABLE IF NOT EXISTS assessments (
    id                         SERIAL PRIMARY KEY,
    session_id                 INTEGER NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    user_id                    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    overall_band               REAL NOT NULL,
    fluency_coherence          REAL NOT NULL,
    lexical_resource           REAL NOT NULL,
    grammatical_range_accuracy REAL NOT NULL,
    pronunciation              REAL NOT NULL,
    raw_result                 JSONB NOT NULL,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at);
