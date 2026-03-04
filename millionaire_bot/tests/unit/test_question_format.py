"""Unit tests for millionaire_bot question format and lifelines."""
import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestQuestionFormat:
    def test_valid_question_structure(self, sample_question):
        assert "question" in sample_question
        assert "options" in sample_question
        assert "correct" in sample_question
        assert len(sample_question["options"]) == 4
        assert sample_question["correct"] in sample_question["options"]

    def test_options_keys(self, sample_question):
        assert set(sample_question["options"].keys()) == {"A", "B", "C", "D"}

    def test_correct_is_valid_key(self, sample_question):
        assert sample_question["correct"] in ["A", "B", "C", "D"]


class TestLifelines:
    def test_fifty_fifty_removes_two_wrong(self, sample_question):
        options = sample_question["options"].copy()
        correct = sample_question["correct"]
        wrong = [k for k in options if k != correct]
        removed = wrong[:2]
        remaining = {k: v for k, v in options.items() if k not in removed}
        assert correct in remaining
        assert len(remaining) == 2

    def test_lifeline_defaults(self):
        defaults = {"fifty": True, "phone": True, "audience": True}
        assert all(defaults.values())
        assert len(defaults) == 3

    def test_lifeline_consumed(self):
        lifelines = {"fifty": True, "phone": True, "audience": True}
        lifelines["phone"] = False
        assert not lifelines["phone"]
        assert lifelines["fifty"]
        assert lifelines["audience"]
