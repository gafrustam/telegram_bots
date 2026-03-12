"""13 difficulty levels for English conversation practice (CEFR-based)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DifficultyLevel:
    level: int
    label: str
    cefr: str
    vocab_count: int          # words to pre-teach
    construction_count: int   # grammar constructions to suggest
    max_sentence_words: int   # target sentence length
    exchanges: int            # number of bot-user exchanges


LEVELS: dict[int, DifficultyLevel] = {
    # ── Absolute Beginner (A0) ──────────────────────────
    1: DifficultyLevel(level=1, label="A0", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=5, exchanges=2),

    # ── Elementary (A1) ─────────────────────────────────
    2: DifficultyLevel(level=2, label="A1-1", cefr="A1",
        vocab_count=5, construction_count=2, max_sentence_words=6, exchanges=3),
    3: DifficultyLevel(level=3, label="A1-2", cefr="A1",
        vocab_count=6, construction_count=2, max_sentence_words=8, exchanges=3),

    # ── Pre-Elementary (A2) ──────────────────────────────
    4: DifficultyLevel(level=4, label="A2-1", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=10, exchanges=4),
    5: DifficultyLevel(level=5, label="A2-2", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=12, exchanges=5),

    # ── Pre-Intermediate (B1) ───────────────────────────
    6: DifficultyLevel(level=6, label="B1-1", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=6),
    7: DifficultyLevel(level=7, label="B1-2", cefr="B1",
        vocab_count=7, construction_count=4, max_sentence_words=16, exchanges=7),

    # ── Upper-Intermediate (B2) ─────────────────────────
    8: DifficultyLevel(level=8, label="B2-1", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=8),
    9: DifficultyLevel(level=9, label="B2-2", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=9),

    # ── Advanced (C1) ───────────────────────────────────
    10: DifficultyLevel(level=10, label="C1-1", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=24, exchanges=10),
    11: DifficultyLevel(level=11, label="C1-2", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=27, exchanges=11),

    # ── Mastery (C2) ────────────────────────────────────
    12: DifficultyLevel(level=12, label="C2-1", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12),
    13: DifficultyLevel(level=13, label="C2-2", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12),
}


def get_level(n: int) -> DifficultyLevel:
    return LEVELS[max(1, min(13, n))]


def format_level_info(n: int) -> str:
    lvl = get_level(n)
    return (
        f"Level {lvl.level} — {lvl.label}\n"
        f"Exchanges: {lvl.exchanges}"
    )
