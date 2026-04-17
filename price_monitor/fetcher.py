import asyncio
import logging
from typing import Optional

import aiohttp

from config import Config

logger = logging.getLogger(__name__)

_HEADERS = {"Accept": "application/json", "User-Agent": "CryptoMonitor/1.0"}


class PriceFetcher:
    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = dict(_HEADERS)
            if Config.COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = Config.COINGECKO_API_KEY
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_prices(self, coingecko_ids: list[str]) -> dict[str, float]:
        """Fetch current USD prices for a list of CoinGecko IDs in one request."""
        ids_str = ",".join(coingecko_ids)
        url = f"{Config.COINGECKO_BASE_URL}/simple/price"
        params = {"ids": ids_str, "vs_currencies": "usd"}
        for attempt in range(3):
            try:
                session = await self._get_session()
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status == 429:
                        wait = 30 * (attempt + 1)
                        logger.warning("CoinGecko rate limit, waiting %ds", wait)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()
                    return {k: v["usd"] for k, v in data.items() if "usd" in v}
            except aiohttp.ClientResponseError as e:
                logger.exception("HTTP error fetching prices (attempt %d): %s", attempt + 1, e)
            except Exception:
                logger.exception("Error fetching prices (attempt %d)", attempt + 1)
            await asyncio.sleep(5)
        return {}

    async def get_atl(self, coingecko_id: str) -> Optional[float]:
        """Fetch all-time low price in USD for a token."""
        url = f"{Config.COINGECKO_BASE_URL}/coins/{coingecko_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }
        for attempt in range(3):
            try:
                session = await self._get_session()
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 429:
                        wait = 60 * (attempt + 1)
                        logger.warning("CoinGecko rate limit on ATL fetch, waiting %ds", wait)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()
                    atl = data.get("market_data", {}).get("atl", {}).get("usd")
                    if atl is not None:
                        logger.info("ATL for %s: $%.8f", coingecko_id, atl)
                        return float(atl)
                    return None
            except Exception:
                logger.exception("Error fetching ATL for %s (attempt %d)", coingecko_id, attempt + 1)
            await asyncio.sleep(5)
        return None

    async def get_coin_info(self, coingecko_id: str) -> Optional[dict]:
        """Fetch name, symbol, current price, ATL, and market cap."""
        url = f"{Config.COINGECKO_BASE_URL}/coins/{coingecko_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }
        try:
            session = await self._get_session()
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                md = data.get("market_data", {})
                return {
                    "name": data.get("name"),
                    "symbol": data.get("symbol", "").upper(),
                    "current_price": md.get("current_price", {}).get("usd"),
                    "atl": md.get("atl", {}).get("usd"),
                    "ath": md.get("ath", {}).get("usd"),
                    "market_cap": md.get("market_cap", {}).get("usd"),
                    "price_change_percentage_24h": md.get("price_change_percentage_24h"),
                }
        except Exception:
            logger.exception("Error fetching coin info for %s", coingecko_id)
            return None
