"""
FastAPI server for Shadowing Practice web app.
Port 8004. Generates CEFR-level passages, serves TTS audio, assesses shadowing.
"""
import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.text_gen import generate_passage
from services.tts import text_to_speech
from services.assessor import assess_shadowing

# ── Logging ──────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
_handler = RotatingFileHandler("logs/shadowing.log", maxBytes=5_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"

app = FastAPI(title="Shadowing Practice")

# ── Session storage ───────────────────────────────────────

VALID_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
VALID_DURATIONS = (30, 60, 90, 120)
SESSION_TTL = 3600


@dataclass
class SessionData:
    session_id: str
    level: str = "C1"
    duration: int = 60
    text: str = ""
    original_audio: bytes = field(default_factory=bytes)
    created_at: float = field(default_factory=time.time)


sessions: dict[str, SessionData] = {}


def _cleanup_sessions() -> None:
    now = time.time()
    expired = [k for k, v in sessions.items() if now - v.created_at > SESSION_TTL]
    for k in expired:
        del sessions[k]


# ── Request models ────────────────────────────────────────

class GenerateRequest(BaseModel):
    session_id: str
    level: str = "C1"
    duration: int = 60


# ── Endpoints ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    if req.level not in VALID_LEVELS:
        raise HTTPException(400, f"Invalid level. Must be one of {VALID_LEVELS}")
    if req.duration not in VALID_DURATIONS:
        raise HTTPException(400, f"Invalid duration. Must be one of {VALID_DURATIONS}")

    _cleanup_sessions()

    # ~160 words per minute for natural speech
    word_count = max(40, int(req.duration / 60 * 160))
    logger.info("Generating passage level=%s words=%d session=%s", req.level, word_count, req.session_id)

    try:
        text = await generate_passage(req.level, word_count)
    except Exception:
        logger.exception("Text generation failed")
        raise HTTPException(500, "Failed to generate passage")

    try:
        audio = await text_to_speech(text)
    except Exception:
        logger.exception("TTS failed")
        raise HTTPException(500, "Failed to synthesize speech")

    sessions[req.session_id] = SessionData(
        session_id=req.session_id,
        level=req.level,
        duration=req.duration,
        text=text,
        original_audio=audio,
    )
    logger.info("Generated session=%s text_len=%d audio_bytes=%d", req.session_id, len(text), len(audio))
    return {"text": text, "audio_url": f"api/audio/{req.session_id}"}


@app.get("/api/audio/{session_id}")
async def api_audio(session_id: str):
    session = sessions.get(session_id)
    if not session or not session.original_audio:
        raise HTTPException(404, "Audio not found — please generate a new passage")
    return Response(content=session.original_audio, media_type="audio/mpeg")


@app.post("/api/assess")
async def api_assess(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found — please generate a new passage")
    if not session.original_audio:
        raise HTTPException(400, "No original audio in session")

    user_audio = await audio.read()
    if len(user_audio) < 500:
        raise HTTPException(400, "Recording too short — please try again")

    logger.info(
        "Assessing session=%s level=%s user_audio_bytes=%d",
        session_id, session.level, len(user_audio),
    )

    try:
        result = await asyncio.wait_for(
            assess_shadowing(
                original_audio=session.original_audio,
                user_audio=user_audio,
                level=session.level,
                text=session.text,
            ),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, "Assessment timed out — please try again")
    except Exception:
        logger.exception("Assessment failed")
        raise HTTPException(500, "Assessment failed — please try again")

    logger.info("Assessment done session=%s overall=%.1f", session_id, result.get("overall", 0))
    return result


app.mount("/", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="webapp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
