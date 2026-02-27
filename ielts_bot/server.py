"""
FastAPI server for IELTS Speaking Practice web app.
Port 8002. Serves the webapp SPA and API endpoints.
"""
import hashlib
import hmac
import json
import logging
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qsl

from dotenv import load_dotenv

load_dotenv()

import database
from assessor import assess_part1, assess_part2, assess_part3, _get_duration_seconds
from questions import generate_session

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

app = FastAPI(title="IELTS Speaking Practice")

# ── Session storage ──────────────────────────────────────

@dataclass
class SessionData:
    session_token: str
    user_id: int | None = None        # set if Telegram Mini App
    part: int | None = None
    topic: str = ""
    questions: list[str] = field(default_factory=list)
    cue_card: str = ""
    audio_files: list[bytes] = field(default_factory=list)   # raw bytes
    audio_durations: list[float] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


sessions: dict[str, SessionData] = {}

SESSION_TTL = 3600  # 1 hour


def _get_or_create_session(token: str) -> SessionData:
    if token not in sessions:
        sessions[token] = SessionData(session_token=token)
    return sessions[token]


def _cleanup_old_sessions() -> None:
    now = time.time()
    expired = [t for t, s in sessions.items() if now - s.created_at > SESSION_TTL]
    for t in expired:
        del sessions[t]


# ── Telegram initData validation ─────────────────────────

def _validate_telegram_init_data(init_data: str) -> dict | None:
    """
    Validate Telegram WebApp initData HMAC-SHA256.
    Returns parsed user dict or None if invalid/missing.
    """
    if not init_data or not TELEGRAM_TOKEN:
        return None
    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = params.pop("hash", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )
        secret_key = hmac.new(
            b"WebAppData", TELEGRAM_TOKEN.encode(), hashlib.sha256
        ).digest()
        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(received_hash, expected_hash):
            return None
        user_str = params.get("user", "{}")
        return json.loads(user_str)
    except Exception:
        logger.exception("initData validation failed")
        return None


# ── Request/response models ──────────────────────────────

class TopicRequest(BaseModel):
    part: int
    session_token: str


class AssessRequest(BaseModel):
    session_token: str


# ── Health ───────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── API: generate topic ──────────────────────────────────

@app.post("/api/topic")
async def api_topic(req: TopicRequest):
    if req.part not in (1, 2, 3):
        raise HTTPException(400, "part must be 1, 2, or 3")

    _cleanup_old_sessions()
    session = _get_or_create_session(req.session_token)
    session.part = req.part
    # Clear previous audio
    session.audio_files = []
    session.audio_durations = []

    try:
        bank_topic = None
        if database.is_available():
            bank_topic = await database.get_random_topic(req.part, session.user_id or 0)

        if bank_topic:
            topic_name = bank_topic["topic"]
            cue_card_template = bank_topic.get("cue_card")
            gen = await generate_session(
                req.part,
                topic=topic_name,
                cue_card_template=cue_card_template if req.part == 2 else None,
            )
            gen.setdefault("topic", topic_name)
        else:
            gen = await generate_session(req.part)
    except Exception as e:
        logger.exception("Topic generation failed")
        raise HTTPException(500, f"Failed to generate topic: {e}")

    session.topic = gen.get("topic", "General")
    session.questions = gen.get("questions", [])
    session.cue_card = gen.get("cue_card", "")

    return {
        "topic": session.topic,
        "questions": session.questions,
        "cue_card": session.cue_card,
    }


# ── API: submit audio answer ─────────────────────────────

@app.post("/api/answer")
async def api_answer(
    session_token: str = Form(...),
    question_index: int = Form(...),
    file: UploadFile = File(...),
):
    session = _get_or_create_session(session_token)
    if session.part is None:
        raise HTTPException(400, "No active topic. Call /api/topic first.")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Empty audio file")

    # Pad list to the right length if needed (allow re-upload)
    while len(session.audio_files) <= question_index:
        session.audio_files.append(b"")
        session.audio_durations.append(0.0)

    session.audio_files[question_index] = audio_bytes

    # Estimate duration from content length (rough: 16kHz mono opus ~16kb/s)
    duration_est = len(audio_bytes) / 16000.0
    session.audio_durations[question_index] = duration_est

    return {"status": "ok", "question_index": question_index}


# ── API: run assessment ──────────────────────────────────

@app.post("/api/assess")
async def api_assess(
    req: AssessRequest,
    x_telegram_init_data: str | None = Header(default=None),
):
    session = sessions.get(req.session_token)
    if session is None:
        raise HTTPException(404, "Session not found")
    if session.part is None:
        raise HTTPException(400, "No active topic")
    if not any(session.audio_files):
        raise HTTPException(400, "No audio submitted")

    # Optionally resolve Telegram user
    if x_telegram_init_data:
        tg_user = _validate_telegram_init_data(x_telegram_init_data)
        if tg_user:
            session.user_id = tg_user.get("id")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Write audio blobs to temp files as OGG (pydub can handle webm/ogg)
            ogg_paths = []
            for i, audio_bytes in enumerate(session.audio_files):
                if not audio_bytes:
                    continue
                ext = _detect_audio_ext(audio_bytes)
                path = os.path.join(tmp_dir, f"response_{i}.{ext}")
                logger.info(
                    "assess: writing audio[%d] size=%d ext=%s session=%s",
                    i, len(audio_bytes), ext, req.session_token[:8],
                )
                with open(path, "wb") as f:
                    f.write(audio_bytes)
                ogg_paths.append(path)

            if not ogg_paths:
                raise HTTPException(400, "No valid audio files")

            part = session.part
            durations_int = [int(d) for d in session.audio_durations if d > 0]

            if part == 1:
                result = await assess_part1(
                    ogg_paths, session.questions[:len(ogg_paths)], session.topic,
                    durations=durations_int or None,
                    user_id=session.user_id,
                )
            elif part == 2:
                duration = await _get_duration_safe(ogg_paths[0])
                result = await assess_part2(
                    ogg_paths[0], session.cue_card, duration,
                    user_id=session.user_id,
                )
            else:
                result = await assess_part3(
                    ogg_paths, session.questions[:len(ogg_paths)], session.topic,
                    durations=durations_int or None,
                    user_id=session.user_id,
                )

        # Save to DB if available
        if database.is_available() and session.user_id:
            db_session_id = await database.create_session(
                user_id=session.user_id,
                part=part,
                topic=session.topic,
                questions=session.questions or None,
                cue_card=session.cue_card or None,
            )
            audio_total = int(sum(session.audio_durations))
            await database.complete_session(db_session_id, audio_total)
            await database.save_assessment(
                session_id=db_session_id,
                user_id=session.user_id,
                result=result,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Assessment failed for session %s", req.session_token)
        raise HTTPException(500, f"Assessment failed: {e}")


async def _get_duration_safe(path: str) -> float:
    import asyncio
    try:
        return await asyncio.to_thread(_get_duration_seconds, path)
    except Exception:
        return 0.0


def _detect_audio_ext(data: bytes) -> str:
    """Detect audio format from magic bytes."""
    if data[:4] == b"OggS":
        return "ogg"
    if data[:4] == b"RIFF":
        return "wav"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    # WebM / Matroska (EBML magic)
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    return "ogg"  # default fallback


# ── Static files & SPA ───────────────────────────────────

# Mount /static for CSS/JS assets
if (WEBAPP_DIR / "css").exists():
    app.mount("/static/css", StaticFiles(directory=str(WEBAPP_DIR / "css")), name="css")
if (WEBAPP_DIR / "js").exists():
    app.mount("/static/js", StaticFiles(directory=str(WEBAPP_DIR / "js")), name="js")


@app.get("/")
async def index():
    index_file = WEBAPP_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(404, "index.html not found")
    return FileResponse(str(index_file))


@app.get("/ttt/")
@app.get("/ttt")
async def ttt_index():
    """Serve the Tic-Tac-Toe game (local dev fallback)."""
    ttt_file = WEBAPP_DIR / "ttt" / "index.html"
    if not ttt_file.exists():
        raise HTTPException(404, "ttt/index.html not found")
    return FileResponse(str(ttt_file))


@app.get("/assets/nav.js")
async def assets_nav_js():
    """Serve nav.js for local development (production serves from nginx static root)."""
    nav_file = WEBAPP_DIR / "js" / "nav.js"
    if not nav_file.exists():
        raise HTTPException(404, "nav.js not found")
    return FileResponse(str(nav_file), media_type="application/javascript")


# ── TTT WebSocket matchmaking ─────────────────────────────

import asyncio as _asyncio
from typing import Optional as _Optional

@dataclass
class TttRoom:
    room_id: str
    players: list = field(default_factory=list)   # list of WebSocket
    symbols: dict = field(default_factory=dict)   # ws_id → 'X'|'O'
    started: bool = False

_ttt_waiting: _Optional[TttRoom] = None
_ttt_rooms: dict[str, TttRoom] = {}


@app.websocket("/ws/ttt")
async def ttt_ws(ws: WebSocket):
    global _ttt_waiting
    await ws.accept()

    # Join or create room
    if _ttt_waiting is None:
        room = TttRoom(room_id=str(uuid.uuid4()))
        _ttt_waiting = room
    else:
        room = _ttt_waiting
        _ttt_waiting = None

    room.players.append(ws)
    ws_id = id(ws)

    if len(room.players) == 1:
        room.symbols[ws_id] = 'X'
        _ttt_rooms[room.room_id] = room
        await ws.send_json({"type": "waiting"})
    else:
        # Second player joins
        room.symbols[ws_id] = 'O'
        room.started = True
        # Notify both
        for p in room.players:
            sym = room.symbols[id(p)]
            await p.send_json({"type": "start", "symbol": sym})

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "move" and room.started:
                # Broadcast move to other player
                for p in room.players:
                    if p is not ws:
                        await p.send_json(data)

            elif msg_type == "restart":
                for p in room.players:
                    if p is not ws:
                        await p.send_json({"type": "restart"})

    except (WebSocketDisconnect, Exception):
        room.players[:] = [p for p in room.players if p is not ws]
        # Notify remaining player
        for p in room.players:
            try:
                await p.send_json({"type": "opponent_left"})
            except Exception:
                pass
        if room.room_id in _ttt_rooms and not room.players:
            del _ttt_rooms[room.room_id]
        # If this was the waiting room, clear it
        if _ttt_waiting is room:
            _ttt_waiting = None


# ── Startup ──────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await database.init_db()
    logger.info("IELTS server started on port 8002")


@app.on_event("shutdown")
async def shutdown():
    await database.close_db()


# ── Entry point ──────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=False)
