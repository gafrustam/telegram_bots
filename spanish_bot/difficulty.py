"""25 difficulty levels for Spanish conversation practice."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DifficultyLevel:
    level: int
    label: str
    cefr: str
    vocab_count: int          # words to pre-teach
    max_sentence_words: int   # target sentence length
    exchanges: int            # number of bot-user exchanges
    grammar: str              # allowed grammar structures
    topics: str               # topic pool description


LEVELS: dict[int, DifficultyLevel] = {
    # ── Absolute Beginner (A0–A1) ──────────────────────
    1: DifficultyLevel(
        level=1, label="Principiante 1", cefr="A0",
        vocab_count=3, max_sentence_words=5, exchanges=3,
        grammar="present tense of ser/estar, simple greetings",
        topics="greetings, introducing yourself, saying hello/goodbye",
    ),
    2: DifficultyLevel(
        level=2, label="Principiante 2", cefr="A0",
        vocab_count=4, max_sentence_words=6, exchanges=3,
        grammar="present tense regular -ar verbs, articles",
        topics="family, numbers, colors, basic descriptions",
    ),
    3: DifficultyLevel(
        level=3, label="Principiante 3", cefr="A1",
        vocab_count=4, max_sentence_words=7, exchanges=4,
        grammar="present tense regular -ar/-er/-ir verbs, gender/number agreement",
        topics="daily routine, food, home, pets",
    ),
    4: DifficultyLevel(
        level=4, label="Principiante 4", cefr="A1",
        vocab_count=5, max_sentence_words=8, exchanges=4,
        grammar="present tense including common irregulars (tener, ir, querer), possessives",
        topics="school, work, hobbies, weekend activities",
    ),
    5: DifficultyLevel(
        level=5, label="Principiante 5", cefr="A1",
        vocab_count=5, max_sentence_words=8, exchanges=4,
        grammar="present tense all common irregulars, gustar construction, hay",
        topics="shopping, clothes, weather, likes/dislikes",
    ),

    # ── Elementary (A2) ────────────────────────────────
    6: DifficultyLevel(
        level=6, label="Elemental 1", cefr="A2",
        vocab_count=5, max_sentence_words=10, exchanges=5,
        grammar="preterite tense regular verbs, present progressive",
        topics="vacations, travel experiences, last weekend",
    ),
    7: DifficultyLevel(
        level=7, label="Elemental 2", cefr="A2",
        vocab_count=6, max_sentence_words=10, exchanges=5,
        grammar="preterite irregular (ir, ser, hacer), reflexive verbs",
        topics="morning routine, health, body parts, doctor visits",
    ),
    8: DifficultyLevel(
        level=8, label="Elemental 3", cefr="A2",
        vocab_count=6, max_sentence_words=12, exchanges=5,
        grammar="imperfect tense, preterite vs imperfect basics",
        topics="childhood memories, describing past habits, city/country life",
    ),
    9: DifficultyLevel(
        level=9, label="Elemental 4", cefr="A2",
        vocab_count=6, max_sentence_words=12, exchanges=6,
        grammar="comparatives/superlatives, direct object pronouns",
        topics="restaurants, ordering food, cooking recipes",
    ),
    10: DifficultyLevel(
        level=10, label="Elemental 5", cefr="A2",
        vocab_count=7, max_sentence_words=12, exchanges=6,
        grammar="indirect object pronouns, near future (ir + a + inf), basic commands",
        topics="giving directions, transportation, making plans",
    ),

    # ── Pre-Intermediate (B1) ──────────────────────────
    11: DifficultyLevel(
        level=11, label="Intermedio 1", cefr="B1",
        vocab_count=7, max_sentence_words=14, exchanges=6,
        grammar="present subjunctive with querer/esperar/ojalá, por vs para",
        topics="opinions, recommendations, hopes and wishes",
    ),
    12: DifficultyLevel(
        level=12, label="Intermedio 2", cefr="B1",
        vocab_count=7, max_sentence_words=14, exchanges=7,
        grammar="subjunctive with emotion/doubt, conditional tense basics",
        topics="environment, news events, social issues",
    ),
    13: DifficultyLevel(
        level=13, label="Intermedio 3", cefr="B1",
        vocab_count=8, max_sentence_words=15, exchanges=7,
        grammar="conditional tense, si clauses (present), relative pronouns",
        topics="hypothetical situations, job interviews, future plans",
    ),
    14: DifficultyLevel(
        level=14, label="Intermedio 4", cefr="B1",
        vocab_count=8, max_sentence_words=15, exchanges=7,
        grammar="present perfect, past perfect, double object pronouns",
        topics="life experiences, achievements, technology use",
    ),
    15: DifficultyLevel(
        level=15, label="Intermedio 5", cefr="B1",
        vocab_count=8, max_sentence_words=16, exchanges=8,
        grammar="all B1 grammar, connectors (sin embargo, aunque, por lo tanto)",
        topics="culture, traditions, describing experiences in detail",
    ),

    # ── Intermediate (B2) ─────────────────────────────
    16: DifficultyLevel(
        level=16, label="Avanzado 1", cefr="B2",
        vocab_count=8, max_sentence_words=18, exchanges=8,
        grammar="imperfect subjunctive, si clauses (past), passive voice",
        topics="politics, economics, debating social issues",
    ),
    17: DifficultyLevel(
        level=17, label="Avanzado 2", cefr="B2",
        vocab_count=9, max_sentence_words=18, exchanges=9,
        grammar="past subjunctive in all contexts, future perfect",
        topics="literature, art, film discussions, reviews",
    ),
    18: DifficultyLevel(
        level=18, label="Avanzado 3", cefr="B2",
        vocab_count=9, max_sentence_words=20, exchanges=9,
        grammar="complex si clauses, subjunctive in adjective/adverb clauses",
        topics="workplace dynamics, negotiation, conflict resolution",
    ),
    19: DifficultyLevel(
        level=19, label="Avanzado 4", cefr="B2",
        vocab_count=10, max_sentence_words=20, exchanges=10,
        grammar="all B2 grammar, common idioms, colloquial expressions",
        topics="philosophy, ethics, cultural differences",
    ),
    20: DifficultyLevel(
        level=20, label="Avanzado 5", cefr="B2",
        vocab_count=10, max_sentence_words=22, exchanges=10,
        grammar="all B2 grammar, nuanced register (formal/informal), idioms",
        topics="any topic, debate format, persuasive arguments",
    ),

    # ── Advanced (C1–C2) ──────────────────────────────
    21: DifficultyLevel(
        level=21, label="Superior 1", cefr="C1",
        vocab_count=10, max_sentence_words=25, exchanges=10,
        grammar="all tenses/moods, complex subordination, literary devices",
        topics="abstract topics, academic discussions, professional scenarios",
    ),
    22: DifficultyLevel(
        level=22, label="Superior 2", cefr="C1",
        vocab_count=10, max_sentence_words=25, exchanges=11,
        grammar="regional variations, voseo, leísmo awareness, advanced idioms",
        topics="regional dialects, Latin American vs Spain culture, humor",
    ),
    23: DifficultyLevel(
        level=23, label="Superior 3", cefr="C1",
        vocab_count=10, max_sentence_words=28, exchanges=11,
        grammar="native-like structures, slang, proverbs, double meanings",
        topics="current events analysis, in-depth cultural topics",
    ),
    24: DifficultyLevel(
        level=24, label="Superior 4", cefr="C2",
        vocab_count=10, max_sentence_words=30, exchanges=12,
        grammar="full native grammar, wordplay, sophisticated register switching",
        topics="any topic at native level, spontaneous conversation",
    ),
    25: DifficultyLevel(
        level=25, label="Superior 5", cefr="C2",
        vocab_count=10, max_sentence_words=30, exchanges=12,
        grammar="complete mastery, literary/poetic forms, dialectal awareness",
        topics="unrestricted: philosophy, science, art, politics, humor, anything",
    ),
}


def get_level(n: int) -> DifficultyLevel:
    return LEVELS[max(1, min(25, n))]


def format_level_info(n: int) -> str:
    lvl = get_level(n)
    return (
        f"Nivel {lvl.level} — {lvl.label} ({lvl.cefr})\n"
        f"Intercambios: {lvl.exchanges}"
    )
