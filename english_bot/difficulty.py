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
    grammar: list[str]        # grammar sub-topics to rotate across lessons
    topics: str               # topic pool description


LEVELS: dict[int, DifficultyLevel] = {
    # ── Absolute Beginner (A0–A1) ──────────────────────
    1: DifficultyLevel(
        level=1, label="Beginner 1", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=4, exchanges=2,
        grammar=[
            "My name is..., I am... (self-introduction)",
            "greetings: hello, hi, goodbye, how are you",
            "yes/no responses, numbers 1-10",
        ],
        topics="saying hello, introducing yourself, saying goodbye",
    ),
    2: DifficultyLevel(
        level=2, label="Beginner 2", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=5, exchanges=2,
        grammar=[
            "to be: I am, you are, he/she/it is (positive sentences)",
            "articles: a, an, the",
            "basic adjectives: big, small, old, new, happy, sad",
        ],
        topics="family members, colors, simple descriptions",
    ),
    3: DifficultyLevel(
        level=3, label="Beginner 3", cefr="A1",
        vocab_count=5, construction_count=2, max_sentence_words=6, exchanges=3,
        grammar=[
            "present simple with I: I like, I have, I go, I eat",
            "basic verbs: want, need, see, know, think",
            "present simple questions: Do you...? What do you...?",
        ],
        topics="daily activities, food basics, simple likes and dislikes",
    ),
    4: DifficultyLevel(
        level=4, label="Beginner 4", cefr="A1",
        vocab_count=6, construction_count=2, max_sentence_words=7, exchanges=3,
        grammar=[
            "present simple: he/she/it + s (likes, has, goes)",
            "there is / there are + singular/plural nouns",
            "have got: I have got, he has got, Have you got...?",
        ],
        topics="home, pets, school, possessions",
    ),
    5: DifficultyLevel(
        level=5, label="Beginner 5", cefr="A1",
        vocab_count=6, construction_count=3, max_sentence_words=7, exchanges=3,
        grammar=[
            "present continuous: I am doing, she is working (right now)",
            "can for ability: I can swim, she can't speak French",
            "can for requests/permission: Can I...? Can you...?",
        ],
        topics="hobbies, weekend activities, abilities, weather",
    ),

    # ── Elementary (A2) ────────────────────────────────
    6: DifficultyLevel(
        level=6, label="Elementary 1", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=9, exchanges=4,
        grammar=[
            "going to for plans: I am going to..., Are you going to...?",
            "adverbs of frequency: always, usually, often, sometimes, never",
            "time expressions: every day, at 5pm, on Mondays, twice a week",
        ],
        topics="plans for today, daily routines, simple schedules",
    ),
    7: DifficultyLevel(
        level=7, label="Elementary 2", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=10, exchanges=4,
        grammar=[
            "past simple regular verbs: walked, played, watched, talked",
            "past simple questions: Did you...? What did you...?",
            "past simple negatives: I didn't go, she didn't eat",
        ],
        topics="what I did yesterday, last weekend, simple past events",
    ),
    8: DifficultyLevel(
        level=8, label="Elementary 3", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=10, exchanges=5,
        grammar=[
            "past simple irregular: go/went, come/came, see/saw, make/made",
            "past simple irregular: eat/ate, drink/drank, take/took, get/got",
            "time phrases: last month, in 2020, three years ago, the other day",
        ],
        topics="holidays, travel, describing past experiences",
    ),
    9: DifficultyLevel(
        level=9, label="Elementary 4", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=11, exchanges=5,
        grammar=[
            "used to for past habits: I used to play, she used to live",
            "comparatives: bigger than, more interesting than, better than",
            "superlatives: the biggest, the most interesting, the best",
        ],
        topics="childhood memories, comparing things, past habits",
    ),
    10: DifficultyLevel(
        level=10, label="Elementary 5", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=12, exchanges=5,
        grammar=[
            "should/shouldn't for advice: You should eat..., You shouldn't smoke",
            "must/have to for obligation: You must wear..., I have to work",
            "imperatives: Turn left, Don't forget, Be careful, Please sit down",
        ],
        topics="restaurants, ordering food, giving simple directions, shopping",
    ),

    # ── Pre-Intermediate (B1) ──────────────────────────
    11: DifficultyLevel(
        level=11, label="Pre-Intermediate 1", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=6,
        grammar=[
            "present perfect with ever/never: Have you ever been to...?",
            "present perfect with just/already: I have just arrived, She has already finished",
            "present perfect with yet: Have you done it yet? I haven't done it yet",
        ],
        topics="life experiences, things you've done, achievements",
    ),
    12: DifficultyLevel(
        level=12, label="Pre-Intermediate 2", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=7,
        grammar=[
            "present perfect vs past simple: I have lived here for 5 years / I lived there in 2020",
            "for and since: I have known her for years / since 2010",
            "How long have you...? How long did you...?",
        ],
        topics="ongoing situations, living somewhere, knowing someone",
    ),
    13: DifficultyLevel(
        level=13, label="Intermediate 1", cefr="B1",
        vocab_count=8, construction_count=3, max_sentence_words=15, exchanges=7,
        grammar=[
            "first conditional: If it rains, I will stay home",
            "will for spontaneous decisions and promises: I'll help you, I'll call her",
            "future with will for predictions: It will probably be cold next week",
        ],
        topics="plans, predictions, problem-solving, job interviews",
    ),
    14: DifficultyLevel(
        level=14, label="Intermediate 2", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=15, exchanges=7,
        grammar=[
            "second conditional: If I had more time, I would travel more",
            "I wish + past simple: I wish I had a car, I wish it were summer",
            "I'd rather / would prefer: I'd rather stay home, I'd prefer coffee",
        ],
        topics="hypothetical situations, dreams, imaginary scenarios",
    ),
    15: DifficultyLevel(
        level=15, label="Intermediate 3", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=16, exchanges=8,
        grammar=[
            "contrast connectors: however, although, despite, on the other hand",
            "addition connectors: moreover, in addition, furthermore, what is more",
            "result connectors: therefore, as a result, consequently",
        ],
        topics="culture, traditions, describing experiences in detail, news topics",
    ),

    # ── Intermediate (B2) ─────────────────────────────
    16: DifficultyLevel(
        level=16, label="Upper-Intermediate 1", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=8,
        grammar=[
            "passive voice present/past: is made, was built, has been found",
            "passive voice future/modal: will be done, can be seen, must be finished",
            "reported speech: said that, told me, asked if, wanted to know",
        ],
        topics="society, technology, environment, debating issues",
    ),
    17: DifficultyLevel(
        level=17, label="Upper-Intermediate 2", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=9,
        grammar=[
            "third conditional: If I had studied more, I would have passed",
            "mixed conditionals: If I had taken that job, I would be richer now",
            "I wish + past perfect: I wish I had listened, If only I had known",
        ],
        topics="regrets, past decisions, alternative histories, lessons learned",
    ),
    18: DifficultyLevel(
        level=18, label="Upper-Intermediate 3", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=9,
        grammar=[
            "defining relative clauses: the man who called, the city where I grew up",
            "non-defining relative clauses: My sister, who lives abroad, ... (with commas)",
            "participle clauses: Having finished the work, he left / Not knowing what to do, she asked",
        ],
        topics="work, negotiations, conflict resolution, professional scenarios",
    ),
    19: DifficultyLevel(
        level=19, label="Upper-Intermediate 4", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=10,
        grammar=[
            "deduction with must have / can't have: He must have forgotten, She can't have arrived yet",
            "possibility with could have / might have: It could have been worse, She might have misunderstood",
            "hedging and softening: I tend to think, It would seem, arguably, to some extent",
        ],
        topics="philosophy, ethics, speculating about the past, cultural differences",
    ),
    20: DifficultyLevel(
        level=20, label="Upper-Intermediate 5", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=22, exchanges=10,
        grammar=[
            "common idioms: break the ice, hit the nail on the head, bite the bullet",
            "colloquial vs formal: get in touch / contact, find out / ascertain, go up / rise",
            "formal register: It is worth noting..., This suggests that..., In light of this...",
        ],
        topics="any topic, debate format, persuasive arguments, complex opinions",
    ),

    # ── Advanced (C1–C2) ──────────────────────────────
    21: DifficultyLevel(
        level=21, label="Advanced 1", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=10,
        grammar=[
            "negative inversion: Never have I seen..., Not only did she..., Rarely do we...",
            "cleft sentences: It was John who called, What I need is..., The thing that bothers me is...",
            "fronting for emphasis: What surprised me most was..., The one thing I regret is...",
        ],
        topics="abstract topics, academic discussions, professional scenarios",
    ),
    22: DifficultyLevel(
        level=22, label="Advanced 2", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=11,
        grammar=[
            "nominalization: the expansion of → expanding, failure to achieve → failing to achieve",
            "advanced collocations: make a concession, draw a distinction, reach a compromise",
            "idiomatic verb phrases: go through the motions, come to terms with, get around to",
        ],
        topics="British vs American English, humor, cultural nuances, social commentary",
    ),
    23: DifficultyLevel(
        level=23, label="Advanced 3", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=28, exchanges=11,
        grammar=[
            "ellipsis and substitution: I will if you will, She said she would and she did",
            "proverbs and sayings: Actions speak louder than words; Every cloud has a silver lining",
            "slang and informal registers: gut feeling, off the top of my head, touch and go",
        ],
        topics="current events analysis, in-depth cultural topics, personal anecdotes",
    ),
    24: DifficultyLevel(
        level=24, label="Mastery 1", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12,
        grammar=[
            "rhetorical devices: anaphora, antithesis, hyperbole, understatement, litotes",
            "register switching: casual → academic → formal → literary across a single topic",
            "wordplay and ambiguity: puns, double entendres, irony, sarcasm",
        ],
        topics="any topic at native level, spontaneous conversation, storytelling",
    ),
    25: DifficultyLevel(
        level=25, label="Mastery 2", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12,
        grammar=[
            "literary and poetic forms: metaphor, allusion, stream of consciousness",
            "dialectal and cultural nuance: British vs American usage, regional expressions",
            "subtle semantic distinctions: imply vs infer, affect vs effect, disinterested vs uninterested",
        ],
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
