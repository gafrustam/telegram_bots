import os

from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def text_to_voice(text: str) -> bytes:
    """Convert text to OGG OPUS audio bytes for Telegram voice messages."""
    client = _get_client()
    model = os.getenv("TTS_MODEL", "tts-1")
    voice = os.getenv("TTS_VOICE", "nova")

    response = await client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="opus",
    )
    return response.content
