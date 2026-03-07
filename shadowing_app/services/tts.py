import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _client


async def text_to_speech(text: str) -> bytes:
    """Convert text to MP3 audio bytes using OpenAI TTS."""
    model = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
    voice = os.getenv("TTS_VOICE", "alloy")

    logger.info("TTS model=%s voice=%s text_len=%d", model, voice, len(text))

    response = await _get_client().audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3",
    )
    audio = response.content
    logger.info("TTS done bytes=%d", len(audio))
    return audio
