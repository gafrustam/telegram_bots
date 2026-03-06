import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
ADMIN_USERNAME: str = (os.getenv("ADMIN_USERNAME") or "").lstrip("@").lower()

GOOGLE_TEXT_MODEL: str = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.5-flash")
GOOGLE_AUDIO_MODEL: str = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.5-flash")
