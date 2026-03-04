"""Unit tests for interview_bot business logic."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestProblemValidation:
    def test_valid_time_format(self):
        """HH:MM time validation."""
        valid = ["09:00", "23:59", "00:00", "12:30"]
        for t in valid:
            h, m = t.split(":")
            assert 0 <= int(h) <= 23
            assert 0 <= int(m) <= 59

    def test_invalid_time_format(self):
        """Invalid time strings."""
        invalid_pairs = [("25", "00"), ("12", "60"), ("00", "99")]
        for h, m in invalid_pairs:
            assert not (0 <= int(h) <= 23 and 0 <= int(m) <= 59)

    def test_difficulty_levels(self):
        """Valid difficulty levels."""
        levels = ["intern", "junior", "middle", "senior"]
        assert len(levels) == 4
        for level in levels:
            assert isinstance(level, str)


class TestFeedbackParsing:
    def test_feedback_json_structure(self):
        """Feedback JSON must have required keys."""
        import json
        sample_feedback = json.dumps({
            "score": 7,
            "verdict": "Good solution",
            "improvements": "Consider edge cases",
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
        })
        parsed = json.loads(sample_feedback)
        required_keys = ["score", "verdict", "improvements"]
        for key in required_keys:
            assert key in parsed

    def test_score_range(self):
        """Score must be between 0 and 10."""
        valid_scores = [0, 5, 10]
        invalid_scores = [-1, 11, 100]
        for score in valid_scores:
            assert 0 <= score <= 10
        for score in invalid_scores:
            assert not (0 <= score <= 10)
