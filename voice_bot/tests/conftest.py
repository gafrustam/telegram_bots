"""Pytest fixtures for voice_bot tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user.id = 123456
    msg.from_user.username = "testuser"
    msg.chat.id = 123456
    msg.reply_text = AsyncMock()
    msg.reply = AsyncMock()
    return msg


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.bot = AsyncMock()
    ctx.bot.get_file = AsyncMock()
    return ctx


@pytest.fixture
def mock_db(tmp_path):
    with patch("database.DB_PATH", str(tmp_path / "test.db")):
        yield


@pytest.fixture
def mock_transcriber():
    with patch("bot.transcribe") as mock_tr:
        mock_tr.return_value = "Hello, this is a test transcription."
        yield mock_tr
