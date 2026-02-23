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
    grammar: str              # allowed grammar structures
    topics: str               # topic pool description


LEVELS: dict[int, DifficultyLevel] = {
    # ── Absolute Beginner (A0–A1) ──────────────────────
    1: DifficultyLevel(
        level=1, label="Beginner 1", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=4, exchanges=2,
        grammar="greetings (hello, goodbye), My name is..., I am..., yes/no",
        topics="saying hello, introducing yourself, saying goodbye",
    ),
    2: DifficultyLevel(
        level=2, label="Beginner 2", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=5, exchanges=2,
        grammar="to be (I am, you are, he is), articles (a, an, the), basic adjectives",
        topics="family members, colors, simple descriptions",
    ),
    3: DifficultyLevel(
        level=3, label="Beginner 3", cefr="A1",
        vocab_count=5, construction_count=2, max_sentence_words=6, exchanges=3,
        grammar="present simple (I like, I have, I go), basic nouns and verbs",
        topics="daily activities, food basics, simple likes and dislikes",
    ),
    4: DifficultyLevel(
        level=4, label="Beginner 4", cefr="A1",
        vocab_count=6, construction_count=2, max_sentence_words=7, exchanges=3,
        grammar="present simple all persons, there is/are, have got",
        topics="home, pets, school, possessions",
    ),
    5: DifficultyLevel(
        level=5, label="Beginner 5", cefr="A1",
        vocab_count=6, construction_count=3, max_sentence_words=7, exchanges=3,
        grammar="present continuous (I am doing), can/can't for ability",
        topics="hobbies, weekend activities, abilities, weather",
    ),

    # ── Elementary (A2) ────────────────────────────────
    6: DifficultyLevel(
        level=6, label="Elementary 1", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=9, exchanges=4,
        grammar="going to for future plans, adverbs of frequency, time expressions",
        topics="plans for today, daily routines, simple schedules",
    ),
    7: DifficultyLevel(
        level=7, label="Elementary 2", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=10, exchanges=4,
        grammar="past simple regular verbs (-ed), yesterday/last week",
        topics="what I did yesterday, last weekend, simple past events",
    ),
    8: DifficultyLevel(
        level=8, label="Elementary 3", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=10, exchanges=5,
        grammar="past simple irregular verbs (go/went, see/saw, eat/ate), time phrases",
        topics="holidays, travel, describing past experiences",
    ),
    9: DifficultyLevel(
        level=9, label="Elementary 4", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=11, exchanges=5,
        grammar="used to for past habits, comparatives (bigger than, more interesting than)",
        topics="childhood memories, comparing things, past habits",
    ),
    10: DifficultyLevel(
        level=10, label="Elementary 5", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=12, exchanges=5,
        grammar="modal verbs (should, must, have to), giving advice and instructions",
        topics="restaurants, ordering food, giving simple directions, shopping",
    ),

    # ── Pre-Intermediate (B1) ──────────────────────────
    11: DifficultyLevel(
        level=11, label="Pre-Intermediate 1", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=6,
        grammar="present perfect (have + past participle) with ever/never/just/already/yet",
        topics="life experiences, things you've done, achievements",
    ),
    12: DifficultyLevel(
        level=12, label="Pre-Intermediate 2", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=7,
        grammar="present perfect vs past simple, for and since, how long",
        topics="ongoing situations, living somewhere, knowing someone",
    ),
    13: DifficultyLevel(
        level=13, label="Intermediate 1", cefr="B1",
        vocab_count=8, construction_count=3, max_sentence_words=15, exchanges=7,
        grammar="first conditional (if + present, will + base), future will for predictions",
        topics="plans, predictions, problem-solving, job interviews",
    ),
    14: DifficultyLevel(
        level=14, label="Intermediate 2", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=15, exchanges=7,
        grammar="second conditional (if + past, would + base), wish + past simple",
        topics="hypothetical situations, dreams, imaginary scenarios",
    ),
    15: DifficultyLevel(
        level=15, label="Intermediate 3", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=16, exchanges=8,
        grammar="all B1 grammar, connectors (however, although, therefore, in addition)",
        topics="culture, traditions, describing experiences in detail, news topics",
    ),

    # ── Intermediate (B2) ─────────────────────────────
    16: DifficultyLevel(
        level=16, label="Upper-Intermediate 1", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=8,
        grammar="passive voice (all tenses), reporting verbs (said that, told me, asked if)",
        topics="society, technology, environment, debating issues",
    ),
    17: DifficultyLevel(
        level=17, label="Upper-Intermediate 2", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=9,
        grammar="third conditional (if + past perfect, would have), mixed conditionals",
        topics="regrets, past decisions, alternative histories, lessons learned",
    ),
    18: DifficultyLevel(
        level=18, label="Upper-Intermediate 3", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=9,
        grammar="complex relative clauses (who, which, where, whose), participle clauses",
        topics="work, negotiations, conflict resolution, professional scenarios",
    ),
    19: DifficultyLevel(
        level=19, label="Upper-Intermediate 4", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=10,
        grammar="modal perfects (must have, could have, should have), hedging language",
        topics="philosophy, ethics, speculating about the past, cultural differences",
    ),
    20: DifficultyLevel(
        level=20, label="Upper-Intermediate 5", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=22, exchanges=10,
        grammar="all B2 grammar, common idioms, colloquial expressions, formal register",
        topics="any topic, debate format, persuasive arguments, complex opinions",
    ),

    # ── Advanced (C1–C2) ──────────────────────────────
    21: DifficultyLevel(
        level=21, label="Advanced 1", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=10,
        grammar="inversion (Never have I..., Not only did...), cleft sentences (It was...that)",
        topics="abstract topics, academic discussions, professional scenarios",
    ),
    22: DifficultyLevel(
        level=22, label="Advanced 2", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=11,
        grammar="complex nominalization, advanced collocations, idiomatic verb phrases",
        topics="British vs American English, humor, cultural nuances, social commentary",
    ),
    23: DifficultyLevel(
        level=23, label="Advanced 3", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=28, exchanges=11,
        grammar="native-like structures, slang, proverbs, double meanings, ellipsis",
        topics="current events analysis, in-depth cultural topics, personal anecdotes",
    ),
    24: DifficultyLevel(
        level=24, label="Mastery 1", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12,
        grammar="full native grammar, wordplay, sophisticated register switching, rhetorical devices",
        topics="any topic at native level, spontaneous conversation, storytelling",
    ),
    25: DifficultyLevel(
        level=25, label="Mastery 2", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12,
        grammar="complete mastery, literary/poetic forms, dialectal awareness, subtle nuance",
        topics="unrestricted: philosophy, science, art, politics, humor, anything",
    ),
}


def get_level(n: int) -> DifficultyLevel:
    return LEVELS[max(1, min(25, n))]


def format_level_info(n: int) -> str:
    lvl = get_level(n)
    return (
        f"Level {lvl.level} — {lvl.label} ({lvl.cefr})\n"
        f"Exchanges: {lvl.exchanges}"
    )
