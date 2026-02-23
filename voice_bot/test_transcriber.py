"""
Integration test: sends a real voice message to the bot and checks transcription.

Usage:
    python test_transcriber.py

Requires BOT_TOKEN and a TEST_CHAT_ID in the .env (or env vars).
TEST_CHAT_ID is the Telegram user ID that will receive the test voice message.
"""
import asyncio
import io
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

# ── Silence gtts/genai import noise ────────────────────
import warnings
warnings.filterwarnings("ignore")


async def _send_and_wait(bot_token: str, chat_id: int, ogg_bytes: bytes) -> str | None:
    """Send a voice file to the chat and wait for the bot's text reply."""
    from telegram import Bot
    from telegram.error import TelegramError

    bot = Bot(token=bot_token)

    # Send as voice
    voice_buf = io.BytesIO(ogg_bytes)
    voice_buf.name = "test.ogg"
    sent = await bot.send_voice(chat_id=chat_id, voice=voice_buf)

    # Poll for bot reply (the bot should echo back the transcription)
    deadline = time.time() + 30
    last_id = sent.message_id
    while time.time() < deadline:
        await asyncio.sleep(2)
        try:
            updates = await bot.get_updates(offset=0, limit=10, timeout=5)
            for upd in updates:
                if (
                    upd.message
                    and upd.message.chat_id == chat_id
                    and upd.message.message_id > last_id
                    and upd.message.text
                ):
                    return upd.message.text
        except TelegramError:
            pass
    return None


def _make_test_ogg(text: str = "Hello, this is a test.") -> bytes:
    """Create a short OGG voice file from text using gTTS."""
    import io
    from gtts import gTTS
    from pydub import AudioSegment

    tts = gTTS(text=text, lang="en")
    mp3_buf = io.BytesIO()
    tts.write_to_fp(mp3_buf)
    mp3_buf.seek(0)
    audio = AudioSegment.from_mp3(mp3_buf)
    ogg_buf = io.BytesIO()
    audio.export(ogg_buf, format="ogg", codec="libopus")
    return ogg_buf.getvalue()


async def test_direct_transcription():
    """Test transcriber.py directly without going through Telegram."""
    import tempfile
    from transcriber import transcribe

    print("\n=== Direct transcription test ===")

    test_text = "Hello, this is a transcription test."
    print(f"  Generating speech for: '{test_text}'")
    ogg_bytes = _make_test_ogg(test_text)
    print(f"  Generated {len(ogg_bytes)} bytes of OGG audio")

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(ogg_bytes)
        tmp_path = f.name

    try:
        provider = os.getenv("AI_PROVIDER", "openai")
        print(f"  Transcribing via provider={provider} ...")
        t0 = time.time()
        result = await transcribe(tmp_path, mime="audio/ogg", user_id=0)
        elapsed = time.time() - t0

        if result:
            print(f"  ✓ Transcription OK in {elapsed:.1f}s: '{result}'")
            return True
        else:
            print(f"  ✗ Transcription returned empty result after {elapsed:.1f}s")
            return False
    except Exception as e:
        print(f"  ✗ Transcription error: {e}")
        return False
    finally:
        os.unlink(tmp_path)


async def test_both_providers():
    """Test transcription with both OpenAI and Google providers."""
    import tempfile
    from transcriber import transcribe

    print("\n=== Both providers test ===")
    test_text = "The quick brown fox jumps over the lazy dog."
    ogg_bytes = _make_test_ogg(test_text)

    results = {}
    for provider in ("openai", "google"):
        os.environ["AI_PROVIDER"] = provider
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(ogg_bytes)
            tmp_path = f.name
        try:
            print(f"  Testing provider={provider} ...")
            t0 = time.time()
            result = await transcribe(tmp_path, mime="audio/ogg", user_id=0)
            elapsed = time.time() - t0
            if result:
                print(f"    ✓ {provider}: '{result}' ({elapsed:.1f}s)")
                results[provider] = True
            else:
                print(f"    ✗ {provider}: empty result ({elapsed:.1f}s)")
                results[provider] = False
        except Exception as e:
            print(f"    ✗ {provider}: {e}")
            results[provider] = False
        finally:
            os.unlink(tmp_path)

    # Restore original provider
    original = os.getenv("AI_PROVIDER", "openai")
    os.environ["AI_PROVIDER"] = original
    return results


async def main():
    print("Voice bot transcriber integration tests")
    print("=" * 40)

    all_ok = True

    # Test 1: direct transcription with current provider
    ok = await test_direct_transcription()
    all_ok = all_ok and ok

    # Test 2: both providers
    results = await test_both_providers()
    for provider, ok in results.items():
        all_ok = all_ok and ok

    print("\n" + "=" * 40)
    if all_ok:
        print("✓ All tests passed")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
