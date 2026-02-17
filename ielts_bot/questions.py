import json
import logging
import os
from pathlib import Path

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "generate_questions.txt"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
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
    """Generate a topic and questions for the given IELTS Speaking part.

    Args:
        part: 1, 2, or 3.
        topic: If provided, generate questions for this specific topic.
        cue_card_template: For Part 2, a cue card template from the topic bank.
        related_topic: For Part 3, the Part 2 topic to relate questions to.

    Returns:
        dict with keys:
            - "topic": str
            - "questions": list[str]  (Parts 1 & 3)
            - "cue_card": str         (Part 2)
    """
    client = _get_client()
    system_prompt = _load_prompt()
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")

    user_msg = f"Generate questions for IELTS Speaking Part {part}."

    if topic:
        user_msg += f"\nTopic: {topic}"

    if part == 2 and cue_card_template:
        user_msg += f"\n\nUse this cue card template as a basis (you may slightly vary the specific subject while keeping the same structure):\n{cue_card_template}"

    if part == 3 and related_topic:
        user_msg += f"\n\nIMPORTANT: The questions must be thematically related to this Part 2 topic: \"{related_topic}\". Generate abstract/analytical discussion questions that explore broader themes connected to this topic."

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=1.0,
    )

    raw = response.choices[0].message.content
    return _parse_json(raw)
