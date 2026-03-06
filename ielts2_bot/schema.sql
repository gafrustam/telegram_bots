-- IELTS Trainer Bot Database Schema

CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT NOT NULL,
    last_name   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Track which section buttons users tap (analytics for all 4 sections)
CREATE TABLE IF NOT EXISTS section_taps (
    id        SERIAL PRIMARY KEY,
    user_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    section   TEXT NOT NULL,
    tapped_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_section_taps_user    ON section_taps(user_id);
CREATE INDEX IF NOT EXISTS idx_section_taps_section ON section_taps(section, tapped_at);

-- Speaking practice sessions (part 1 / 2 / 3)
CREATE TABLE IF NOT EXISTS sessions (
    id                   SERIAL PRIMARY KEY,
    user_id              BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    part                 SMALLINT NOT NULL CHECK (part IN (1, 2, 3)),
    topic                TEXT NOT NULL,
    questions            JSONB,
    cue_card             TEXT,
    status               TEXT NOT NULL DEFAULT 'started'
                           CHECK (status IN ('started', 'completed', 'failed')),
    started_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at         TIMESTAMPTZ,
    audio_duration_total REAL,
    topic_id             INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id    ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user_part  ON sessions(user_id, part);

-- Speaking assessments
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

CREATE INDEX IF NOT EXISTS idx_assessments_user_id    ON assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at);

-- AI-generated topics shown to users
CREATE TABLE IF NOT EXISTS generated_topics (
    id         SERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    part       SMALLINT NOT NULL CHECK (part IN (1, 2, 3)),
    topic      TEXT NOT NULL,
    questions  JSONB,
    cue_card   TEXT,
    accepted   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gen_topics_user ON generated_topics(user_id);

-- Curated topic bank (seeded with real IELTS topics)
CREATE TABLE IF NOT EXISTS topic_bank (
    id        SERIAL PRIMARY KEY,
    part      SMALLINT NOT NULL CHECK (part IN (1, 2, 3)),
    topic     TEXT NOT NULL,
    weight    REAL NOT NULL DEFAULT 1.0,
    cue_card  TEXT,
    questions JSONB,
    UNIQUE (part, topic)
);
