"""
Pronunciation Practice – FastAPI backend
Port 8005. Accepts audio + word, sends to Gemini for pronunciation assessment.
"""
import asyncio
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

# ── Logging ──────────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
_handler = RotatingFileHandler("logs/pronunciation.log", maxBytes=5_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ── Gemini client ─────────────────────────────────────────────────────────────
from google import genai
from google.genai import types

_client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY", ""))
_model = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.5-flash")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_mime(audio_bytes: bytes) -> str:
    if len(audio_bytes) < 4:
        return "audio/webm"
    if audio_bytes[:4] == b"\x1a\x45\xdf\xa3":
        return "audio/webm"
    if audio_bytes[:4] == b"OggS":
        return "audio/ogg"
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "audio/mpeg"
    if audio_bytes[:4] == b"RIFF":
        return "audio/wav"
    return "audio/webm"


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

        # Convert to mp3 for reliable Gemini processing
        mp3_bytes = await asyncio.to_thread(_to_mp3, audio_bytes)

        prompt = ASSESS_TEMPLATE.format(word=word, ipa=ipa, comment=comment)

        def _call():
            return _client.models.generate_content(
                model=_model,
                contents=[
                    types.Part.from_bytes(data=mp3_bytes, mime_type="audio/mp3"),
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )

        response = await asyncio.to_thread(_call)
        result = _parse_json(response.text)

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
