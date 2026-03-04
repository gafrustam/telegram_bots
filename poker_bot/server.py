"""
FastAPI server — Poker Mini App backend.
Serves static files + WebSocket game engine.
"""

import asyncio
import logging
import random
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from poker_engine import PokerGame
from ai_player import AIPlayer
from database import init_db, save_game, load_game, update_stats

load_dotenv()

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/poker_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Poker Mini App")

# Mount /static so that index.html can load assets if needed
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-memory sessions (also persisted to PostgreSQL)
_games: Dict[str, PokerGame] = {}
_ai: Dict[str, AIPlayer] = {}


# ──────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def _startup():
    await init_db()


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ──────────────────────────────────────────────────────────────────────────────
#  WebSocket endpoint
# ──────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/{user_id}")
async def ws_endpoint(ws: WebSocket, user_id: str):
    await ws.accept()

    # Restore or create game
    game = await _get_or_create_game(user_id)

    # Send initial state
    await ws.send_json({"type": "state", "game": game.get_state()})

    try:
        while True:
            msg = await ws.receive_json()
            mtype = msg.get("type", "")

            # ── new_game: full reset ──────────────────────────────────────
            if mtype == "new_game":
                game = _new_game(user_id)
                await save_game(user_id, game.to_dict())
                await ws.send_json({"type": "state", "game": game.get_state()})

            # ── new_hand: deal next hand (same game stacks) ───────────────
            elif mtype == "new_hand":
                if game.is_game_over():
                    game = _new_game(user_id)

                state = game.start_new_hand()
                await save_game(user_id, game.to_dict())
                await ws.send_json({"type": "state", "game": state})

                # If AI acts first (it's SB some hands), trigger AI turn
                if state.get("to_act") == "ai" and not state.get("winner"):
                    await _ai_turn(user_id, ws, game)

            # ── action: player action ─────────────────────────────────────
            elif mtype == "action":
                action = msg.get("action", "")
                amount = int(msg.get("amount", 0))

                hand = game.hand
                if not hand or hand.get("to_act") != "player":
                    await ws.send_json({
                        "type": "error",
                        "message": "Not your turn"
                    })
                    continue

                state = game.apply_action("player", action, raise_to=amount)
                await save_game(user_id, game.to_dict())
                await ws.send_json({"type": "state", "game": state})

                # Record stats if hand over
                if state.get("winner"):
                    await _record_hand_stats(user_id, state)

                # Trigger AI if it's their turn
                if state.get("to_act") == "ai" and not state.get("winner"):
                    await _ai_turn(user_id, ws, game)

            # ── get_state ─────────────────────────────────────────────────
            elif mtype == "get_state":
                await ws.send_json({"type": "state", "game": game.get_state()})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("WebSocket handler error for user %s", user_id)
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            logger.exception("Failed to send error response to user %s", user_id)


# ──────────────────────────────────────────────────────────────────────────────
#  AI turn helper
# ──────────────────────────────────────────────────────────────────────────────

async def _ai_turn(user_id: str, ws: WebSocket, game: PokerGame):
    """Run AI decision loop until it's the player's turn or hand is over."""
    ai = _ai.get(user_id)
    if not ai:
        ai = AIPlayer()
        _ai[user_id] = ai

    # Notify frontend
    await ws.send_json({"type": "ai_thinking"})

    # Natural delay
    await asyncio.sleep(random.uniform(0.7, 1.8))

    info = game.get_ai_hand_info()
    if not info:
        return

    try:
        decision = await ai.decide(info)
    except Exception:
        logger.exception("AI decision failed for user %s, defaulting to call", user_id)
        decision = {"action": "call", "amount": 0}

    action = decision.get("action", "call")
    amount = int(decision.get("amount", 0))

    state = game.apply_action("ai", action, raise_to=amount)
    await save_game(user_id, game.to_dict())
    await ws.send_json({"type": "state", "game": state})

    if state.get("winner"):
        await _record_hand_stats(user_id, state)
        return

    # If AI still needs to act (e.g. after street advance with no player action)
    if state.get("to_act") == "ai":
        await asyncio.sleep(0.4)
        await _ai_turn(user_id, ws, game)


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _new_game(user_id: str) -> PokerGame:
    game = PokerGame(starting_stack=3000, small_blind=50)
    _games[user_id] = game
    _ai[user_id] = AIPlayer()
    return game


async def _get_or_create_game(user_id: str) -> PokerGame:
    if user_id in _games:
        return _games[user_id]

    saved = await load_game(user_id)
    if saved:
        try:
            game = PokerGame.from_dict(saved)
            _games[user_id] = game
            _ai[user_id] = AIPlayer()
            return game
        except Exception:
            logger.exception("Failed to restore saved game for user %s, starting new game", user_id)

    return _new_game(user_id)


async def _record_hand_stats(user_id: str, state: dict):
    winner = state.get("winner")
    pot = state.get("pot", 0)
    if winner in ("player", "ai"):
        await update_stats(user_id, won=(winner == "player"), pot=pot)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
