"""Pytest fixtures for interview_bot tests."""
import os
import sqlite3
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def test_db(tmp_path):
    """In-memory test database with schema applied."""
    db_path = tmp_path / "test_interview.db"
    conn = sqlite3.connect(str(db_path))
    schema = open(os.path.join(os.path.dirname(__file__), "..", "schema.sql")).read()
    conn.executescript(schema)
    conn.commit()
    yield str(db_path)
    conn.close()


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user.id = 123456
    msg.from_user.username = "testuser"
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    return msg


@pytest.fixture
def sample_problem():
    return {
        "id": 1,
        "title": "Two Sum",
        "description": "Find two numbers that add up to target",
        "difficulty": "intern",
        "examples": '[{"input": "[2,7,11,15], 9", "output": "[0,1]"}]',
        "constraints": "2 <= nums.length <= 10^4",
    }
