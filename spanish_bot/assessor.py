import asyncio
import base64
import json
import logging
import os
import tempfile
from pathlib import Path

from openai import AsyncOpenAI
from pydub import AudioSegment

from difficulty import DifficultyLevel

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


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

async def generate_scenario(level: DifficultyLevel, user_id: int | None = None) -> dict:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    system_prompt = _load_prompt(
        "generate_scenario.txt",
        level=str(level.level), label=level.label, cefr=level.cefr,
        grammar=level.grammar, topics=level.topics,
        max_sentence_words=str(level.max_sentence_words),
        vocab_count=str(level.vocab_count),
        construction_count=str(level.construction_count),
    )
    logger.info("%sgenerating scenario level=%d via provider=%s", uid_tag, level.level, provider)
    try:
        if provider == "google":
            result = await _generate_text_google(system_prompt, "Generate a scenario.")
        else:
            result = await _generate_text_openai(system_prompt, "Generate a scenario.")
        logger.info("%sscenario generated OK", uid_tag)
        return result
    except Exception as e:
        logger.error("%sscenario generation failed [provider=%s]: %s", uid_tag, provider, e)
        raise


# ── Conversation reply ──────────────────────────────────

async def get_conversation_reply(
    history: list[dict], level: DifficultyLevel,
    scenario: str, exchanges_left: int, user_id: int | None = None,
) -> str:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    system_prompt = _load_prompt(
        "conversation.txt",
        level=str(level.level), label=level.label, cefr=level.cefr,
        grammar=level.grammar, max_sentence_words=str(level.max_sentence_words),
        scenario=scenario, exchanges_left=str(exchanges_left),
    )
    logger.info("%sconversation reply via provider=%s exchanges_left=%d", uid_tag, provider, exchanges_left)
    try:
        if provider == "google":
            result = await _conversation_reply_google(system_prompt, history)
        else:
            result = await _conversation_reply_openai(system_prompt, history)
        logger.info("%sconversation reply OK", uid_tag)
        return result
    except Exception as e:
        logger.error("%sconversation reply failed [provider=%s]: %s", uid_tag, provider, e)
        raise


async def _generate_text_openai(system_prompt: str, user_msg: str) -> dict:
    client = _get_openai_client()
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    return _parse_json(response.choices[0].message.content)


async def _generate_text_google(system_prompt: str, user_msg: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.0-flash")
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name, contents=user_msg,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return _parse_json(response.text)


async def _conversation_reply_openai(system_prompt: str, history: list[dict]) -> str:
    client = _get_openai_client()
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
    messages = [{"role": "system", "content": system_prompt}] + history
    response = await client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content.strip()


async def _conversation_reply_google(system_prompt: str, history: list[dict]) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.0-flash")

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name, contents=contents,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text.strip()


# ── Whisper / Gemini transcription ──────────────────────

async def transcribe_voice(ogg_data: bytes, user_id: int | None = None) -> str:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    logger.info("%stranscribing voice via provider=%s bytes=%d", uid_tag, provider, len(ogg_data))
    try:
        if provider == "google":
            result = await _transcribe_voice_google(ogg_data)
        else:
            result = await _transcribe_voice_openai(ogg_data)
        logger.info("%stranscription OK text_len=%d", uid_tag, len(result))
        return result
    except Exception as e:
        logger.error("%stranscription failed [provider=%s]: %s", uid_tag, provider, e)
        raise


async def _transcribe_voice_openai(ogg_data: bytes) -> str:
    client = _get_openai_client()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(ogg_data)
        f.flush()
        tmp_path = f.name
    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, language="es",
            )
        return transcript.text
    finally:
        os.unlink(tmp_path)


async def _transcribe_voice_google(ogg_data: bytes) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.0-flash")
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name,
        contents=[
            types.Part.from_bytes(data=ogg_data, mime_type="audio/ogg"),
            types.Part.from_text(text="Transcribe the speech in this audio. Return only the transcribed text, nothing else."),
        ],
    )
    return response.text.strip()


# ── Full conversation assessment ────────────────────────

async def assess_conversation(
    ogg_paths: list[str], history: list[dict],
    level: DifficultyLevel, scenario: str,
    exchange_count: int, user_id: int | None = None,
) -> dict:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    system_prompt = _load_prompt(
        "assess.txt",
        level=str(level.level), label=level.label, cefr=level.cefr,
        grammar=level.grammar, scenario=scenario, exchange_count=str(exchange_count),
    )
    transcript_lines = []
    for msg in history:
        role_label = "Bot" if msg["role"] == "assistant" else "Student"
        transcript_lines.append(f"{role_label}: {msg['content']}")
    transcript_text = "\n".join(transcript_lines)

    logger.info("%sassessing conversation via provider=%s n_audio=%d exchanges=%d", uid_tag, provider, len(ogg_paths), exchange_count)
    try:
        if provider == "google":
            result = await _assess_conversation_google(ogg_paths, system_prompt, transcript_text)
        else:
            result = await _assess_conversation_openai(ogg_paths, system_prompt, transcript_text)
        logger.info("%sconversation assessment OK", uid_tag)
        return result
    except Exception as e:
        logger.error("%sconversation assessment failed [provider=%s]: %s", uid_tag, provider, e)
        raise


async def _assess_conversation_openai(
    ogg_paths: list[str], system_prompt: str, transcript_text: str,
) -> dict:
    content_parts: list[dict] = [{
        "type": "text",
        "text": f"Conversation transcript:\n{transcript_text}\n\nNow here are the student's audio recordings:",
    }]
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, ogg_path in enumerate(ogg_paths):
            mp3_path = os.path.join(tmp_dir, f"user_{i}.mp3")
            await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)
            audio_b64 = _encode_mp3(mp3_path)
            content_parts.append({"type": "text", "text": f"Student audio {i + 1}:"})
            content_parts.append({"type": "input_audio", "input_audio": {"data": audio_b64, "format": "mp3"}})
    content_parts.append({"type": "text", "text": "Now assess the student's overall performance across all their audio responses."})

    client = _get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")
    response = await client.chat.completions.create(
        model=model, modalities=["text"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts},
        ],
    )
    return _parse_json(response.choices[0].message.content)


async def _assess_conversation_google(
    ogg_paths: list[str], system_prompt: str, transcript_text: str,
) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.0-flash")

    content_parts: list = [
        types.Part.from_text(text=f"Conversation transcript:\n{transcript_text}\n\nNow here are the student's audio recordings:"),
    ]
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, ogg_path in enumerate(ogg_paths):
            mp3_path = os.path.join(tmp_dir, f"user_{i}.mp3")
            await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)
            content_parts.append(types.Part.from_text(text=f"Student audio {i + 1}:"))
            with open(mp3_path, "rb") as f:
                audio_bytes = f.read()
            content_parts.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"))
    content_parts.append(types.Part.from_text(text="Now assess the student's overall performance across all their audio responses."))

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name, contents=content_parts,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return _parse_json(response.text)
