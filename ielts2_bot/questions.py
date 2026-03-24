import logging
import os
from pathlib import Path

from openai import AsyncOpenAI
import json

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "generate_questions.txt"

_openai_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise


async def generate_session(
    part: int,
    topic: str | None = None,
    cue_card_template: str | None = None,
    related_topic: str | None = None,
) -> dict:
    """Generate a topic + questions/cue_card for the given IELTS Speaking part."""
    system_prompt = _load_prompt()

    user_msg = f"Generate questions for IELTS Speaking Part {part}."
    if topic:
        user_msg += f"\nTopic: {topic}"
    if part == 2 and cue_card_template:
        user_msg += (
            f"\n\nUse this cue card template as a basis (you may slightly vary the specific "
            f"subject while keeping the same structure):\n{cue_card_template}"
        )
    if part == 3 and related_topic:
        user_msg += (
            f'\n\nIMPORTANT: The questions must be thematically related to this Part 2 topic: '
            f'"{related_topic}". Generate abstract/analytical discussion questions that explore '
            f'broader themes connected to this topic.'
        )

    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
    logger.info("Generating part%d questions via OpenAI (%s)", part, model)

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=1.0,
        )
        result = _parse_json(response.choices[0].message.content)
        logger.info("Part%d questions generated OK", part)
        return result
    except Exception as e:
        logger.error("Part%d question generation failed: %s", part, e)
        raise
