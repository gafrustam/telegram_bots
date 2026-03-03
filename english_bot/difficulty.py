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
            "this/that + noun: this is a pen, that is my bag",
            "basic question words: What? Who? Where?",
            "numbers 1-20 and ages: I am ten years old",
            "colors as adjectives: a red apple, a blue bag",
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
            "to be negative: I am not, he isn't, they aren't",
            "to be questions: Are you...? Is she...?",
            "possessives: my, your, his, her, its, our, their",
            "demonstratives: this, that, these, those",
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
            "present simple negatives: I don't like, I don't want",
            "object pronouns: me, you, him, her, it, us, them",
            "prepositions of place: in, on, under, next to, between",
            "frequency: every day, twice a week, on weekends",
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
            "possessive 's: John's car, my sister's friend",
            "prepositions of time: at 6pm, on Monday, in January",
            "countable vs uncountable: a bottle of water, some bread, many cars",
            "plural nouns: cats, buses, children, people, mice",
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
            "present continuous questions: Are you working? What are you doing?",
            "present continuous negatives: I'm not sleeping, she isn't coming",
            "very/quite/really + adjective: very cold, quite interesting",
            "would like: I'd like a coffee, Would you like to...?",
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
            "will for offers: I'll help you, Shall I carry that?",
            "telling time: It's half past, quarter to, five past",
            "prepositions of movement: to, from, up, down, across, through",
            "connectors: and, but, or, so, because",
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
            "ago: three days ago, two weeks ago, a long time ago",
            "when + past: When I was young, When she arrived...",
            "before/after + noun/V-ing: before lunch, after eating",
            "linking past events: first, then, next, after that, finally",
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
            "narrative linkers: suddenly, unfortunately, luckily, in the end",
            "both...and / neither...nor: both fast and easy",
            "how + adjective questions: How far? How long? How often?",
            "past continuous: was/were + -ing for background: I was reading when she called",
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
            "enough/too: old enough to drive, too cold to go out",
            "so/such: so interesting, such a good film",
            "not as...as: not as fast as, not as expensive as",
            "a bit / a lot + comparative: a bit faster, much more interesting",
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
            "might/may for possibility: It might rain, She may be late",
            "would rather vs prefer: I'd rather walk; I prefer tea to coffee",
            "prepositions after adjectives: good at, interested in, bored with, scared of",
            "verb patterns: enjoy + -ing, want + infinitive, avoid + -ing",
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
            "present perfect continuous: have been working, has been raining (duration)",
            "still/anymore: Is she still working here? He doesn't live here anymore",
            "been vs gone: She has been to Paris (returned) vs She has gone to Paris (still there)",
            "by the time: by the time I arrived, by the time you read this",
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
            "past perfect: I had already eaten when she called",
            "reported speech basic: She said she was tired. He told me to wait.",
            "make/let/help + object + infinitive: let me explain, make her laugh",
            "quantifiers: a few, a little, plenty of, a great deal of",
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
            "unless + present: unless it rains, unless you hurry up",
            "as soon as / when + future meaning: as soon as I arrive, when you finish",
            "be about to: I'm about to leave, she's about to call",
            "be likely to: It's likely to rain, She's likely to be late",
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
            "as if / as though: He talks as if he knows everything",
            "suppose/supposing: Suppose you could fly, what would you do?",
            "could/would/might in second conditional: If you practiced, you could improve",
            "whether or not: I'll go whether or not you come",
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
            "purpose clauses: in order to, so that, so as not to",
            "time clauses: while, as, when, after, before, until, as soon as",
            "cause connectors: because of, due to, owing to, as, since",
            "opinion phrases: In my view, From my perspective, As far as I'm concerned",
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
            "passive causative: have/get something done: I had my car repaired",
            "impersonal passive: It is said that..., It is believed that...",
            "complex reporting verbs: claim, admit, deny, suggest, warn, recommend",
            "modal passives: should be done, must be cleaned, might have been forgotten",
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
            "continuous third conditional: If I had been paying attention...",
            "otherwise/or else: You should study harder, otherwise you'll fail",
            "provided that / as long as / on condition that",
            "it's time / it's high time: It's time you studied. It's high time she decided.",
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
            "reduced relative clauses: the man standing there, the letter written yesterday",
            "abstract nominal clauses: The fact that..., The idea that..., The belief that...",
            "prepositions with relatives: the person with whom I spoke, the town in which I grew up",
            "cleft sentences: It was the book that I wanted. What I need is more practice.",
        ],
        topics="work, negotiations, conflict resolution, professional scenarios",
    ),
    19: DifficultyLevel(
        level=19, label="Upper-Intermediate 4", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=10,
        grammar=[
            "deduction with must have / can't have: He must have forgotten",
            "possibility with could have / might have: It could have been worse",
            "hedging and softening: I tend to think, It would seem, arguably, to some extent",
            "should have / ought to have: You should have called",
            "needn't have vs didn't need to: I needn't have bought milk (but I did)",
            "emphatic DO: I do agree with you. She does know what she's talking about.",
            "inversions for emphasis: Only when I read it did I understand.",
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
            "discourse markers: having said that, all things considered, needless to say",
            "euphemisms and understatement: pass away, a bit under the weather, not exactly brilliant",
            "phrasal verbs formal vs informal: look into vs investigate, put off vs postpone",
            "complex nominalization: the implementation of, the development of, an improvement in",
        ],
        topics="any topic, debate format, persuasive arguments, complex opinions",
    ),

    # ── Advanced (C1–C2) ──────────────────────────────
    21: DifficultyLevel(
        level=21, label="Advanced 1", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=10,
        grammar=[
            "negative inversion: Never have I seen..., Not only did she..., Rarely do we...",
            "cleft sentences: It was John who called, What I need is...",
            "fronting for emphasis: What surprised me most was..., The one thing I regret is...",
            "double inversion: No sooner had she left than..., Barely had he arrived when...",
            "abstract subjunctive: I suggest he be present. It is vital that she attend.",
            "concessive clauses: However hard I try, Whatever you say, Wherever he goes",
            "as...as constructions: as early as the 1900s, as recently as last year",
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
            "delexical verbs: make a decision, take a risk, give advice, have an impact",
            "complex prepositions: with regard to, in terms of, by means of, as opposed to",
            "subjunctive in formal/literary use: Were I to..., Had she known..., Should you require...",
            "rhetorical questions: What can we do? How could anyone disagree? Is this really necessary?",
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
            "conditional inversion: Were it not for..., Should you need help..., Had I known...",
            "discourse cohesion: the former/the latter, the above-mentioned, respectively",
            "stance adverbs: arguably, presumably, admittedly, frankly, interestingly",
            "subtle modal distinctions: will vs would for habits, shall for offers/suggestions",
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
            "pragmatic nuance: implicature, presupposition, face-threatening acts",
            "systemic cohesion: anaphoric/cataphoric reference, ellipsis chains",
            "metalinguistic commentary: strictly speaking, in the literal sense, loosely defined as",
            "complex aspect: I was going to have finished by now; She will have been waiting",
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
            "archaic or formal grammar: would that it were, methinks, 'tis — uses in literature",
            "modal complexity: must vs have to (logical vs deontic), can vs could (ability vs hypothetical)",
            "advanced hedging: it would not be unreasonable to suggest, to put it mildly",
            "word-formation: affixation, conversion, blending, back-formation, compounding",
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
