import asyncio
import io
import logging

logger = logging.getLogger(__name__)


async def text_to_voice(text: str) -> bytes:
    """Convert English text to OGG Opus bytes for Telegram voice messages (gTTS)."""
    from gtts import gTTS
    from pydub import AudioSegment

    logger.info("TTS request len=%d", len(text))

    def _convert() -> bytes:
        tts = gTTS(text=text, lang="en")
        mp3_buf = io.BytesIO()
        tts.write_to_fp(mp3_buf)
        mp3_buf.seek(0)
        audio = AudioSegment.from_mp3(mp3_buf)
        ogg_buf = io.BytesIO()
        audio.export(ogg_buf, format="ogg", codec="libopus")
        return ogg_buf.getvalue()

    try:
        result = await asyncio.to_thread(_convert)
        logger.info("TTS OK bytes=%d", len(result))
        return result
    except Exception as e:
        logger.error("TTS failed: %s", e)
        raise
