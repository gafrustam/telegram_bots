"""25 difficulty levels for Spanish conversation practice."""

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
        level=1, label="Principiante 1", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=4, exchanges=2,
        grammar=[
            "Me llamo..., Soy... (auto-presentación)",
            "Saludos: hola, buenos días, buenas tardes, adiós, ¿cómo te llamas?",
            "Respuestas sí/no, números 1-10",
        ],
        topics="saying hello, saying your name, goodbye",
    ),
    2: DifficultyLevel(
        level=2, label="Principiante 2", cefr="A0",
        vocab_count=5, construction_count=2, max_sentence_words=5, exchanges=2,
        grammar=[
            "ser: yo soy, tú eres, él/ella es (presentaciones y origen)",
            "artículos: el, la, los, las, un, una, unos, unas",
            "adjetivos básicos: grande, pequeño, viejo, nuevo, bonito, feo (concordancia)",
        ],
        topics="family members, colors, simple descriptions",
    ),
    3: DifficultyLevel(
        level=3, label="Principiante 3", cefr="A1",
        vocab_count=5, construction_count=2, max_sentence_words=6, exchanges=3,
        grammar=[
            "verbos -ar regulares: hablar, estudiar, trabajar, caminar (presente)",
            "verbos -ar preguntas: ¿Hablas inglés? ¿Trabajas aquí?",
            "concordancia de género y número: el chico alto, la chica alta, los niños altos",
        ],
        topics="daily activities, food basics, simple likes",
    ),
    4: DifficultyLevel(
        level=4, label="Principiante 4", cefr="A1",
        vocab_count=6, construction_count=2, max_sentence_words=7, exchanges=3,
        grammar=[
            "verbos -er/-ir regulares: comer, beber, vivir, escribir (presente)",
            "tener y querer: tengo hambre, quiero café, ¿tienes...?",
            "hay + sustantivo: hay un gato, hay muchos libros, no hay nada",
        ],
        topics="home, pets, school, what I have",
    ),
    5: DifficultyLevel(
        level=5, label="Principiante 5", cefr="A1",
        vocab_count=6, construction_count=3, max_sentence_words=7, exchanges=3,
        grammar=[
            "verbos irregulares comunes: ir (voy, vas, va), venir, hacer (hago, haces)",
            "gustar + sustantivo: me gusta el café, me gustan las películas",
            "gustar + infinitivo: me gusta bailar, no me gusta madrugar",
        ],
        topics="hobbies, weekend, likes and dislikes, weather basics",
    ),

    # ── Elementary (A2) ────────────────────────────────
    6: DifficultyLevel(
        level=6, label="Elemental 1", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=9, exchanges=4,
        grammar=[
            "presente progresivo: estoy hablando, está comiendo, estamos trabajando",
            "futuro próximo: voy a llamar, ¿vas a venir?, no va a llover",
            "contraste presente simple vs progresivo: vivo aquí / estoy viviendo aquí",
        ],
        topics="what I'm doing now, plans for today, simple routines",
    ),
    7: DifficultyLevel(
        level=7, label="Elemental 2", cefr="A2",
        vocab_count=6, construction_count=3, max_sentence_words=10, exchanges=4,
        grammar=[
            "pretérito indefinido regular: hablar → hablé/hablaste, comer → comí/comiste",
            "pretérito preguntas y negaciones: ¿Llegaste a tiempo? No comí nada",
            "verbos reflexivos: levantarse, acostarse, ducharse, llamarse",
        ],
        topics="yesterday, last weekend, morning routine",
    ),
    8: DifficultyLevel(
        level=8, label="Elemental 3", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=10, exchanges=5,
        grammar=[
            "pretérito irregular: ir/ser (fui, fuiste), hacer (hice, hiciste)",
            "pretérito irregular: tener (tuve), estar (estuve), poder (pude)",
            "expresiones de tiempo: ayer, la semana pasada, hace tres días, el año pasado",
        ],
        topics="vacations, travel stories, city descriptions",
    ),
    9: DifficultyLevel(
        level=9, label="Elemental 4", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=11, exchanges=5,
        grammar=[
            "imperfecto para hábitos: cuando era niño/a, siempre jugaba, todos los veranos íbamos",
            "imperfecto descriptivo: era alto, tenía el pelo largo, hacía frío",
            "comparativos: más alto que, menos caro que, tan bueno como",
        ],
        topics="childhood memories, comparing things, describing past habits",
    ),
    10: DifficultyLevel(
        level=10, label="Elemental 5", cefr="A2",
        vocab_count=7, construction_count=3, max_sentence_words=12, exchanges=5,
        grammar=[
            "pronombres de objeto directo: lo/la/los/las — ¿lo viste? la compré ayer",
            "imperativo tú afirmativo: ¡Habla!, ¡Come!, ¡Escribe!, ¡Ve!",
            "imperativo tú negativo: no hables, no comas, no escribas, no vayas",
        ],
        topics="restaurants, ordering food, giving simple directions",
    ),

    # ── Pre-Intermediate (B1) ──────────────────────────
    11: DifficultyLevel(
        level=11, label="Intermedio 1", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=6,
        grammar=[
            "subjuntivo con quiero que, espero que: quiero que vengas, espero que tengas éxito",
            "ojalá + subjuntivo: ojalá llueva, ojalá puedas venir mañana",
            "por vs para: por razón/causa (por eso, por el tráfico), para propósito/destino",
        ],
        topics="opinions, recommendations, hopes and wishes",
    ),
    12: DifficultyLevel(
        level=12, label="Intermedio 2", cefr="B1",
        vocab_count=7, construction_count=3, max_sentence_words=14, exchanges=7,
        grammar=[
            "subjuntivo con emoción: me alegra que, es una pena que, me sorprende que",
            "subjuntivo con duda: no creo que, dudo que, no estoy seguro de que",
            "condicional simple: hablaría, comería, ¿qué harías si tuvieras más tiempo?",
        ],
        topics="environment, news events, social issues",
    ),
    13: DifficultyLevel(
        level=13, label="Intermedio 3", cefr="B1",
        vocab_count=8, construction_count=3, max_sentence_words=15, exchanges=7,
        grammar=[
            "cláusulas si (presente): si tengo tiempo, iré; si llueve, nos quedamos en casa",
            "pronombres relativos: que (personas/cosas), quien (personas), donde (lugar)",
            "condicional para cortesía: ¿podría ayudarme? ¿me podría decir dónde está...?",
        ],
        topics="hypothetical situations, job interviews, future plans",
    ),
    14: DifficultyLevel(
        level=14, label="Intermedio 4", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=15, exchanges=7,
        grammar=[
            "pretérito perfecto: he comido, ¿has estado en...?, ella ha llegado ya",
            "pretérito pluscuamperfecto: había terminado, ya había visto esa película",
            "pronombres dobles: se lo doy, me lo dijeron, ¿se lo puedes dar a ella?",
        ],
        topics="life experiences, achievements, technology use",
    ),
    15: DifficultyLevel(
        level=15, label="Intermedio 5", cefr="B1",
        vocab_count=8, construction_count=4, max_sentence_words=16, exchanges=8,
        grammar=[
            "conectores de contraste: sin embargo, aunque, a pesar de, por otro lado",
            "conectores de adición: además, asimismo, incluso, por otra parte",
            "conectores de resultado: por lo tanto, así que, por eso, de modo que",
        ],
        topics="culture, traditions, describing experiences in detail",
    ),

    # ── Intermediate (B2) ─────────────────────────────
    16: DifficultyLevel(
        level=16, label="Avanzado 1", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=8,
        grammar=[
            "imperfecto de subjuntivo: quisiera, tuviera, pudiera — quería que fueras",
            "cláusulas si con pasado: si tuviera dinero, viajaría más",
            "voz pasiva: fue construido, es conocido, ha sido inaugurado",
        ],
        topics="politics, economics, debating social issues",
    ),
    17: DifficultyLevel(
        level=17, label="Avanzado 2", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=18, exchanges=9,
        grammar=[
            "subjuntivo imperfecto con ojalá: ojalá hubiera venido, ojalá lo supieras",
            "como si + subjuntivo: actuaba como si supiera todo, habla como si fuera jefe",
            "futuro perfecto: habrá terminado para entonces, ya habrán llegado",
        ],
        topics="literature, art, film discussions, reviews",
    ),
    18: DifficultyLevel(
        level=18, label="Avanzado 3", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=9,
        grammar=[
            "cláusulas si mixtas: si hubiera estudiado más, hablaría mejor ahora",
            "subjuntivo en cláusulas adjetivas: busco alguien que sepa cocinar",
            "subjuntivo en cláusulas adverbiales: cuando llegues, aunque no quieras, antes de que salga",
        ],
        topics="workplace dynamics, negotiation, conflict resolution",
    ),
    19: DifficultyLevel(
        level=19, label="Avanzado 4", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=20, exchanges=10,
        grammar=[
            "modismos comunes: tener mala leche, meter la pata, costar un ojo de la cara",
            "expresiones coloquiales: ¡Qué chulo!, ¿Qué pasa?, mola mucho, tío/tía",
            "registro formal vs informal: desearía / querría, solicitar / pedir, tenga en cuenta",
        ],
        topics="philosophy, ethics, cultural differences",
    ),
    20: DifficultyLevel(
        level=20, label="Avanzado 5", cefr="B2",
        vocab_count=8, construction_count=4, max_sentence_words=22, exchanges=10,
        grammar=[
            "registro académico y formal: en virtud de, cabe señalar que, con respecto a",
            "eufemismos y perífrasis: persona de la tercera edad, hacer sus necesidades",
            "locuciones verbales avanzadas: dar en el clavo, salirse con la suya, echar en falta",
        ],
        topics="any topic, debate format, persuasive arguments",
    ),

    # ── Advanced (C1–C2) ──────────────────────────────
    21: DifficultyLevel(
        level=21, label="Superior 1", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=10,
        grammar=[
            "subordinación compleja: habiendo terminado, siendo así las cosas, no bien llegué",
            "perífrasis verbales: llevar + gerundio, seguir + gerundio, volver a + infinitivo",
            "inversión y énfasis: Nunca lo habría creído, No fue él quien llamó sino...",
        ],
        topics="abstract topics, academic discussions, professional scenarios",
    ),
    22: DifficultyLevel(
        level=22, label="Superior 2", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=25, exchanges=11,
        grammar=[
            "voseo y variantes regionales: vos tenés, vos sos — uso en Argentina y Uruguay",
            "leísmo y laísmo: le dije vs lo dije — diferencias entre España y Latinoamérica",
            "modismos avanzados regionales: chévere (Caribe), guay (España), copado (Argentina)",
        ],
        topics="regional dialects, Latin American vs Spain culture, humor",
    ),
    23: DifficultyLevel(
        level=23, label="Superior 3", cefr="C1",
        vocab_count=8, construction_count=4, max_sentence_words=28, exchanges=11,
        grammar=[
            "refranes y proverbios: Más vale tarde que nunca, En boca cerrada no entran moscas",
            "jerga y lenguaje juvenil: molar, flipar, mogollón, pasarse de listo",
            "dobles sentidos y humor lingüístico: juegos de palabras, ironía, sobreentendidos",
        ],
        topics="current events analysis, in-depth cultural topics",
    ),
    24: DifficultyLevel(
        level=24, label="Superior 4", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12,
        grammar=[
            "recursos retóricos: anáfora, antítesis, hipérbole, litotes, perífrasis",
            "alternancia de registro: coloquial → periodístico → literario → académico",
            "juegos de palabras y ambigüedad: doble sentido, calambur, ironía sofisticada",
        ],
        topics="any topic at native level, spontaneous conversation",
    ),
    25: DifficultyLevel(
        level=25, label="Superior 5", cefr="C2",
        vocab_count=8, construction_count=4, max_sentence_words=30, exchanges=12,
        grammar=[
            "formas literarias y poéticas: metáfora extendida, aliteración, hipérbaton",
            "matices dialectales: castellano peninsular vs español de América, andaluz, canario",
            "sutilezas semánticas: implicar vs implicarse, connotar vs denotar, parecer vs parecerse",
        ],
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
