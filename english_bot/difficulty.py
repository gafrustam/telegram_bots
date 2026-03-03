"""25 difficulty levels for English conversation practice."""

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
    # ── Absolute Beginner (A0–A1) ──────────────────────
    1: DifficultyLevel(level=1, label="Beginner 1", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=4, exchanges=2),
    2: DifficultyLevel(level=2, label="Beginner 2", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=5, exchanges=2),
    3: DifficultyLevel(level=3, label="Beginner 3", cefr="A1",
        vocab_count=5, construction_count=2, max_sentence_words=6, exchanges=3),
    4: DifficultyLevel(level=4, label="Beginner 4", cefr="A1",
        vocab_count=6, construction_count=2, max_sentence_words=7, exchanges=3),
    5: DifficultyLevel(level=5, label="Beginner 5", cefr="A1",
        vocab_count=6, construction_count=3, max_sentence_words=7, exchanges=3),

    # ── Elementary (A2) ────────────────────────────────
    6: DifficultyLevel(level=6, label="Elementary 1", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=9, exchanges=4),
    7: DifficultyLevel(level=7, label="Elementary 2", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=10, exchanges=4),
    8: DifficultyLevel(level=8, label="Elementary 3", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=10, exchanges=5),
    9: DifficultyLevel(level=9, label="Elementary 4", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=11, exchanges=5),
    10: DifficultyLevel(level=10, label="Elementary 5", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=12, exchanges=5),

    # ── Pre-Intermediate (B1) ──────────────────────────
    11: DifficultyLevel(level=11, label="Pre-Intermediate 1", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=6),
    12: DifficultyLevel(level=12, label="Pre-Intermediate 2", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=7),
    13: DifficultyLevel(level=13, label="Intermediate 1", cefr="B1",
        vocab_count=8, construction_count=3, max_sentence_words=15, exchanges=7),
    14: DifficultyLevel(level=14, label="Intermediate 2", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=15, exchanges=7),
    15: DifficultyLevel(level=15, label="Intermediate 3", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=16, exchanges=8),

    # ── Intermediate (B2) ─────────────────────────────
    16: DifficultyLevel(level=16, label="Upper-Intermediate 1", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=8),
    17: DifficultyLevel(level=17, label="Upper-Intermediate 2", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=9),
    18: DifficultyLevel(level=18, label="Upper-Intermediate 3", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=9),
    19: DifficultyLevel(level=19, label="Upper-Intermediate 4", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=10),
    20: DifficultyLevel(level=20, label="Upper-Intermediate 5", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=22, exchanges=10),

    # ── Advanced (C1–C2) ──────────────────────────────
    21: DifficultyLevel(level=21, label="Advanced 1", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=10),
    22: DifficultyLevel(level=22, label="Advanced 2", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=11),
    23: DifficultyLevel(level=23, label="Advanced 3", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=28, exchanges=11),
    24: DifficultyLevel(level=24, label="Mastery 1", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12),
    25: DifficultyLevel(level=25, label="Mastery 2", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12),
}


def get_level(n: int) -> DifficultyLevel:
    return LEVELS[max(1, min(25, n))]


def format_level_info(n: int) -> str:
    lvl = get_level(n)
    return (
        f"Level {lvl.level} — {lvl.label} ({lvl.cefr})\n"
        f"Exchanges: {lvl.exchanges}"
    )
