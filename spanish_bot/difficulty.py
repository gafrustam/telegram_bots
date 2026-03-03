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
            "pronombres personales: yo, tú, él/ella, nosotros, vosotros/ustedes, ellos",
            "¿Cómo estás? Bien, mal, más o menos, gracias, de nada",
            "números 1-20 y edades: tengo 20 años, ¿cuántos años tienes?",
            "colores básicos: rojo, azul, verde, amarillo, blanco, negro",
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
            "estar para estados: estoy cansado, está enfermo, estamos listos",
            "ser vs estar básico: soy alto (permanente) / estoy cansado (temporal)",
            "posesivos: mi, tu, su, nuestro, vuestro, su",
            "demostrativos: este, esta, estos, estas; ese, esa; aquel, aquella",
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
            "negación: no hablo francés, no trabajo los domingos",
            "pronombres de objeto: me, te, le, nos, os, les",
            "preposiciones de lugar: en, sobre, debajo de, al lado de, entre, delante de",
            "días y meses: el lunes, en enero, los fines de semana",
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
            "saber vs conocer: sé nadar (habilidad), conozco a María (persona/lugar)",
            "tener que + infinitivo: tengo que estudiar, ¿tienes que trabajar mañana?",
            "plurales: el gato → los gatos, la ciudad → las ciudades",
            "preposiciones de tiempo: a las tres, el lunes, en enero, por la mañana",
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
            "encantar/odiar/molestar: me encanta bailar, me molesta el ruido",
            "poder + infinitivo: puedo hablar, ¿puedes ayudarme?",
            "querer + infinitivo: quiero ir, ¿quieres venir?",
            "muy/bastante/un poco + adjetivo: muy rápido, bastante difícil, un poco aburrido",
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
            "acabar de + infinitivo: acabo de llegar, ella acaba de llamar",
            "seguir + gerundio: sigo estudiando, ¿sigues trabajando aquí?",
            "expresiones de frecuencia: siempre, normalmente, a veces, nunca, casi nunca",
            "conectores básicos: y, pero, o, porque, aunque",
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
            "ser vs estar en contextos más amplios: la fiesta es a las 8 / está en mi casa",
            "adverbios de tiempo pasado: ayer, la semana pasada, anteayer, el año pasado",
            "hace + tiempo + que + pretérito: hace dos días que llegué",
            "pronombres reflexivos en pasado: me lavé, te duchaste, nos peinamos",
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
            "imperfecto regular: hablaba, comía, vivía — forma y uso básico",
            "imperfecto de ser/ir/ver: era, iba, veía",
            "contraste pretérito/imperfecto básico: ayer comí (acción) / siempre comía (hábito)",
            "marcadores de imperfecto: cuando era pequeño, antes, siempre, todos los días",
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
            "superlativo: el más alto de, la menos cara de, el mejor de todos",
            "tan...como vs tanto como: tan rápido como yo, tanto como tú",
            "bastante/demasiado/suficiente: bastante caro, demasiado tarde, suficiente dinero",
            "pretérito + imperfecto narrativo: entré en la sala y había mucha gente",
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
            "pronombres de objeto indirecto: me dijo, te preguntó, le escribí",
            "imperativo usted: ¡Hable!, ¡Coma!, ¡Venga!, ¡No haga eso!",
            "imperativo nosotros: ¡Vamos!, ¡Hagamos algo!, ¡Comamos aquí!",
            "posición de pronombres con imperativo: dámelo, no me lo des",
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
            "subjuntivo con verbos de voluntad: necesito que..., pido que..., prefiero que...",
            "para que + subjuntivo: te lo explico para que lo entiendas",
            "aunque + subjuntivo vs indicativo: aunque llueva (hipotético) / aunque llueve (real)",
            "expresiones impersonales: es importante que, es necesario que, es posible que",
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
            "condicional con verbos modales: podría hacerlo, debería llamarla, querría ir",
            "ya que / puesto que / como causal: ya que estás aquí, como no tenía dinero",
            "llevar + gerundio: llevo tres horas esperando, llevaba meses sin verte",
            "imperfecto de subjuntivo básico: si tuviera, si pudiera, si fuera",
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
            "futuro de indicativo regular: hablaré, comerás, viviremos",
            "futuro de probabilidad: serán las 3, tendrá unos 40 años, estará en casa",
            "subjuntivo en cláusulas temporales: cuando llegues, hasta que termines, en cuanto puedas",
            "se impersonal: se dice que, se puede entrar, se habla español aquí",
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
            "seguir/continuar + gerundio vs dejar de + infinitivo: sigo trabajando / dejé de fumar",
            "volver a + infinitivo: volvió a llamar, ¿vas a volver a intentarlo?",
            "acabar de + infinitivo en pasado: acababa de salir cuando llamó",
            "haber que vs tener que: hay que estudiar (general) / tienes que estudiar (personal)",
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
            "conectores de causa: porque, ya que, puesto que, dado que, a causa de",
            "conectores concesivos: aunque, a pesar de que, pese a que, si bien",
            "conectores de finalidad: para, para que, a fin de, con el objetivo de",
            "marcadores del discurso: en primer lugar, a continuación, por último, en conclusión",
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
            "subjuntivo pluscuamperfecto: hubiera comido, si hubiera sabido...",
            "se pasivo vs se impersonal: se vendió la casa / se vende bien",
            "voz pasiva con ser + participio: fue inaugurado, serán elegidos",
            "concesivas con subjuntivo: por mucho que estudies, por más que intentes",
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
            "condicional perfecto: habría hecho, habrías podido, hubiera preferido",
            "si + pluscuamperfecto + condicional perfecto: si hubiera estudiado más, habría aprobado",
            "futuro de probabilidad en pasado: habrá llegado ya, ya habrán comido",
            "gerundio como condición: siendo así, teniendo en cuenta, contando con eso",
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
            "nominalización: el desarrollo de, el aumento de, la reducción de",
            "participio en construcciones absolutas: terminado el trabajo, llegada la primavera",
            "construcciones con de + infinitivo: de haberlo sabido, de ser posible, de no ser por ti",
            "relativos con preposición: la ciudad en la que nací, el hombre con quien hablé",
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
            "argot juvenil: flipar, molar, petarlo, ser un crack, pasarse de la raya",
            "variantes del español: Latinoamérica vs España (vos/tú, carro/coche, coger/tomar)",
            "eufemismos formales: persona en situación irregular, conflicto bélico, ajuste de plantilla",
            "frases hechas con cuerpo: costar un ojo, meter la pata, no tener pelos en la lengua",
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
            "perífrasis verbales complejas: estar a punto de, ponerse a + inf, echarse a + inf",
            "oraciones condicionales con inversión: de haber sabido, de no ser por...",
            "sintaxis de énfasis: es que..., lo que pasa es que..., el hecho es que...",
            "construcciones impersonales formales: cabe destacar que, conviene señalar que, es de suponer que",
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
            "usos avanzados del subjuntivo: quienquiera que sea, dondequiera que vaya, sea lo que sea",
            "construcciones con aunque + modo: aunque lo haga / aunque lo hace (diferencia pragmática)",
            "apócope y contracciones: del, al, primer, gran, cualquier — reglas y excepciones",
            "gerundio especificativo vs predicativo: vi a la mujer trabajando / trabajando aquí, aprendí",
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
            "español neutro vs variedades: medios internacionales vs habla cotidiana regional",
            "falsos cognados español-inglés: embarazada/embarrassed, éxito/exit, librería/library",
            "intensificadores y atenuadores: enormemente, en absoluto, ni mucho menos, cuanto menos",
            "construcciones con ser/estar de alta complejidad: está siendo construido, fue siendo reconocido",
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
            "construcciones literarias: lo + adjetivo (lo bello, lo difícil), así + subjuntivo",
            "discurso indirecto complejo: dijo que lo haría, preguntó si había llegado, pidió que fuéramos",
            "frases sentenciosas: la letra con sangre entra, el que persevera alcanza",
            "uso arcaico y literario: plugo, hubiste, habrás menester — usos en literatura clásica",
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
            "hipérbaton literario: De las almas el dolor, Yo que fui..., Tales las ansias",
            "construcciones perifrásticas complejas: vine a ser, alcancé a comprender",
            "referencias intertextuales: cervantismos, quijotismos, frases bíblicas en español",
            "pragmática avanzada: actos de habla indirectos, implicaturas, cortesía lingüística",
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
            "diacronía del español: latín vulgar → español medieval → Siglo de Oro → moderno",
            "gramática del texto: coherencia y cohesión, anáforas, catáforas, elipsis discursiva",
            "variación funcional: registro coloquial, culto, científico, jurídico, periodístico",
            "creatividad léxica: neologismos, anglicismos, calcos lingüísticos, palabras híbridas",
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
