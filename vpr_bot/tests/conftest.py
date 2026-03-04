"""Pytest fixtures for vpr_bot tests."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_pool():
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn), __aexit__=AsyncMock()))
    return pool


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user.id = 123456
    msg.from_user.username = "testuser"
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def mock_state():
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    return state


@pytest.fixture
def sample_problem():
    return {
        "id": 1,
        "grade": 4,
        "topic": "arithmetic",
        "statement": "Вычисли: 15 + 27 = ?",
        "answer": "42",
        "solution": "15 + 27 = 42",
    }
