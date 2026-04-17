import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: int = int(os.getenv("TELEGRAM_CHAT_ID", "138468116"))
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")

    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    PRICE_CHECK_HOURS = 2
    BIWEEKLY_CHECK_HOURS = 6   # how often to check if biweekly report is due
    BIWEEKLY_DAYS = 14

    # Tokens to monitor: coingecko_id → initial target price (None = use ATL)
    TOKENS = [
        {
            "coingecko_id": "vitadao",
            "name": "VitaDAO",
            "symbol": "VITA",
            "target_price": 0.25,
            "cmc_url": "https://coinmarketcap.com/currencies/vitadao/",
        },
        {
            "coingecko_id": "boundless",
            "name": "Boundless",
            "symbol": "MAGIC",
            "target_price": None,  # ATL
            "cmc_url": "https://www.coingecko.com/en/coins/boundless",
        },
        {
            "coingecko_id": "hivemapper",
            "name": "Hivemapper",
            "symbol": "HONEY",
            "target_price": None,  # ATL
            "cmc_url": "https://coinmarketcap.com/currencies/hivemapper/",
        },
    ]
