"""
Test configuration: set up sys.path and environment variables
before any bot modules are imported.
"""
import os
import sys

# Add parent directory so that `import database`, `import formatter`, etc. work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Provide fake env vars so bot.py can be imported without a real token
os.environ.setdefault("TELEGRAM_TOKEN", "123456789:AABBCCDDEEFFaabbccddeeff-GGHHIIjjkkll")
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("ADMIN_USERNAME", "testadmin")
os.environ.setdefault("OPENAI_API_KEY", "sk-fake-key")
