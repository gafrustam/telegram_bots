import asyncio
import base64
import json
import os
import tempfile
from pathlib import Path

from openai import AsyncOpenAI
from pydub import AudioSegment

from difficulty import DifficultyLevel

PROMPTS_DIR = Path(__file__).parent / "prompts"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _load_prompt(filename: str, **kwargs: str) -> str:
    template = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return template.format(**kwargs)


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


def _convert_ogg_to_mp3(ogg_path: str, mp3_path: str) -> None:
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(mp3_path, format="mp3", bitrate="64k")


def _encode_mp3(mp3_path: str) -> str:
    with open(mp3_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── Scenario generation ─────────────────────────────────

async def generate_scenario(level: DifficultyLevel) -> dict:
    """Generate a conversation scenario with vocabulary for the given level."""
    system_prompt = _load_prompt(
        "generate_scenario.txt",
        level=str(level.level),
        label=level.label,
        cefr=level.cefr,
        grammar=level.grammar,
        topics=level.topics,
        max_sentence_words=str(level.max_sentence_words),
        vocab_count=str(level.vocab_count),
        construction_count=str(level.construction_count),
    )

    client = _get_client()
    text_model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")

    response = await client.chat.completions.create(
        model=text_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate a scenario."},
        ],
    )

    return _parse_json(response.choices[0].message.content)


# ── Conversation reply ──────────────────────────────────

async def get_conversation_reply(
    history: list[dict], level: DifficultyLevel,
    scenario: str, exchanges_left: int,
) -> str:
    """Get the bot's next reply in the conversation."""
    system_prompt = _load_prompt(
        "conversation.txt",
        level=str(level.level),
        label=level.label,
        cefr=level.cefr,
        grammar=level.grammar,
        max_sentence_words=str(level.max_sentence_words),
        scenario=scenario,
        exchanges_left=str(exchanges_left),
    )

    client = _get_client()
    text_model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")

    messages = [{"role": "system", "content": system_prompt}] + history

    response = await client.chat.completions.create(
        model=text_model,
        messages=messages,
    )

    return response.choices[0].message.content.strip()


# ── Whisper transcription ───────────────────────────────

async def transcribe_voice(ogg_data: bytes) -> str:
    """Transcribe voice message using Whisper API."""
    client = _get_client()

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(ogg_data)
        f.flush()
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es",
            )
        return transcript.text
    finally:
        os.unlink(tmp_path)


# ── Full conversation assessment ────────────────────────

async def assess_conversation(
    ogg_paths: list[str],
    history: list[dict],
    level: DifficultyLevel,
    scenario: str,
    exchange_count: int,
) -> dict:
    """Assess all user audio from the conversation using gpt-4o-audio-preview."""
    system_prompt = _load_prompt(
        "assess.txt",
        level=str(level.level),
        label=level.label,
        cefr=level.cefr,
        grammar=level.grammar,
        scenario=scenario,
        exchange_count=str(exchange_count),
    )

    # Build content: transcript context + user audio files
    content_parts: list[dict] = []

    # Add conversation transcript for context
    transcript_lines = []
    for msg in history:
        role_label = "Bot" if msg["role"] == "assistant" else "Student"
        transcript_lines.append(f"{role_label}: {msg['content']}")
    transcript_text = "\n".join(transcript_lines)

    content_parts.append({
        "type": "text",
        "text": f"Conversation transcript:\n{transcript_text}\n\nNow here are the student's audio recordings:",
    })

    # Add user audio files
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, ogg_path in enumerate(ogg_paths):
            mp3_path = os.path.join(tmp_dir, f"user_{i}.mp3")
            await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)
            audio_b64 = _encode_mp3(mp3_path)

            content_parts.append({
                "type": "text",
                "text": f"Student audio {i + 1}:",
            })
            content_parts.append({
                "type": "input_audio",
                "input_audio": {"data": audio_b64, "format": "mp3"},
            })

    content_parts.append({
        "type": "text",
        "text": "Now assess the student's overall performance across all their audio responses.",
    })

    client = _get_client()
    audio_model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")

    response = await client.chat.completions.create(
        model=audio_model,
        modalities=["text"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts},
        ],
    )

    raw = response.choices[0].message.content
    return _parse_json(raw)
