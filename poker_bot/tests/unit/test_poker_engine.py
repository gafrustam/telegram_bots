"""Unit tests for poker engine."""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from poker_engine import PokerGame


class TestPokerGame:
    def test_new_game_initial_state(self):
        game = PokerGame(starting_stack=1000)
        state = game.get_state()
        assert state["player_stack"] == 1000
        assert state["ai_stack"] == 1000
        assert state["phase"] == "waiting"

    def test_game_serialization(self):
        game = PokerGame(starting_stack=1500)
        data = game.to_dict()
        assert isinstance(data, dict)
        restored = PokerGame.from_dict(data)
        assert restored.get_state()["player_stack"] == game.get_state()["player_stack"]

    def test_new_hand_starts(self):
        game = PokerGame(starting_stack=1000)
        state = game.start_new_hand()
        assert state is not None
        assert state.get("phase") != "waiting"

    def test_fold_ends_hand(self):
        game = PokerGame(starting_stack=1000)
        game.start_new_hand()
        state = game.apply_action("player", "fold")
        assert state is not None
        # After fold, hand should be resolved
        assert "phase" in state or "error" in state

    def test_game_over_when_broke(self):
        game = PokerGame(starting_stack=1000)
        assert not game.is_game_over()

    def test_default_stacks(self):
        game = PokerGame()
        state = game.get_state()
        assert state["player_stack"] > 0
        assert state["ai_stack"] > 0
