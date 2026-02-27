import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")
