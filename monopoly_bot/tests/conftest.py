"""Pytest fixtures for monopoly_bot tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(return_value='{"type": "ping"}')
    return ws


@pytest.fixture
def sample_player():
    return {
        "id": "player_1",
        "name": "TestPlayer",
        "cash": 1500,
        "position": 0,
        "properties": [],
        "in_jail": False,
        "jail_turns": 0,
    }


@pytest.fixture
def mock_db():
    with patch("database.init_db", new_callable=AsyncMock):
        with patch("database.record_visit", new_callable=AsyncMock):
            yield
