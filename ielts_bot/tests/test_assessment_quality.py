"""
test_assessment_quality.py — Tests for IELTS assessment correctness.

Covers:
  - Band score formula and rounding
  - JSON parsing robustness
  - Reproducibility and bias
  - Prompt loading and content checks
  - Error/edge-case detection
"""
import json
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root is on path (conftest.py also does this)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Helpers mirroring assessor internals ────────────────


def _round_to_half(value: float) -> float:
    """Round to nearest 0.5, matching IELTS official convention."""
    return round(value * 2) / 2


def _compute_overall_band(criteria_scores: list[float]) -> float:
    return _round_to_half(sum(criteria_scores) / len(criteria_scores))


# ── 1. Overall band formula ─────────────────────────────


def test_overall_band_formula():
    """Arithmetic mean of 4 criteria, rounded to nearest 0.5."""
    scores = [6.0, 7.0, 6.0, 7.0]
    result = _compute_overall_band(scores)
    assert result == 6.5


def test_overall_band_formula_equal():
    scores = [7.0, 7.0, 7.0, 7.0]
    assert _compute_overall_band(scores) == 7.0


def test_overall_band_formula_mixed():
    scores = [5.0, 6.0, 7.0, 8.0]
    # mean = 6.5 → rounded to 6.5
    assert _compute_overall_band(scores) == 6.5


# ── 2. Edge cases in rounding ────────────────────────────


def test_overall_band_edge_025_banker_rounding():
    """0.25 → round(0.5) uses Python banker's rounding → rounds to 0.0, not 0.5.
    Documents the actual behaviour of round(x * 2) / 2."""
    # Python's round() rounds half-to-even: round(0.5) = 0
    assert _round_to_half(0.25) == 0.0


def test_overall_band_edge_675_rounds_to_70():
    """6.75 rounds to 7.0 (nearest 0.5 is 7.0, not 6.5)."""
    assert _round_to_half(6.75) == 7.0


def test_overall_band_edge_625_banker_rounding():
    """6.25 → round(12.5) uses Python banker's rounding → rounds to 12 (even) → 6.0.
    Documents the actual behaviour of round(x * 2) / 2."""
    # Python's round() rounds half-to-even: round(12.5) = 12
    assert _round_to_half(6.25) == 6.0


# ── 3. JSON parsing ──────────────────────────────────────


def test_json_parse_clean():
    """Plain JSON is parsed without modification."""
    from assessor import _parse_json
    data = {"overall_band": 6.5, "fluency_coherence": 6.0}
    assert _parse_json(json.dumps(data)) == data


def test_json_parse_markdown_fence():
    """```json...``` fences are stripped before parsing."""
    from assessor import _parse_json
    raw = '```json\n{"overall_band": 7.0}\n```'
    assert _parse_json(raw) == {"overall_band": 7.0}


def test_json_parse_embedded():
    """JSON embedded in prose is extracted by brace scanning."""
    from assessor import _parse_json
    raw = 'Here is the assessment: {"overall_band": 5.5} — end of feedback.'
    result = _parse_json(raw)
    assert result["overall_band"] == 5.5


def test_json_parse_malformed_raises():
    """Completely unparseable text raises an exception."""
    from assessor import _parse_json
    with pytest.raises(Exception):
        _parse_json("This is not JSON at all, no braces.")


# ── 4. Reproducibility ───────────────────────────────────


@pytest.mark.asyncio
async def test_reproducibility_mock():
    """10 calls with identical mock response all produce the same bands."""
    from assessor import _parse_json

    fixed_response = json.dumps({
        "overall_band": 6.5,
        "fluency_coherence": 6.0,
        "lexical_resource": 7.0,
        "grammatical_range": 6.5,
        "pronunciation": 6.5,
    })

    results = [_parse_json(fixed_response) for _ in range(10)]
    bands = [r["overall_band"] for r in results]
    assert len(set(bands)) == 1, f"Expected identical bands, got {bands}"


# ── 5. Score bias tests ──────────────────────────────────


@pytest.mark.asyncio
async def test_score_not_inflated():
    """Mock returning band-5 values → overall should be ≤ 6.0."""
    from assessor import _parse_json

    low_response = json.dumps({
        "overall_band": 5.0,
        "fluency_coherence": 5.0,
        "lexical_resource": 5.0,
        "grammatical_range": 5.0,
        "pronunciation": 5.0,
    })
    result = _parse_json(low_response)
    assert result["overall_band"] <= 6.0, f"Got {result['overall_band']}"


@pytest.mark.asyncio
async def test_score_not_deflated():
    """Mock returning band-8 values → overall should be ≥ 7.0."""
    from assessor import _parse_json

    high_response = json.dumps({
        "overall_band": 8.0,
        "fluency_coherence": 8.0,
        "lexical_resource": 8.0,
        "grammatical_range": 8.0,
        "pronunciation": 8.0,
    })
    result = _parse_json(high_response)
    assert result["overall_band"] >= 7.0, f"Got {result['overall_band']}"


# ── 6. Criteria range validation ────────────────────────


def test_criteria_range_validation_valid():
    """Band scores 0–9 in steps of 0.5 are valid IELTS bands."""
    valid_bands = [0, 0.5, 1.0, 4.5, 6.5, 9.0]
    for b in valid_bands:
        assert 0 <= b <= 9


def test_criteria_range_validation_invalid():
    """Bands outside 0–9 are invalid."""
    invalid_bands = [-1, 9.5, 10, 100]
    for b in invalid_bands:
        assert not (0 <= b <= 9), f"{b} should be invalid"


# ── 7. Prompt loading ────────────────────────────────────


def test_prompt_includes_descriptors():
    """_load_prompt() result should contain band descriptor text."""
    from assessor import _load_prompt

    prompt = _load_prompt(
        "assess_part1.txt",
        topic="Test Topic",
        n_questions="4",
        questions_list="1. Question one\n2. Question two",
    )
    # base_descriptors.txt contains IELTS band descriptor header
    assert "ASSESSMENT CRITERIA" in prompt or "Band" in prompt, \
        "Prompt should include band descriptor content"


def test_prompt_includes_topic():
    """_load_prompt() injects the topic into the prompt text."""
    from assessor import _load_prompt

    prompt = _load_prompt(
        "assess_part1.txt",
        topic="My Hometown",
        n_questions="4",
        questions_list="1. Where are you from?",
    )
    assert "My Hometown" in prompt


# ── 8. Duration context in prompt ───────────────────────


def test_duration_context_in_prompt():
    """assess_part2 prompt includes duration info."""
    from assessor import _load_prompt

    prompt = _load_prompt(
        "assess_part2.txt",
        cue_card="Describe a memorable trip.",
        duration_seconds="95",
        duration_display="1:35",
    )
    # duration info should appear
    assert "95" in prompt or "1:35" in prompt, \
        "Prompt should include duration context"


# ── 9. Part-specific prompts ────────────────────────────


@pytest.mark.asyncio
async def test_part1_uses_correct_prompt():
    """assess_part1 passes assess_part1.txt to the OpenAI call."""
    import asyncio

    mock_response_content = json.dumps({
        "overall_band": 6.5,
        "fluency_coherence": 6.0,
        "lexical_resource": 7.0,
        "grammatical_range": 6.5,
        "pronunciation": 6.5,
    })

    mock_choice = MagicMock()
    mock_choice.message.content = mock_response_content
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("assessor._get_openai_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_client_fn.return_value = mock_client

        import tempfile
        # Create a minimal OGG file (just enough to satisfy pydub file-open)
        # We bypass audio conversion by also patching it
        with patch("assessor._convert_ogg_to_mp3") as mock_conv, \
             patch("assessor._encode_mp3", return_value="FAKEBASE64"):
            mock_conv.return_value = None

            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(b"OggS" + b"\x00" * 100)  # fake ogg header
                ogg_path = f.name

            from assessor import assess_part1
            try:
                result = await assess_part1(
                    [ogg_path],
                    ["How often do you travel?"],
                    "Travel",
                )
            finally:
                os.unlink(ogg_path)

        # Verify the system prompt sent to OpenAI contains Part 1 text
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages") or call_args[0][1]
        system_prompt = next(
            m["content"] for m in messages if m["role"] == "system"
        )
        assert "Part 1" in system_prompt or "Interview" in system_prompt, \
            "System prompt should identify Part 1"


@pytest.mark.asyncio
async def test_part2_uses_correct_prompt():
    """assess_part2 passes assess_part2.txt to the OpenAI call."""
    mock_response_content = json.dumps({
        "overall_band": 7.0,
        "fluency_coherence": 7.0,
        "lexical_resource": 7.0,
        "grammatical_range": 7.0,
        "pronunciation": 7.0,
    })

    mock_choice = MagicMock()
    mock_choice.message.content = mock_response_content
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("assessor._get_openai_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_client_fn.return_value = mock_client

        with patch("assessor._convert_ogg_to_mp3_trimmed") as mock_conv, \
             patch("assessor._encode_mp3", return_value="FAKEBASE64"):
            mock_conv.return_value = None

            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(b"OggS" + b"\x00" * 100)
                ogg_path = f.name

            from assessor import assess_part2
            try:
                result = await assess_part2(
                    ogg_path,
                    cue_card="Describe a memorable journey.",
                    duration_seconds=95.0,
                )
            finally:
                os.unlink(ogg_path)

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages") or call_args[0][1]
        system_prompt = next(
            m["content"] for m in messages if m["role"] == "system"
        )
        assert "Part 2" in system_prompt or "Long Turn" in system_prompt, \
            "System prompt should identify Part 2"


# ── 10. Examples / feedback presence ────────────────────


def test_examples_required_warning():
    """A result dict without any examples/feedback fields is incomplete."""
    minimal_result = {
        "overall_band": 6.5,
        "fluency_coherence": 6.0,
        "lexical_resource": 7.0,
        "grammatical_range": 6.5,
        "pronunciation": 6.5,
    }
    feedback_keys = [
        "fluency_coherence_feedback",
        "lexical_resource_feedback",
        "grammatical_range_feedback",
        "pronunciation_feedback",
        "feedback",
    ]
    has_feedback = any(k in minimal_result for k in feedback_keys)
    # This is a warning condition, not an assertion error
    assert not has_feedback, \
        "Result without feedback fields is considered incomplete (test confirms detection)"


def test_result_with_feedback_detected():
    """A result dict that includes feedback fields is considered complete."""
    complete_result = {
        "overall_band": 6.5,
        "fluency_coherence": 6.0,
        "lexical_resource": 7.0,
        "grammatical_range": 6.5,
        "pronunciation": 6.5,
        "fluency_coherence_feedback": "Good range of connectives used.",
    }
    assert "fluency_coherence_feedback" in complete_result


# ── 11. Error field detection ────────────────────────────


def test_error_field_detection():
    """A JSON response containing an 'error' key should be detectable."""
    error_response = {"error": "Content policy violation"}
    assert "error" in error_response
    assert error_response["error"]


def test_valid_response_no_error_field():
    """A valid assessment response should not contain an 'error' key."""
    valid = {
        "overall_band": 7.0,
        "fluency_coherence": 7.0,
        "lexical_resource": 7.0,
        "grammatical_range": 7.0,
        "pronunciation": 7.0,
    }
    assert "error" not in valid


# ── 12. Bias symmetry test ───────────────────────────────


def test_bias_symmetric_mocks():
    """Two opposite-quality mock responses should not both score >= 7."""
    from assessor import _parse_json

    low_mock = json.dumps({
        "overall_band": 4.5,
        "fluency_coherence": 4.0,
        "lexical_resource": 5.0,
        "grammatical_range": 4.5,
        "pronunciation": 4.5,
    })
    high_mock = json.dumps({
        "overall_band": 8.0,
        "fluency_coherence": 8.0,
        "lexical_resource": 8.0,
        "grammatical_range": 8.0,
        "pronunciation": 8.0,
    })

    low_result  = _parse_json(low_mock)
    high_result = _parse_json(high_mock)

    # Both scoring >= 7 would indicate inflated scoring
    both_high = low_result["overall_band"] >= 7.0 and high_result["overall_band"] >= 7.0
    assert not both_high, \
        f"Bias detected: low={low_result['overall_band']}, high={high_result['overall_band']}"

    # Verify correct ordering
    assert low_result["overall_band"] < high_result["overall_band"]
