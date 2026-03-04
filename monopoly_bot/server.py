"""Monopoly FastAPI + WebSocket server."""

import asyncio
import json
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import game as G
from board_data import board_dict, COLOR_GROUPS
from database import init_db, record_visit

os.makedirs("logs", exist_ok=True)
_log_handler = RotatingFileHandler("logs/monopoly_bot.log", maxBytes=5_000_000, backupCount=3)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_log_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await init_db()

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Connection registry ────────────────────────────────────────────────────────
# player_id -> set of WebSocket
_connections: dict[str, set[WebSocket]] = {}
# game_id -> set of player_id (spectators too)
_game_watchers: dict[str, set[str]] = {}


async def _broadcast_game(game_id: str, data: dict):
    watchers = _game_watchers.get(game_id, set())
    dead = []
    for pid in list(watchers):
        for ws in list(_connections.get(pid, [])):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                logger.exception("WebSocket send failed for player %s", pid)
                dead.append((pid, ws))
    for pid, ws in dead:
        _connections.get(pid, set()).discard(ws)


async def _broadcast_lobby():
    snap = G.lobby_snapshot()
    snap["type"] = "lobby"
    dead = []
    for pid, sockets in list(_connections.items()):
        for ws in list(sockets):
            try:
                await ws.send_text(json.dumps(snap))
            except Exception:
                logger.exception("WebSocket send failed for player %s", pid)
                dead.append((pid, ws))
    for pid, ws in dead:
        _connections.get(pid, set()).discard(ws)


async def _send(ws: WebSocket, data: dict):
    await ws.send_text(json.dumps(data))


# ── HTTP routes ────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/board")
async def get_board():
    return JSONResponse({
        "board": board_dict(),
        "color_groups": COLOR_GROUPS,
    })


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    player_id: Optional[str] = None
    current_game_id: Optional[str] = None

    try:
        async for raw in ws.iter_text():
            msg = json.loads(raw)
            action = msg.get("action")

            # ── Identify ──────────────────────────────────────
            if action == "identify":
                player_id = msg.get("player_id") or str(uuid.uuid4())
                if player_id not in _connections:
                    _connections[player_id] = set()
                    await record_visit(player_id)
                _connections[player_id].add(ws)
                await _send(ws, {
                    "type": "identified",
                    "player_id": player_id,
                    **G.lobby_snapshot(),
                })
                continue

            if not player_id:
                await _send(ws, {"type": "error", "error": "Сначала идентифицируйтесь"})
                continue

            # ── Lobby ─────────────────────────────────────────
            if action == "list_games":
                await _send(ws, {"type": "lobby", **G.lobby_snapshot()})

            elif action == "create_game":
                name = msg.get("name", "Игрок")[:20]
                max_humans = min(max(int(msg.get("max_humans", 2)), 1), 6)
                max_ai = min(max(int(msg.get("max_ai", 0)), 0), 5)
                if max_humans + max_ai > 6:
                    max_ai = max(0, 6 - max_humans)
                g = G.create_game(player_id, name, max_humans, max_ai)
                current_game_id = g.game_id
                _game_watchers.setdefault(g.game_id, set()).add(player_id)
                snap = G._state_snapshot(g)
                snap["type"] = "game_state"
                await _send(ws, snap)
                await _broadcast_lobby()
                # If game starts immediately (1 human + AI)
                if g.status == "playing":
                    await _run_ai_turns(g)

            elif action == "join_game":
                game_id = msg.get("game_id")
                name = msg.get("name", "Игрок")[:20]
                g = G.join_game(game_id, player_id, name)
                if not g:
                    await _send(ws, {"type": "error", "error": "Не удалось присоединиться к игре"})
                    continue
                current_game_id = g.game_id
                _game_watchers.setdefault(g.game_id, set()).add(player_id)
                snap = G._state_snapshot(g)
                snap["type"] = "game_state"
                await _broadcast_game(g.game_id, snap)
                await _broadcast_lobby()
                if g.status == "playing":
                    await _run_ai_turns(g)

            elif action == "rejoin_game":
                game_id = msg.get("game_id")
                g = G.get_game(game_id)
                if g:
                    current_game_id = game_id
                    _game_watchers.setdefault(game_id, set()).add(player_id)
                    snap = G._state_snapshot(g)
                    snap["type"] = "game_state"
                    await _send(ws, snap)

            # ── In-game actions ───────────────────────────────
            elif action in ("roll_dice", "buy", "decline_buy", "end_turn",
                            "pay_bail", "use_card", "build_house", "sell_house",
                            "mortgage", "unmortgage"):
                if not current_game_id:
                    await _send(ws, {"type": "error", "error": "Вы не в игре"})
                    continue
                g = G.get_game(current_game_id)
                if not g or g.status != "playing":
                    await _send(ws, {"type": "error", "error": "Игра не активна"})
                    continue

                snap = None
                if action == "roll_dice":
                    snap = G.roll_dice(g)
                elif action == "buy":
                    snap = G.buy_property(g, player_id)
                elif action == "decline_buy":
                    snap = G.decline_buy(g, player_id)
                elif action == "end_turn":
                    snap = G.end_turn(g, player_id)
                elif action == "pay_bail":
                    snap = G.pay_jail_bail(g)
                elif action == "use_card":
                    snap = G.use_jail_free_card(g)
                elif action == "build_house":
                    snap = G.build_house(g, player_id, int(msg.get("position", -1)))
                elif action == "sell_house":
                    snap = G.sell_house(g, player_id, int(msg.get("position", -1)))
                elif action == "mortgage":
                    snap = G.mortgage_property(g, player_id, int(msg.get("position", -1)))
                elif action == "unmortgage":
                    snap = G.unmortgage_property(g, player_id, int(msg.get("position", -1)))

                if snap:
                    if "error" in snap:
                        await _send(ws, {"type": "error", **snap})
                    else:
                        snap["type"] = "game_state"
                        await _broadcast_game(current_game_id, snap)
                        await _run_ai_turns(g)

    except WebSocketDisconnect:
        pass
    finally:
        if player_id:
            _connections.get(player_id, set()).discard(ws)


async def _run_ai_turns(g: G.GameState):
    """Run AI turns in sequence until a human's turn or game ends."""
    for _ in range(100):  # safety cap
        if g.status != "playing":
            break
        cp = G.current_player(g)
        if not cp.is_ai:
            break
        await asyncio.sleep(0.8)
        snapshots = G.ai_turn(g)
        for snap in snapshots:
            snap["type"] = "game_state"
            await _broadcast_game(g.game_id, snap)
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
