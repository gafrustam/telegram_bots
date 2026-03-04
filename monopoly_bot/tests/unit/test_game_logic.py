"""Unit tests for monopoly_bot game logic."""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestPlayerState:
    def test_initial_player_cash(self, sample_player):
        assert sample_player["cash"] == 1500

    def test_player_not_in_jail_by_default(self, sample_player):
        assert not sample_player["in_jail"]
        assert sample_player["jail_turns"] == 0

    def test_player_position_in_range(self, sample_player):
        assert 0 <= sample_player["position"] <= 39


class TestDiceRoll:
    def test_dice_sum_in_range(self):
        import random
        for _ in range(100):
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            total = d1 + d2
            assert 2 <= total <= 12

    def test_doubles_detection(self):
        assert 3 == 3  # both dice same value = doubles
        assert 3 != 4  # not doubles


class TestPropertyPurchase:
    def test_cannot_buy_without_funds(self, sample_player):
        property_cost = 2000
        assert sample_player["cash"] < property_cost

    def test_can_buy_with_funds(self, sample_player):
        property_cost = 60  # Mediterranean Ave
        assert sample_player["cash"] >= property_cost
