import asyncio
import base64
import json
import logging
import os
import tempfile
from pathlib import Path

from openai import AsyncOpenAI
from pydub import AudioSegment

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _load_base_descriptors() -> str:
    return (PROMPTS_DIR / "base_descriptors.txt").read_text(encoding="utf-8")


def _load_prompt(filename: str, **kwargs: str) -> str:
    template = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    base = _load_base_descriptors()
    return template.format(base_descriptors=base, **kwargs)


def _convert_ogg_to_mp3(ogg_path: str, mp3_path: str) -> None:
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(mp3_path, format="mp3", bitrate="64k")


def _convert_ogg_to_mp3_trimmed(ogg_path: str, mp3_path: str, max_ms: int) -> None:
    audio = AudioSegment.from_ogg(ogg_path)
    if len(audio) > max_ms:
        audio = audio[:max_ms]
    audio.export(mp3_path, format="mp3", bitrate="64k")


def _get_duration_seconds(ogg_path: str) -> float:
    audio = AudioSegment.from_ogg(ogg_path)
    return len(audio) / 1000.0


def _encode_mp3(mp3_path: str) -> str:
    with open(mp3_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


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


def _format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


async def assess_part1(
    ogg_paths: list[str], questions: list[str], topic: str,
    durations: list[int] | None = None, user_id: int | None = None,
) -> dict:
    return await _assess_multi_audio(
        ogg_paths, questions, topic,
        prompt_file="assess_part1.txt",
        n_questions=len(questions),
        durations=durations,
        user_id=user_id,
    )


async def assess_part3(
    ogg_paths: list[str], questions: list[str], topic: str,
    durations: list[int] | None = None, user_id: int | None = None,
) -> dict:
    return await _assess_multi_audio(
        ogg_paths, questions, topic,
        prompt_file="assess_part3.txt",
        n_questions=len(questions),
        durations=durations,
        user_id=user_id,
    )


async def _assess_multi_audio(
    ogg_paths: list[str],
    questions: list[str],
    topic: str,
    prompt_file: str,
    n_questions: int,
    durations: list[int] | None = None,
    user_id: int | None = None,
) -> dict:
    questions_list = "\n".join(f"  {i + 1}. {q}" for i, q in enumerate(questions))
    system_prompt = _load_prompt(
        prompt_file, topic=topic,
        n_questions=str(n_questions), questions_list=questions_list,
    )

    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    part = "1" if "part1" in prompt_file else "3"
    logger.info("%sassessing part%s topic=%r via provider=%s n_audio=%d", uid_tag, part, topic, provider, len(ogg_paths))
    try:
        if provider == "google":
            result = await _assess_multi_audio_google(ogg_paths, questions, system_prompt, durations)
        else:
            result = await _assess_multi_audio_openai(ogg_paths, questions, system_prompt, durations)
        logger.info("%spart%s assessment OK band=%.1f", uid_tag, part, result.get("overall_band", 0))
        return result
    except Exception as e:
        logger.error("%spart%s assessment failed [provider=%s]: %s", uid_tag, part, provider, e)
        raise


async def _assess_multi_audio_openai(
    ogg_paths: list[str], questions: list[str],
    system_prompt: str, durations: list[int] | None,
) -> dict:
    content_parts: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, (ogg_path, question) in enumerate(zip(ogg_paths, questions)):
            mp3_path = os.path.join(tmp_dir, f"response_{i}.mp3")
            await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)
            audio_b64 = _encode_mp3(mp3_path)
            dur_info = f" (duration: {durations[i]} seconds)" if durations and i < len(durations) else ""
            content_parts.append({"type": "text", "text": f"Question {i + 1}: {question}{dur_info}"})
            content_parts.append({"type": "input_audio", "input_audio": {"data": audio_b64, "format": "mp3"}})
    content_parts.append({"type": "text", "text": "Now assess the overall performance across all responses above."})

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


async def _assess_multi_audio_google(
    ogg_paths: list[str], questions: list[str],
    system_prompt: str, durations: list[int] | None,
) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.0-flash")

    content_parts: list = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, (ogg_path, question) in enumerate(zip(ogg_paths, questions)):
            mp3_path = os.path.join(tmp_dir, f"response_{i}.mp3")
            await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)
            dur_info = f" (duration: {durations[i]} seconds)" if durations and i < len(durations) else ""
            content_parts.append(types.Part.from_text(text=f"Question {i + 1}: {question}{dur_info}"))
            with open(mp3_path, "rb") as f:
                audio_bytes = f.read()
            content_parts.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"))
    content_parts.append(types.Part.from_text(text="Now assess the overall performance across all responses above."))

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name, contents=content_parts,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return _parse_json(response.text)


async def assess_part2(
    ogg_path: str, cue_card: str, duration_seconds: float,
    user_id: int | None = None,
) -> dict:
    system_prompt = _load_prompt(
        "assess_part2.txt", cue_card=cue_card,
        duration_seconds=str(round(duration_seconds)),
        duration_display=_format_duration(duration_seconds),
    )

    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    logger.info("%sassessing part2 duration=%.1fs via provider=%s", uid_tag, duration_seconds, provider)
    try:
        if provider == "google":
            result = await _assess_part2_google(ogg_path, system_prompt)
        else:
            result = await _assess_part2_openai(ogg_path, system_prompt)
        logger.info("%spart2 assessment OK band=%.1f", uid_tag, result.get("overall_band", 0))
        return result
    except Exception as e:
        logger.error("%spart2 assessment failed [provider=%s]: %s", uid_tag, provider, e)
        raise


async def _assess_part2_openai(ogg_path: str, system_prompt: str) -> dict:
    max_ms = 120_000
    with tempfile.TemporaryDirectory() as tmp_dir:
        mp3_path = os.path.join(tmp_dir, "response.mp3")
        await asyncio.to_thread(_convert_ogg_to_mp3_trimmed, ogg_path, mp3_path, max_ms)
        audio_b64 = _encode_mp3(mp3_path)

    client = _get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")
    response = await client.chat.completions.create(
        model=model, modalities=["text"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "input_audio", "input_audio": {"data": audio_b64, "format": "mp3"}},
                {"type": "text", "text": "Assess this Part 2 Long Turn response."},
            ]},
        ],
    )
    return _parse_json(response.choices[0].message.content)


async def _assess_part2_google(ogg_path: str, system_prompt: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.0-flash")

    max_ms = 120_000
    with tempfile.TemporaryDirectory() as tmp_dir:
        mp3_path = os.path.join(tmp_dir, "response.mp3")
        await asyncio.to_thread(_convert_ogg_to_mp3_trimmed, ogg_path, mp3_path, max_ms)
        with open(mp3_path, "rb") as f:
            audio_bytes = f.read()

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"),
            types.Part.from_text(text="Assess this Part 2 Long Turn response."),
        ],
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return _parse_json(response.text)
