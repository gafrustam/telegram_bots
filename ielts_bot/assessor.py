import asyncio
import base64
import json
import os
import tempfile
from pathlib import Path

from openai import AsyncOpenAI
from pydub import AudioSegment

PROMPTS_DIR = Path(__file__).parent / "prompts"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


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
    """Convert OGG to MP3, trimming to max_ms milliseconds."""
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


async def assess_part1(ogg_paths: list[str], questions: list[str], topic: str) -> dict:
    """Assess IELTS Speaking Part 1 with multiple Q&A pairs."""
    return await _assess_multi_audio(
        ogg_paths, questions, topic,
        prompt_file="assess_part1.txt",
        n_questions=len(questions),
    )


async def assess_part3(ogg_paths: list[str], questions: list[str], topic: str) -> dict:
    """Assess IELTS Speaking Part 3 with multiple Q&A pairs."""
    return await _assess_multi_audio(
        ogg_paths, questions, topic,
        prompt_file="assess_part3.txt",
        n_questions=len(questions),
    )


async def _assess_multi_audio(
    ogg_paths: list[str],
    questions: list[str],
    topic: str,
    prompt_file: str,
    n_questions: int,
) -> dict:
    """Assess multiple audio responses paired with questions."""
    system_prompt = _load_prompt(
        prompt_file,
        topic=topic,
        n_questions=str(n_questions),
    )

    content_parts: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, (ogg_path, question) in enumerate(zip(ogg_paths, questions)):
            mp3_path = os.path.join(tmp_dir, f"response_{i}.mp3")
            await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)
            audio_b64 = _encode_mp3(mp3_path)

            content_parts.append({
                "type": "text",
                "text": f"Question {i + 1}: {question}",
            })
            content_parts.append({
                "type": "input_audio",
                "input_audio": {"data": audio_b64, "format": "mp3"},
            })

    content_parts.append({
        "type": "text",
        "text": "Now assess the overall performance across all responses above.",
    })

    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")

    response = await client.chat.completions.create(
        model=model,
        modalities=["text"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts},
        ],
    )

    raw = response.choices[0].message.content
    return _parse_json(raw)


async def assess_part2(ogg_path: str, cue_card: str, duration_seconds: float) -> dict:
    """Assess IELTS Speaking Part 2 with duration context.

    If audio exceeds 120 seconds, it is trimmed to the first 2 minutes.
    """
    system_prompt = _load_prompt(
        "assess_part2.txt",
        cue_card=cue_card,
        duration_seconds=str(round(duration_seconds)),
        duration_display=_format_duration(duration_seconds),
    )

    max_ms = 120_000  # 2 minutes
    with tempfile.TemporaryDirectory() as tmp_dir:
        mp3_path = os.path.join(tmp_dir, "response.mp3")
        await asyncio.to_thread(
            _convert_ogg_to_mp3_trimmed, ogg_path, mp3_path, max_ms,
        )
        audio_b64 = _encode_mp3(mp3_path)

    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")

    response = await client.chat.completions.create(
        model=model,
        modalities=["text"],
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_b64, "format": "mp3"},
                    },
                    {
                        "type": "text",
                        "text": "Assess this Part 2 Long Turn response.",
                    },
                ],
            },
        ],
    )

    raw = response.choices[0].message.content
    return _parse_json(raw)
