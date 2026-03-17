"""
Integration latency tests for Spanish bot.

Measures real API response times for:
  1. Scenario generation (when user requests "Nuevo dialogo")
  2. Audio response pipeline:
       - voice transcription (Whisper / Gemini)
       - conversation reply generation (GPT / Gemini)
       - TTS (OpenAI / gTTS)
       - total round-trip from user audio → bot voice

Run:
  cd /home/ubuntu/telegram_bots/spanish_bot
  source venv/bin/activate
  python -m pytest tests/integration/test_response_latency.py -v -s
"""

import asyncio
import io
import os
import sys
import time

import pytest

# Allow imports from the bot root
_BOT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _BOT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_BOT_ROOT, ".env"))

from difficulty import get_level
from assessor import generate_scenario, get_conversation_reply, transcribe_voice
from tts import text_to_voice

# Hard time limits (seconds) — fail the test if exceeded
LIMIT_SCENARIO = 60
LIMIT_TRANSCRIPTION = 60
LIMIT_REPLY = 30
LIMIT_TTS = 30
LIMIT_TOTAL_PIPELINE = 120


# ── Fixtures ────────────────────────────────────────────────────────────────


def _make_ogg_audio() -> bytes:
    """Generate a short Spanish phrase as OGG audio (used as fake user voice)."""
    from gtts import gTTS
    from pydub import AudioSegment

    tts = gTTS(text="Trabajo como programador y me gusta mucho mi trabajo.", lang="es")
    mp3_buf = io.BytesIO()
    tts.write_to_fp(mp3_buf)
    mp3_buf.seek(0)
    audio = AudioSegment.from_mp3(mp3_buf)
    ogg_buf = io.BytesIO()
    audio.export(ogg_buf, format="ogg", codec="libopus")
    return ogg_buf.getvalue()


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def test_audio_ogg():
    """OGG audio bytes of a Spanish phrase for transcription tests."""
    print("\n[fixture] Generating test audio OGG...", flush=True)
    data = _make_ogg_audio()
    print(f"[fixture] Audio generated: {len(data)} bytes", flush=True)
    return data


@pytest.fixture(scope="module")
def level_b1():
    return get_level(12)  # B1 level — realistic mid-difficulty


GRAMMAR_OVERRIDE = "presente de indicativo, pretérito indefinido"  # passed explicitly since DifficultyLevel has no .grammar field


def _provider() -> str:
    return os.getenv("AI_PROVIDER", "openai").upper()


# ── Scenario generation ─────────────────────────────────────────────────────


class TestScenarioGenerationLatency:
    """Time how long it takes to generate a conversation topic + scenario."""

    def test_scenario_generation_time(self, event_loop, level_b1):
        async def _run():
            t0 = time.perf_counter()
            result = await generate_scenario(level_b1, "My Dream Job", grammar_override=GRAMMAR_OVERRIDE)
            elapsed = time.perf_counter() - t0

            print(
                f"\n{'='*60}\n"
                f"  SCENARIO GENERATION  [{_provider()}]\n"
                f"{'='*60}\n"
                f"  Time:  {elapsed:.2f}s\n"
                f"  Topic: {result.get('topic', 'N/A')}\n"
                f"  Vocab words: {len(result.get('vocabulary', []))}\n"
                f"{'='*60}"
            )
            return elapsed, result

        elapsed, result = event_loop.run_until_complete(_run())

        assert isinstance(result, dict), "generate_scenario should return a dict"
        assert "scenario" in result, "Result must contain 'scenario' key"
        assert elapsed < LIMIT_SCENARIO, f"Scenario generation too slow: {elapsed:.2f}s (limit: {LIMIT_SCENARIO}s)"


# ── Audio response pipeline ─────────────────────────────────────────────────


class TestAudioResponsePipelineLatency:
    """Time each stage from user voice → bot voice reply."""

    def test_transcription_time(self, event_loop, test_audio_ogg):
        async def _run():
            t0 = time.perf_counter()
            text = await transcribe_voice(test_audio_ogg)
            elapsed = time.perf_counter() - t0

            print(
                f"\n{'='*60}\n"
                f"  TRANSCRIPTION  [{_provider()}]\n"
                f"{'='*60}\n"
                f"  Time:       {elapsed:.2f}s\n"
                f"  Transcript: '{text}'\n"
                f"{'='*60}"
            )
            return elapsed, text

        elapsed, text = event_loop.run_until_complete(_run())

        assert isinstance(text, str)
        assert len(text) > 0, "Transcript must not be empty"
        assert elapsed < LIMIT_TRANSCRIPTION, f"Transcription too slow: {elapsed:.2f}s (limit: {LIMIT_TRANSCRIPTION}s)"

    def test_conversation_reply_time(self, event_loop, level_b1):
        async def _run():
            history = [
                {"role": "assistant", "content": "¡Hola! ¿De qué trabajas ahora?"},
                {"role": "user", "content": "Trabajo como programador en una empresa de tecnología."},
            ]
            t0 = time.perf_counter()
            reply = await get_conversation_reply(
                history=history,
                level=level_b1,
                scenario="Discussing your dream job and career aspirations.",
                exchanges_left=3,
                grammar_override=GRAMMAR_OVERRIDE,
            )
            elapsed = time.perf_counter() - t0

            print(
                f"\n{'='*60}\n"
                f"  CONVERSATION REPLY  [{_provider()}]\n"
                f"{'='*60}\n"
                f"  Time:  {elapsed:.2f}s\n"
                f"  Reply: '{reply[:100]}'\n"
                f"{'='*60}"
            )
            return elapsed, reply

        elapsed, reply = event_loop.run_until_complete(_run())

        assert isinstance(reply, str)
        assert len(reply) > 0, "Reply must not be empty"
        assert elapsed < LIMIT_REPLY, f"Conversation reply too slow: {elapsed:.2f}s (limit: {LIMIT_REPLY}s)"

    def test_tts_time(self, event_loop):
        async def _run():
            text = "¡Muy interesante! ¿Y cuáles son tus planes para el futuro en la empresa?"
            t0 = time.perf_counter()
            audio = await text_to_voice(text)
            elapsed = time.perf_counter() - t0

            print(
                f"\n{'='*60}\n"
                f"  TEXT-TO-SPEECH  [{_provider()}]\n"
                f"{'='*60}\n"
                f"  Time:  {elapsed:.2f}s\n"
                f"  Bytes: {len(audio)}\n"
                f"{'='*60}"
            )
            return elapsed, audio

        elapsed, audio = event_loop.run_until_complete(_run())

        assert isinstance(audio, bytes)
        assert len(audio) > 0, "TTS output must not be empty"
        assert elapsed < LIMIT_TTS, f"TTS too slow: {elapsed:.2f}s (limit: {LIMIT_TTS}s)"

    def test_full_audio_pipeline_time(self, event_loop, test_audio_ogg, level_b1):
        """
        Measures the total latency a user experiences after sending a voice message:
          1. Transcribe user audio
          2. Generate bot reply text
          3. Convert reply to voice (TTS)
        """
        async def _run():
            history = [
                {"role": "assistant", "content": "¡Hola! Cuéntame sobre tu trabajo ideal."},
            ]

            pipeline_start = time.perf_counter()

            # Step 1: Transcribe user audio
            t0 = time.perf_counter()
            user_text = await transcribe_voice(test_audio_ogg)
            transcribe_time = time.perf_counter() - t0

            history.append({"role": "user", "content": user_text})

            # Step 2: Get bot reply
            t0 = time.perf_counter()
            bot_reply = await get_conversation_reply(
                history=history,
                level=level_b1,
                scenario="Discussing your dream job.",
                exchanges_left=3,
                grammar_override=GRAMMAR_OVERRIDE,
            )
            reply_time = time.perf_counter() - t0

            # Step 3: TTS
            t0 = time.perf_counter()
            audio = await text_to_voice(bot_reply)
            tts_time = time.perf_counter() - t0

            total_time = time.perf_counter() - pipeline_start

            print(
                f"\n{'='*60}\n"
                f"  FULL AUDIO PIPELINE BREAKDOWN  [{_provider()}]\n"
                f"{'='*60}\n"
                f"  1. Transcription:     {transcribe_time:>6.2f}s\n"
                f"  2. Conversation reply:{reply_time:>6.2f}s\n"
                f"  3. TTS:               {tts_time:>6.2f}s\n"
                f"  {'─'*40}\n"
                f"  TOTAL:                {total_time:>6.2f}s\n"
                f"{'='*60}\n"
                f"  User said: '{user_text[:70]}'\n"
                f"  Bot said:  '{bot_reply[:70]}'"
            )
            return total_time, transcribe_time, reply_time, tts_time

        total, t_transcribe, t_reply, t_tts = event_loop.run_until_complete(_run())

        assert total < LIMIT_TOTAL_PIPELINE, f"Full pipeline too slow: {total:.2f}s (limit: {LIMIT_TOTAL_PIPELINE}s)"
