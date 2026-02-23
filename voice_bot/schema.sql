CREATE TABLE IF NOT EXISTS users (
    id         BIGINT PRIMARY KEY,
    username   TEXT,
    first_name TEXT NOT NULL,
    last_name  TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transcriptions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    chat_id     BIGINT NOT NULL,
    file_id     TEXT,
    mime_type   TEXT,
    text        TEXT NOT NULL,
    provider    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS transcriptions_user_id_idx ON transcriptions(user_id);
CREATE INDEX IF NOT EXISTS transcriptions_created_at_idx ON transcriptions(created_at DESC);
