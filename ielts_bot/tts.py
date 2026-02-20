import asyncio
import io
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


async def text_to_voice(text: str, user_id: int | None = None) -> bytes:
    """Convert text to OGG OPUS audio bytes for Telegram voice messages."""
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    logger.info("%sTTS via provider=%s text_len=%d", uid_tag, provider, len(text))
    try:
        if provider == "google":
            result = await _gtts_text_to_voice(text)
        else:
            result = await _openai_text_to_voice(text)
        logger.info("%sTTS OK bytes=%d", uid_tag, len(result))
        return result
    except Exception as e:
        logger.error("%sTTS failed [provider=%s]: %s", uid_tag, provider, e)
        raise


async def _openai_text_to_voice(text: str) -> bytes:
    client = _get_openai_client()
    model = os.getenv("TTS_MODEL", "tts-1")
    voice = os.getenv("TTS_VOICE", "alloy")
    response = await client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="opus",
    )
    return response.content


async def _gtts_text_to_voice(text: str) -> bytes:
    from gtts import gTTS
    from pydub import AudioSegment

    def _convert() -> bytes:
        tts = gTTS(text=text, lang="en")
        mp3_buf = io.BytesIO()
        tts.write_to_fp(mp3_buf)
        mp3_buf.seek(0)
        audio = AudioSegment.from_mp3(mp3_buf)
        ogg_buf = io.BytesIO()
        audio.export(ogg_buf, format="ogg", codec="libopus")
        return ogg_buf.getvalue()

    return await asyncio.to_thread(_convert)
