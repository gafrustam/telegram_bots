"""Pytest fixtures for millionaire_bot tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user.id = 123456
    msg.from_user.username = "testuser"
    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    return msg


@pytest.fixture
def mock_callback():
    cb = MagicMock()
    cb.from_user.id = 123456
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    return cb


@pytest.fixture
def mock_state():
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={
        "level": 1,
        "question": "What is 2+2?",
        "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
        "correct": "B",
        "lifelines": {"fifty": True, "phone": True, "audience": True},
        "msg_id": 999,
    })
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    return state


@pytest.fixture
def sample_question():
    return {
        "question": "What is the capital of France?",
        "options": {"A": "London", "B": "Berlin", "C": "Paris", "D": "Madrid"},
        "correct": "C",
    }


@pytest.fixture
def mock_openai():
    with patch("questions.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        yield mock_client
