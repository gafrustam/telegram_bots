import asyncio
import base64
import json
import os
import tempfile
from pathlib import Path

from openai import AsyncOpenAI
from pydub import AudioSegment

PROMPT_PATH = Path(__file__).parent / "prompt.txt"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _convert_ogg_to_mp3(ogg_path: str, mp3_path: str) -> None:
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(mp3_path, format="mp3", bitrate="64k")


def _get_duration_seconds(ogg_path: str) -> float:
    audio = AudioSegment.from_ogg(ogg_path)
    return len(audio) / 1000.0


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening ```json
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


async def assess_speaking(ogg_path: str) -> dict:
    """Assess an IELTS Speaking audio sample.

    Args:
        ogg_path: Path to the OGG audio file from Telegram.

    Returns:
        Parsed assessment dict or dict with 'error' key.
    """
    duration = await asyncio.to_thread(_get_duration_seconds, ogg_path)
    if duration < 5:
        return {"error": "Аудио слишком короткое. Запишите сообщение длительностью хотя бы 10 секунд, чтобы я мог оценить ваш Speaking."}

    with tempfile.TemporaryDirectory() as tmp_dir:
        mp3_path = os.path.join(tmp_dir, "audio.mp3")
        await asyncio.to_thread(_convert_ogg_to_mp3, ogg_path, mp3_path)

        with open(mp3_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    system_prompt = _load_prompt()
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
                        "input_audio": {
                            "data": audio_b64,
                            "format": "mp3",
                        },
                    },
                    {
                        "type": "text",
                        "text": "Оцени этот образец IELTS Speaking по всем четырём критериям.",
                    },
                ],
            },
        ],
    )

    raw = response.choices[0].message.content
    return _parse_json(raw)
