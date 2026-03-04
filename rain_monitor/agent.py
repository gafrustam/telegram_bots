#!/usr/bin/env python3
"""
Rain Monitor Agent — Koh Samui
Runs every 30 minutes via systemd timer.
Fetches weather from open-meteo.com (free, no key),
uses OpenAI to compose a friendly Russian alert,
sends Telegram notification 1 hour before rain.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import httpx
from openai import OpenAI

# ── Logging ───────────────────────────────────────────────────────────────────
_log_dir = Path(__file__).parent / "logs"
_log_dir.mkdir(exist_ok=True)

_handler = RotatingFileHandler(
    _log_dir / "rain_monitor.log", maxBytes=5_000_000, backupCount=3
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_handler, logging.StreamHandler()],
)
logger = logging.getLogger("rain_monitor")

# ── Config ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY    = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
BOT_TOKEN         = os.environ["RAIN_BOT_TOKEN"]

_GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
AI_MODEL = "gemini-2.0-flash" if GOOGLE_AI_API_KEY else "gpt-4o-mini"


def _get_ai_client() -> OpenAI:
    if GOOGLE_AI_API_KEY:
        return OpenAI(api_key=GOOGLE_AI_API_KEY, base_url=_GOOGLE_BASE_URL)
    return OpenAI(api_key=OPENAI_API_KEY)
CHAT_ID        = os.environ["RAIN_CHAT_ID"]
STATE_FILE     = Path(__file__).parent / "rain_state.json"

# Koh Samui, Thailand (UTC+7)
LAT, LON              = 9.5287, 100.0628
BANGKOK_TZ_OFFSET     = timedelta(hours=7)
MIN_ALERT_INTERVAL_H  = 2.0   # don't alert more often than this
RAIN_PROB_THRESHOLD   = 60    # % precipitation probability


# ── Weather ───────────────────────────────────────────────────────────────────

def fetch_forecast() -> list[dict]:
    """Return next 4 hours of hourly forecast from open-meteo.com."""
    resp = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude":  LAT,
            "longitude": LON,
            "hourly": [
                "precipitation_probability",
                "precipitation",
                "weathercode",
                "temperature_2m",
            ],
            "forecast_days": 1,
            "timezone": "Asia/Bangkok",
        },
        timeout=15,
    )
    resp.raise_for_status()
    raw = resp.json()

    now_bkk = datetime.now(timezone.utc) + BANGKOK_TZ_OFFSET
    hourly  = raw["hourly"]
    result  = []

    for i, t_str in enumerate(hourly["time"]):
        t       = datetime.fromisoformat(t_str)
        delta_h = (t - now_bkk.replace(tzinfo=None)).total_seconds() / 3600
        if delta_h < -0.5:
            continue
        if delta_h > 4:
            break
        result.append({
            "time":       t_str,
            "in_hours":   round(delta_h, 1),
            "prob_%":     hourly["precipitation_probability"][i],
            "mm":         hourly["precipitation"][i],
            "wcode":      hourly["weathercode"][i],
            "temp_c":     hourly["temperature_2m"][i],
        })

    return result


# ── State (deduplication) ─────────────────────────────────────────────────────

def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except Exception:
        logger.exception("Failed to load state file")
        return {}


def can_alert() -> bool:
    last = load_state().get("last_alert_utc")
    if not last:
        return True
    last_dt   = datetime.fromisoformat(last).replace(tzinfo=timezone.utc)
    hours_ago = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
    return hours_ago >= MIN_ALERT_INTERVAL_H


def mark_alerted() -> None:
    state = load_state()
    state["last_alert_utc"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Alert ─────────────────────────────────────────────────────────────────────

WEATHER_CODES = {
    range(0, 1):   "ясно",
    range(1, 4):   "облачно",
    range(51, 58): "морось",
    range(61, 68): "дождь",
    range(71, 78): "снег",
    range(80, 83): "ливень",
    range(95, 100):"гроза",
}

def wcode_to_ru(code: int) -> str:
    for r, name in WEATHER_CODES.items():
        if code in r:
            return name
    return "осадки"


def compose_alert(slot: dict) -> str:
    """Use AI to compose a short friendly Russian alert."""
    client = _get_ai_client()

    weather_type = wcode_to_ru(slot["wcode"])
    is_storm     = slot["wcode"] >= 95

    prompt = (
        f"Напиши короткое предупреждение о дожде на Ко Самуи (Таиланд). "
        f"Параметры: тип осадков={weather_type}, через={slot['in_hours']} ч, "
        f"вероятность={slot['prob_%']}%, интенсивность={slot['mm']} мм, температура={slot['temp_c']}°C. "
        f"Требования: 1-3 строки, русский язык, HTML-разметка (<b>), эмодзи {'⛈' if is_storm else '☔'}, "
        f"укажи через сколько минут ожидать. Без лишних слов."
    )

    resp = client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def send_telegram(text: str) -> None:
    resp = httpx.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
    resp.raise_for_status()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Rain check started")

    try:
        forecast = fetch_forecast()
    except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError,
            httpx.HTTPStatusError) as exc:
        logger.warning("Transient error fetching forecast (skipping): %s", exc)
        return
    except Exception:
        logger.exception("Unexpected error fetching forecast")
        return

    logger.info("Forecast (%d slots):", len(forecast))
    for s in forecast:
        logger.info("  +%4.1fh  prob=%3d%%  mm=%.1f  wcode=%d",
                    s["in_hours"], s["prob_%"], s["mm"], s["wcode"])

    # Find the nearest slot within 1 hour with rain likely
    rain_slot = next(
        (s for s in forecast if s["in_hours"] <= 1.0 and s["prob_%"] >= RAIN_PROB_THRESHOLD),
        None,
    )

    if rain_slot is None:
        logger.info("No rain expected within 1 hour. Nothing to do.")
        return

    logger.info("Rain detected: %s", rain_slot)

    if not can_alert():
        state = load_state()
        logger.info("Alert suppressed (last sent: %s)", state.get("last_alert_utc"))
        return

    logger.info("Composing alert with AI...")
    try:
        message = compose_alert(rain_slot)
    except Exception:
        logger.exception("Failed to compose AI alert")
        return
    logger.info("Message: %s", message[:100])

    try:
        send_telegram(message)
    except Exception:
        logger.exception("Failed to send Telegram alert")
        return
    mark_alerted()
    logger.info("Alert sent and state saved.")


if __name__ == "__main__":
    main()
