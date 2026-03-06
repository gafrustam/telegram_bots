import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_base_descriptors() -> str:
    return (PROMPTS_DIR / "base_descriptors.txt").read_text(encoding="utf-8")


def _load_prompt(filename: str, **kwargs: str) -> str:
    template = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    base = _load_base_descriptors()
    return template.format(base_descriptors=base, **kwargs)


def _convert_audio(src: str, dst: str, max_ms: int | None = None) -> None:
    audio = AudioSegment.from_file(src)
    if max_ms and len(audio) > max_ms:
        audio = audio[:max_ms]
    audio.export(dst, format="mp3", bitrate="64k")


def _get_duration_seconds(path: str) -> float:
    return len(AudioSegment.from_file(path)) / 1000.0


def _format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


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


def _google_client():
    from google import genai
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


async def assess_part1(
    ogg_paths: list[str], questions: list[str], topic: str,
    durations: list[int] | None = None,
) -> dict:
    return await _assess_multi(
        ogg_paths, questions, topic,
        prompt_file="assess_part1.txt",
        part_label="1",
        durations=durations,
    )


async def assess_part3(
    ogg_paths: list[str], questions: list[str], topic: str,
    durations: list[int] | None = None,
) -> dict:
    return await _assess_multi(
        ogg_paths, questions, topic,
        prompt_file="assess_part3.txt",
        part_label="3",
        durations=durations,
    )


async def _assess_multi(
    ogg_paths: list[str],
    questions: list[str],
    topic: str,
    prompt_file: str,
    part_label: str,
    durations: list[int] | None = None,
) -> dict:
    from google.genai import types

    n = len(questions)
    questions_list = "\n".join(f"  {i + 1}. {q}" for i, q in enumerate(questions))
    system_prompt = _load_prompt(
        prompt_file, topic=topic,
        n_questions=str(n), questions_list=questions_list,
    )
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.5-flash")
    logger.info("Assessing part%s via Gemini n_audio=%d", part_label, len(ogg_paths))

    try:
        content_parts = []
        with tempfile.TemporaryDirectory() as tmp:
            for i, (ogg_path, question) in enumerate(zip(ogg_paths, questions)):
                mp3 = os.path.join(tmp, f"r{i}.mp3")
                await asyncio.to_thread(_convert_audio, ogg_path, mp3)
                dur_info = f" (duration: {durations[i]} seconds)" if durations and i < len(durations) else ""
                content_parts.append(types.Part.from_text(text=f"Question {i + 1}: {question}{dur_info}"))
                with open(mp3, "rb") as f:
                    content_parts.append(types.Part.from_bytes(data=f.read(), mime_type="audio/mp3"))

        content_parts.append(types.Part.from_text(text="Now assess the overall performance across all responses above."))

        client = _google_client()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model_name,
            contents=content_parts,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        result = _parse_json(response.text)
        logger.info("Part%s assessment OK band=%.1f", part_label, result.get("overall_band", 0))
        return result
    except Exception as e:
        logger.error("Part%s assessment failed: %s", part_label, e)
        raise


async def assess_part2(
    ogg_path: str, cue_card: str, duration_seconds: float,
) -> dict:
    from google.genai import types

    system_prompt = _load_prompt(
        "assess_part2.txt", cue_card=cue_card,
        duration_seconds=str(round(duration_seconds)),
        duration_display=_format_duration(duration_seconds),
    )
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.5-flash")
    logger.info("Assessing part2 via Gemini duration=%.1fs", duration_seconds)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = os.path.join(tmp, "r.mp3")
            await asyncio.to_thread(_convert_audio, ogg_path, mp3, 120_000)
            with open(mp3, "rb") as f:
                audio_bytes = f.read()

        client = _google_client()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model_name,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"),
                types.Part.from_text(text="Assess this Part 2 Long Turn response."),
            ],
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        result = _parse_json(response.text)
        logger.info("Part2 assessment OK band=%.1f", result.get("overall_band", 0))
        return result
    except Exception as e:
        logger.error("Part2 assessment failed: %s", e)
        raise
