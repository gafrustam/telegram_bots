#!/usr/bin/env python3
"""VitaDAO (VITA) price alert: notifies when price reaches $0.22."""

import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests

# Config
TELEGRAM_TOKEN = "8549917399:AAGMkkcouoQxSIdTJPNcD7Ec3qXab3aUqWk"
ADMIN_CHAT_ID = 138468116
TARGET_PRICE = 0.22
COINGECKO_ID = "vitadao"
COOLDOWN_FILE = Path(__file__).parent / ".last_notified"
COOLDOWN_SECONDS = 12 * 3600  # 12 hours between repeat alerts

# Logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
handler = RotatingFileHandler(log_dir / "price_monitor.log", maxBytes=5_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_vita_price() -> float:
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={COINGECKO_ID}&vs_currencies=usd"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()[COINGECKO_ID]["usd"]


def send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
    resp.raise_for_status()


def cooldown_passed() -> bool:
    if not COOLDOWN_FILE.exists():
        return True
    last = float(COOLDOWN_FILE.read_text().strip())
    return (time.time() - last) >= COOLDOWN_SECONDS


def record_notification() -> None:
    COOLDOWN_FILE.write_text(str(time.time()))


def main() -> None:
    try:
        price = get_vita_price()
        logger.info("VITA price: $%.4f (target: $%.2f)", price, TARGET_PRICE)

        if price <= TARGET_PRICE:
            if cooldown_passed():
                msg = (
                    f"🎯 <b>VitaDAO (VITA) достиг целевой цены!</b>\n\n"
                    f"Текущая цена: <b>${price:.4f}</b>\n"
                    f"Целевая цена: <b>${TARGET_PRICE:.2f}</b>\n\n"
                    f"<a href=\"https://coinmarketcap.com/currencies/vitadao/\">CoinMarketCap</a>"
                )
                send_telegram_message(msg)
                record_notification()
                logger.info("Alert sent: price $%.4f <= target $%.2f", price, TARGET_PRICE)
            else:
                logger.info("Price at target but cooldown active, skipping alert.")
        else:
            logger.info("Price $%.4f above target, no alert.", price)

    except Exception:
        logger.exception("Error in price check")


if __name__ == "__main__":
    main()
