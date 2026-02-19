"""
Unit tests for keyboards.py — keyboard builders and admin button visibility.
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from keyboards import (
    ADMIN_BTN,
    PART1_BTN,
    PART2_BTN,
    PART3_BTN,
    STATS_BTN,
    interrupt_keyboard,
    main_menu_keyboard,
    results_keyboard,
    topic_keyboard,
)
from states import InterruptAction, ResultAction, TopicAction


# ── main_menu_keyboard ───────────────────────────────────

class TestMainMenuKeyboard:
    def test_regular_user_has_4_rows(self):
        kb = main_menu_keyboard(is_admin=False)
        assert len(kb.keyboard) == 4

    def test_admin_user_has_5_rows(self):
        kb = main_menu_keyboard(is_admin=True)
        assert len(kb.keyboard) == 5

    def test_admin_row_contains_admin_button(self):
        kb = main_menu_keyboard(is_admin=True)
        last_row = kb.keyboard[-1]
        texts = [btn.text for btn in last_row]
        assert ADMIN_BTN in texts

    def test_admin_button_not_present_for_regular_user(self):
        kb = main_menu_keyboard(is_admin=False)
        all_texts = [btn.text for row in kb.keyboard for btn in row]
        assert ADMIN_BTN not in all_texts

    def test_all_part_buttons_present(self):
        kb = main_menu_keyboard()
        all_texts = [btn.text for row in kb.keyboard for btn in row]
        assert PART1_BTN in all_texts
        assert PART2_BTN in all_texts
        assert PART3_BTN in all_texts

    def test_stats_button_present(self):
        kb = main_menu_keyboard()
        all_texts = [btn.text for row in kb.keyboard for btn in row]
        assert STATS_BTN in all_texts

    def test_resize_keyboard_is_true(self):
        kb = main_menu_keyboard()
        assert kb.resize_keyboard is True


# ── topic_keyboard ───────────────────────────────────────

class TestTopicKeyboard:
    def test_has_three_buttons(self):
        kb = topic_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert len(all_buttons) == 3

    def test_accept_button_callback(self):
        kb = topic_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        accept_cb = TopicAction(action="accept").pack()
        assert accept_cb in callbacks

    def test_another_button_callback(self):
        kb = topic_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        another_cb = TopicAction(action="another").pack()
        assert another_cb in callbacks

    def test_custom_button_callback(self):
        kb = topic_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        custom_cb = TopicAction(action="custom").pack()
        assert custom_cb in callbacks


# ── results_keyboard ─────────────────────────────────────

class TestResultsKeyboard:
    def test_has_two_buttons(self):
        kb = results_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert len(all_buttons) == 2

    def test_retry_button_callback(self):
        kb = results_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        retry_cb = ResultAction(action="retry").pack()
        assert retry_cb in callbacks

    def test_menu_button_callback(self):
        kb = results_keyboard()
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        menu_cb = ResultAction(action="menu").pack()
        assert menu_cb in callbacks


# ── interrupt_keyboard ───────────────────────────────────

class TestInterruptKeyboard:
    def test_has_two_buttons(self):
        kb = interrupt_keyboard(new_part=1)
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert len(all_buttons) == 2

    def test_continue_button_callback(self):
        kb = interrupt_keyboard(new_part=2)
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        continue_cb = InterruptAction(action="continue", new_part=2).pack()
        assert continue_cb in callbacks

    def test_new_part_button_callback(self):
        kb = interrupt_keyboard(new_part=3)
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        new_cb = InterruptAction(action="new", new_part=3).pack()
        assert new_cb in callbacks

    def test_new_part_label_shown(self):
        kb = interrupt_keyboard(new_part=2)
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        texts = [btn.text for btn in all_buttons]
        assert any("Part 2" in t for t in texts)

    @pytest.mark.parametrize("part", [1, 2, 3])
    def test_different_parts(self, part):
        kb = interrupt_keyboard(new_part=part)
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for btn in all_buttons]
        new_cb = InterruptAction(action="new", new_part=part).pack()
        assert new_cb in callbacks


# ── callback data round-trip ─────────────────────────────

class TestCallbackDataRoundTrip:
    def test_topic_action_accept_roundtrip(self):
        packed = TopicAction(action="accept").pack()
        unpacked = TopicAction.unpack(packed)
        assert unpacked.action == "accept"

    def test_topic_action_another_roundtrip(self):
        packed = TopicAction(action="another").pack()
        unpacked = TopicAction.unpack(packed)
        assert unpacked.action == "another"

    def test_result_action_retry_roundtrip(self):
        packed = ResultAction(action="retry").pack()
        unpacked = ResultAction.unpack(packed)
        assert unpacked.action == "retry"

    def test_result_action_menu_roundtrip(self):
        packed = ResultAction(action="menu").pack()
        unpacked = ResultAction.unpack(packed)
        assert unpacked.action == "menu"

    def test_interrupt_action_roundtrip(self):
        packed = InterruptAction(action="new", new_part=2).pack()
        unpacked = InterruptAction.unpack(packed)
        assert unpacked.action == "new"
        assert unpacked.new_part == 2


# ── _is_admin logic (pure function, tested inline) ───────

class TestIsAdminLogic:
    """
    Tests the _is_admin business logic without importing bot.py.
    Mirrors the exact logic from bot.py:
        def _is_admin(user_id=0, username=None):
            if user_id and user_id in _admin_ids:
                return True
            return ADMIN_USERNAME is not None and bool(username) and username.lower() == ADMIN_USERNAME
    """

    def _make_is_admin(self, admin_username, admin_ids):
        def is_admin(user_id=0, username=None):
            if user_id and user_id in admin_ids:
                return True
            return (
                admin_username is not None
                and bool(username)
                and username.lower() == admin_username
            )
        return is_admin

    def test_returns_false_when_no_admin_configured(self):
        is_admin = self._make_is_admin(None, set())
        assert is_admin(0, "anyone") is False

    def test_returns_true_for_matching_username(self):
        is_admin = self._make_is_admin("testadmin", set())
        assert is_admin(0, "testadmin") is True

    def test_case_insensitive_username_match(self):
        is_admin = self._make_is_admin("testadmin", set())
        assert is_admin(0, "TESTADMIN") is True
        assert is_admin(0, "TestAdmin") is True

    def test_returns_false_for_wrong_username(self):
        is_admin = self._make_is_admin("testadmin", set())
        assert is_admin(0, "other") is False

    def test_returns_true_for_cached_admin_id(self):
        is_admin = self._make_is_admin("testadmin", {42})
        assert is_admin(42) is True

    def test_returns_false_for_unknown_user_id(self):
        is_admin = self._make_is_admin("testadmin", {42})
        assert is_admin(99) is False

    def test_returns_false_for_zero_user_id(self):
        is_admin = self._make_is_admin("testadmin", {42})
        assert is_admin(0) is False

    def test_returns_false_for_none_username(self):
        is_admin = self._make_is_admin("testadmin", set())
        assert is_admin(0, None) is False
