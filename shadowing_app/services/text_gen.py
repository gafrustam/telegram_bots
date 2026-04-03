import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

LEVEL_DESCRIPTIONS = {
    "A1": (
        "A1 Beginner level. Use only the 300-500 most common English words. "
        "Simple present tense only. Very short sentences (5-8 words each). "
        "Topics: family, home, daily routine, food, colors, simple descriptions."
    ),
    "A2": (
        "A2 Elementary level. Common vocabulary (up to 1,500 words). "
        "Simple past and near-future tenses. Short sentences (8-12 words). "
        "Topics: shopping, travel, work, weather, hobbies, simple stories."
    ),
    "B1": (
        "B1 Intermediate level. Standard vocabulary (up to 2,500 words). "
        "Perfect tenses, conditionals, modal verbs, comparatives. Medium-length sentences. "
        "Topics: personal experiences, travel, culture, technology basics, opinions."
    ),
    "B2": (
        "B2 Upper-Intermediate level. Wide vocabulary range including some idioms. "
        "Complex sentences, passive voice, relative clauses, reported speech. "
        "Topics: social issues, science, arts, environment, current events, debate."
    ),
    "C1": (
        "C1 Advanced level. Sophisticated vocabulary including collocations, phrasal verbs, and idioms. "
        "Complex grammatical structures, nuanced meaning, varied sentence patterns. "
        "Topics: abstract concepts, global issues, psychology, philosophy, specialized fields."
    ),
    "C2": (
        "C2 Mastery level. Near-native vocabulary with rare words, subtle connotations, and cultural references. "
        "Highly sophisticated, varied grammar. Eloquent, precise expression. "
        "Topics: any intellectually challenging subject — ethics, politics, science, literature."
    ),
}

_GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_openai_client: AsyncOpenAI | None = None
_google_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _openai_client, _google_client
    if os.getenv("AI_PROVIDER", "openai").lower() == "google":
        if _google_client is None:
            _google_client = AsyncOpenAI(
                api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
                base_url=_GOOGLE_BASE_URL,
            )
        return _google_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _openai_client


def _get_model() -> str:
    if os.getenv("AI_PROVIDER", "openai").lower() == "google":
        return os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.5-flash")
    return os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")


async def generate_passage(level: str, word_count: int) -> str:
    """Generate a natural English passage for shadowing at the given CEFR level."""
    model = _get_model()
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["C1"])

    prompt = (
        f"Generate a natural English passage for shadowing (listening-and-repeating) practice.\n\n"
        f"Level: {level_desc}\n\n"
        f"Requirements:\n"
        f"- Target: approximately {word_count} words (±10%)\n"
        f"- One continuous paragraph — NO bullet points, NO headers, NO lists\n"
        f"- Write as natural flowing speech that sounds great when read aloud\n"
        f"- Choose an engaging, relatable topic: travel, culture, food, human behavior, "
        f"technology, nature, fascinating facts, or everyday life\n"
        f"- Vary sentence length naturally for good rhythm\n"
        f"- Avoid tongue twisters or awkward consonant clusters\n"
        f"- The text must feel like something a native speaker would naturally say in conversation\n\n"
        f"Return ONLY the passage text. No title, no introduction, no quotes, no explanation."
    )

    logger.info("Generating passage level=%s word_count=%d provider=%s model=%s",
                level, word_count, provider, model)

    client = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    text = response.choices[0].message.content.strip()
    logger.info("Generated passage word_count_actual=%d", len(text.split()))
    return text
