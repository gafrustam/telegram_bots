import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
