import asyncio
import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

_openai_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


async def transcribe(path: str, mime: str, user_id: int | None = None) -> str | None:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    uid_tag = f"user_id={user_id} " if user_id else ""
    logger.info("%stranscribing via provider=%s mime=%s", uid_tag, provider, mime)
    try:
        if provider == "google":
            result = await _transcribe_google(path, mime)
        else:
            result = await _transcribe_openai(path)
        if result:
            logger.info("%stranscription OK text_len=%d provider=%s", uid_tag, len(result), provider)
        else:
            logger.warning("%stranscription returned empty result provider=%s", uid_tag, provider)
        return result
    except Exception as e:
        logger.error("%stranscription failed [provider=%s mime=%s]: %s", uid_tag, provider, mime, e)
        return None


async def _transcribe_openai(path: str) -> str | None:
    def _do():
        with open(path, "rb") as f:
            r = _get_openai_client().audio.transcriptions.create(model="whisper-1", file=f)
            return getattr(r, "text", None)
    return await asyncio.to_thread(_do)


async def _transcribe_google(path: str, mime: str) -> str | None:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.0-flash")

    def _do():
        with open(path, "rb") as f:
            audio_bytes = f.read()
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                types.Part.from_text(text="Transcribe the speech in this audio. Return only the transcribed text, nothing else."),
            ],
        )
        return response.text.strip() or None

    return await asyncio.to_thread(_do)
