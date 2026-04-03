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
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _openai_client


async def _tts_openai(text: str) -> bytes:
    model = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
    voice = os.getenv("TTS_VOICE", "alloy")
    response = await _get_openai_client().audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3",
    )
    return response.content


async def _tts_google(text: str) -> bytes:
    """Convert text to MP3 using gTTS."""
    from gtts import gTTS
    from pydub import AudioSegment

    def _convert() -> bytes:
        tts = gTTS(text=text, lang="en")
        mp3_buf = io.BytesIO()
        tts.write_to_fp(mp3_buf)
        mp3_buf.seek(0)
        # Re-encode to ensure valid MP3
        audio = AudioSegment.from_mp3(mp3_buf)
        out = io.BytesIO()
        audio.export(out, format="mp3", bitrate="64k")
        return out.getvalue()

    return await asyncio.to_thread(_convert)


async def text_to_speech(text: str) -> bytes:
    """Convert text to MP3 audio bytes."""
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    logger.info("TTS provider=%s text_len=%d", provider, len(text))
    if provider == "google":
        audio = await _tts_google(text)
    else:
        audio = await _tts_openai(text)
    logger.info("TTS done bytes=%d", len(audio))
    return audio
