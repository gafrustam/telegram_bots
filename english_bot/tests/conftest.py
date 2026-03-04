"""Pytest fixtures for english_bot tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user.id = 123456
    msg.from_user.username = "testuser"
    msg.answer = AsyncMock()
    msg.answer_voice = AsyncMock()
    return msg


@pytest.fixture
def mock_state():
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={
        "scenario": "ordering coffee",
        "history": [],
        "session_id": "test-session-123",
    })
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    return state


@pytest.fixture
def mock_db(tmp_path):
    with patch("database.DB_PATH", str(tmp_path / "test.db")):
        yield


@pytest.fixture
def mock_openai():
    with patch("bot.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock()
        mock_client.audio.speech.create = AsyncMock()
        yield mock_client
