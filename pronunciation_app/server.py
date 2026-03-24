"""
Pronunciation Practice – FastAPI backend
Port 8005. Accepts audio + word, sends to OpenAI for pronunciation assessment.
"""
import asyncio
import base64
import json
import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI

# ── Logging ──────────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
_handler = RotatingFileHandler("logs/pronunciation.log", maxBytes=5_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ── OpenAI client ─────────────────────────────────────────────────────────────
_openai_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _openai_client


_model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_mp3(audio_bytes: bytes) -> bytes:
    """Convert audio bytes to mp3 using pydub (sync, run in thread)."""
    import io
    from pydub import AudioSegment

    buf = io.BytesIO(audio_bytes)
    seg = AudioSegment.from_file(buf)
    out = io.BytesIO()
    seg.export(out, format="mp3", bitrate="64k")
    return out.getvalue()


def _parse_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s = text.find("{")
        e = text.rfind("}") + 1
        if s != -1 and e > s:
            return json.loads(text[s:e])
        raise


SYSTEM_PROMPT = (
    "You are an English pronunciation coach. "
    "Assess the learner's pronunciation based on IPA phonetics. "
    "Accept both British (RP) and General American accents. "
    "Be a bit lenient — focus on the key characteristic sounds, "
    "not minor accent differences. "
    "Respond ONLY with valid JSON, no markdown, no extra text."
)

ASSESS_TEMPLATE = """\
The learner is practicing the English word: "{word}"
Correct IPA pronunciation: /{ipa}/
Key phonetic rule: {comment}

Listen to the audio recording of the learner saying this word.
Determine whether the pronunciation is correct or acceptable.

Return ONLY valid JSON on one line:
{{"correct": true, "feedback": "Отличное произношение!"}}
or
{{"correct": false, "feedback": "Краткое объяснение ошибки на русском (1 предложение)."}}"""


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Pronunciation Practice")


@app.post("/api/assess")
async def assess_pronunciation(
    audio: UploadFile = File(...),
    word: str = Form(...),
    ipa: str = Form(...),
    comment: str = Form(...),
):
    try:
        audio_bytes = await audio.read()
        logger.info("Assessing word='%s' audio_size=%d bytes mime=%s",
                    word, len(audio_bytes), audio.content_type)

        # Convert to mp3 for reliable processing
        mp3_bytes = await asyncio.to_thread(_to_mp3, audio_bytes)
        audio_b64 = base64.b64encode(mp3_bytes).decode("utf-8")

        prompt = ASSESS_TEMPLATE.format(word=word, ipa=ipa, comment=comment)

        client = _get_client()
        response = await client.chat.completions.create(
            model=_model, modalities=["text"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "input_audio", "input_audio": {"data": audio_b64, "format": "mp3"}},
                    {"type": "text", "text": prompt},
                ]},
            ],
        )
        result = _parse_json(response.choices[0].message.content)

        correct = bool(result.get("correct", False))
        feedback = str(result.get("feedback", ""))
        logger.info("Word='%s' correct=%s", word, correct)
        return {"correct": correct, "feedback": feedback}

    except Exception:
        logger.exception("Error assessing word='%s'", word)
        return JSONResponse(
            {"correct": False, "feedback": "Ошибка оценки. Попробуйте ещё раз."},
            status_code=200,
        )


# Serve static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8005"))
    uvicorn.run("server:app", host="127.0.0.1", port=port, log_level="info")
