import asyncio
import json
import logging
import os
from pathlib import Path

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "generate_questions.txt"

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


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
    user_id: int | None = None,
) -> dict:
    """Generate a topic and questions for the given IELTS Speaking part."""
    system_prompt = _load_prompt()

    user_msg = f"Generate questions for IELTS Speaking Part {part}."
    if topic:
        user_msg += f"\nTopic: {topic}"
    if part == 2 and cue_card_template:
        user_msg += f"\n\nUse this cue card template as a basis (you may slightly vary the specific subject while keeping the same structure):\n{cue_card_template}"
    if part == 3 and related_topic:
        user_msg += f"\n\nIMPORTANT: The questions must be thematically related to this Part 2 topic: \"{related_topic}\". Generate abstract/analytical discussion questions that explore broader themes connected to this topic."

    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    logger.info("%sgenerating part%d questions via provider=%s", uid_tag, part, provider)
    try:
        if provider == "google":
            result = await _generate_session_google(system_prompt, user_msg)
        else:
            result = await _generate_session_openai(system_prompt, user_msg)
        logger.info("%spart%d questions generated OK", uid_tag, part)
        return result
    except Exception as e:
        logger.error("%spart%d question generation failed [provider=%s]: %s", uid_tag, part, provider, e)
        raise


async def _generate_session_openai(system_prompt: str, user_msg: str) -> dict:
    client = _get_openai_client()
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=1.0,
    )
    return _parse_json(response.choices[0].message.content)


async def _generate_session_google(system_prompt: str, user_msg: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.0-flash")
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name,
        contents=user_msg,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=1.0,
        ),
    )
    return _parse_json(response.text)
