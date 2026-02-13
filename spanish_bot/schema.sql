CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT NOT NULL,
    last_name   TEXT,
    difficulty_level INTEGER NOT NULL DEFAULT 3,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    difficulty_level INTEGER NOT NULL,
    scenario_topic  TEXT NOT NULL,
    scenario_text   TEXT,
    exchange_count  INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    role            TEXT NOT NULL,
    text_content    TEXT,
    audio_file_id   TEXT,
    sequence_num    INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    conversation_id INTEGER REFERENCES conversations(id),
    spanish_word    TEXT NOT NULL,
    english_word    TEXT NOT NULL,
    example         TEXT,
    was_used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS assessments (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    user_id         BIGINT NOT NULL REFERENCES users(id),
    overall_score   REAL NOT NULL DEFAULT 0,
    vocab_use       REAL NOT NULL DEFAULT 0,
    grammar         REAL NOT NULL DEFAULT 0,
    fluency         REAL NOT NULL DEFAULT 0,
    comprehension   REAL NOT NULL DEFAULT 0,
    pronunciation   REAL NOT NULL DEFAULT 0,
    feedback_text   TEXT,
    raw_result      JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
