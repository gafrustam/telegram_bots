"""Pytest fixtures for poker_bot tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from poker_engine import PokerGame


@pytest.fixture
def fresh_game():
    """New PokerGame instance with default stack."""
    return PokerGame(player_stack=1000, ai_stack=1000)


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock(return_value={"type": "fold"})
    return ws


@pytest.fixture
def mock_ai_player():
    ai = AsyncMock()
    ai.decide = AsyncMock(return_value={"action": "call", "amount": 0})
    return ai


@pytest.fixture
def mock_db():
    with patch("database.init_db", new_callable=AsyncMock):
        with patch("database.save_game", new_callable=AsyncMock):
            with patch("database.load_game", new_callable=AsyncMock, return_value=None):
                with patch("database.update_stats", new_callable=AsyncMock):
                    yield
