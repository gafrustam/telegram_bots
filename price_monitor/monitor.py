#!/usr/bin/env python3
"""
Crypto Price Monitor
- Checks prices every 2 hours, sends alert when target reached (then lowers target 20%)
- Sends biweekly report per token: current price, 2-week change, 3-year Gemini scenarios
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import database
import fetcher as fetch_module
import notifier
import scenarios as scenario_module
from config import Config

# ── Logging ──────────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
_handler = RotatingFileHandler("logs/crypto_monitor.log", maxBytes=5_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[_handler, logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# ── Init ─────────────────────────────────────────────────────────────────────

async def init_tokens(pool, fetcher: fetch_module.PriceFetcher) -> None:
    """Insert configured tokens into DB on first run; set ATL targets where needed."""
    for cfg in Config.TOKENS:
        cid = cfg["coingecko_id"]
        existing = await database.get_token_by_coingecko_id(pool, cid)
        if existing:
            logger.info("Token %s already in DB (target: %s)", cfg["name"], existing["target_price"])
            continue

        target = cfg["target_price"]
        if target is None:
            logger.info("Fetching ATL for %s…", cfg["name"])
            target = await fetcher.get_atl(cid)
            if target is None:
                logger.warning("Could not fetch ATL for %s, using 0.001 as fallback", cfg["name"])
                target = 0.001
            await asyncio.sleep(2)  # respect CoinGecko rate limit between calls

        await database.upsert_token(
            pool,
            symbol=cfg["symbol"],
            name=cfg["name"],
            coingecko_id=cid,
            cmc_url=cfg.get("cmc_url", ""),
            target_price=target,
        )
        logger.info("Inserted token %s with target $%.8f", cfg["name"], target)


# ── Price check job (every 2 hours) ──────────────────────────────────────────

async def job_check_prices() -> None:
    logger.info("=== Price check started ===")
    pool = await database.get_pool()
    fetcher = fetch_module.PriceFetcher()
    try:
        tokens = await database.get_active_tokens(pool)
        if not tokens:
            logger.warning("No active tokens in DB")
            return

        ids = [t["coingecko_id"] for t in tokens]
        prices = await fetcher.get_prices(ids)

        for token in tokens:
            cid = token["coingecko_id"]
            price = prices.get(cid)
            if price is None:
                logger.warning("No price returned for %s", cid)
                continue

            target = token["target_price"]
            logger.info("%s (%s): $%.8f | target: %s",
                        token["name"], cid, price,
                        f"${float(target):.8f}" if target else "none")

            await database.record_price(pool, token["id"], price)

            if target is not None and price <= float(target):
                new_target = float(target) * 0.8
                await database.update_target_price(pool, token["id"], new_target)
                await notifier.send_price_alert(token, price, float(target), new_target)
    except Exception:
        logger.exception("Error in price check job")
    finally:
        await fetcher.close()
    logger.info("=== Price check done ===")


# ── Biweekly report job (checked every 6 hours) ───────────────────────────────

async def job_biweekly_check() -> None:
    logger.info("=== Biweekly check started ===")
    pool = await database.get_pool()
    fetcher = fetch_module.PriceFetcher()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=Config.BIWEEKLY_DAYS)

    try:
        tokens = await database.get_active_tokens(pool)
        for token in tokens:
            last_at = token.get("last_biweekly_at")
            if last_at and last_at.tzinfo is None:
                last_at = last_at.replace(tzinfo=timezone.utc)

            if last_at and last_at > cutoff:
                next_report = last_at + timedelta(days=Config.BIWEEKLY_DAYS)
                logger.info("%s: next report at %s", token["name"], next_report.strftime("%Y-%m-%d %H:%M UTC"))
                continue

            logger.info("%s: generating biweekly report…", token["name"])
            price = (await fetcher.get_prices([token["coingecko_id"]])).get(token["coingecko_id"])
            if price is None:
                logger.warning("Cannot fetch price for %s, skipping report", token["name"])
                continue

            prev_price = token.get("last_biweekly_price")
            change_pct: Optional[float] = None
            if prev_price:
                prev_f = float(prev_price)
                if prev_f > 0:
                    change_pct = ((price - prev_f) / prev_f) * 100

            # Fetch ATL for scenario context
            coin_info = await fetcher.get_coin_info(token["coingecko_id"])
            atl = coin_info.get("atl") if coin_info else None
            await asyncio.sleep(2)

            scen = await scenario_module.generate_scenarios(
                token["name"], token["symbol"], price, atl
            )

            target = token.get("target_price")
            await notifier.send_biweekly_report(
                token,
                current_price=price,
                prev_price=float(prev_price) if prev_price else None,
                change_pct=change_pct,
                target_price=float(target) if target else None,
                scenario_list=scen,
            )

            await database.update_biweekly_snapshot(pool, token["id"], price)
            await asyncio.sleep(3)  # pace between tokens

    except Exception:
        logger.exception("Error in biweekly check job")
    finally:
        await fetcher.close()
    logger.info("=== Biweekly check done ===")


# ── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    logger.info("Starting Crypto Monitor…")
    pool = await database.get_pool()
    await database.create_tables(pool)

    fetcher = fetch_module.PriceFetcher()
    try:
        await init_tokens(pool, fetcher)
    finally:
        await fetcher.close()

    tokens = await database.get_active_tokens(pool)
    await notifier.send_startup_message(tokens)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        job_check_prices,
        IntervalTrigger(hours=Config.PRICE_CHECK_HOURS),
        id="price_check",
        next_run_time=datetime.now(timezone.utc),  # run immediately on start
    )
    # Delay biweekly check by 5 minutes to avoid simultaneous CoinGecko requests
    scheduler.add_job(
        job_biweekly_check,
        IntervalTrigger(hours=Config.BIWEEKLY_CHECK_HOURS),
        id="biweekly_check",
        next_run_time=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    scheduler.start()
    logger.info("Scheduler started. Price check every %dh, biweekly check every %dh.",
                Config.PRICE_CHECK_HOURS, Config.BIWEEKLY_CHECK_HOURS)

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down…")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
