import asyncio
import base64
import json
import logging
import os
import tempfile

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert English language assessor specializing in shadowing practice evaluation.

Shadowing is a language learning technique where the learner listens to a native speaker and simultaneously (or immediately after) repeats what they hear, trying to match pronunciation, rhythm, and intonation as closely as possible.

You will receive two audio recordings:
1. ORIGINAL: A native English speaker reading a passage at a specified CEFR level
2. USER: A learner's attempt to shadow (repeat) the original passage

Assess the user's shadowing attempt on these five criteria (score each 0.0–10.0, one decimal place):

1. pronunciation: How accurately did the user reproduce English sounds, phonemes, consonant clusters, vowel quality, and word stress? (10 = perfect native-like pronunciation)

2. rhythm: How well did the user match the natural rhythm, pace, weak/strong syllable patterns, and word grouping of the original? (10 = identical rhythm to native)

3. intonation: How accurately did the user replicate the sentence melody, rising/falling patterns, focus stress, and emotional tone? (10 = indistinguishable intonation)

4. fluency: How smoothly and naturally did the user speak? Consider hesitations, false starts, pauses, and flow. (10 = perfectly fluent, no interruptions)

5. overall: Your holistic assessment of how successfully the user shadowed the original. Consider all criteria together. (10 = could be mistaken for a native speaker)

Also provide:
- text_coverage: integer 0–100 representing what percentage of the passage the user attempted to say (100 = complete passage, 50 = only half the words attempted, 0 = silence or completely different content)
- strengths: list of exactly 2–3 specific, positive observations about what the user did well
- improvements: list of exactly 2–3 specific, actionable suggestions for improvement (be concrete, e.g. "Focus on linking words like 'the apple' → 'thee apple'" rather than "work on pronunciation")
- comment: 2–3 encouraging, personalized sentences summarizing performance and motivating continued practice

IMPORTANT:
- Base your assessment ONLY on what you actually hear in the audio recordings
- If the user recording is very short, silent, or contains mostly noise, score text_coverage=0 and other scores appropriately low
- Be honest but encouraging — language learning requires constructive feedback
- Scores should reflect real English proficiency standards (a 7/10 means genuinely good, not mediocre)"""

ASSESSMENT_PROMPT_TEMPLATE = """The original passage (CEFR level: {level}) was:

"{text}"

First audio is the ORIGINAL native speaker recording.
Second audio is the USER's shadowing attempt.

Please assess the user's shadowing performance and return ONLY valid JSON (no markdown, no code fences):
{{
  "pronunciation": <float 0.0-10.0>,
  "rhythm": <float 0.0-10.0>,
  "intonation": <float 0.0-10.0>,
  "fluency": <float 0.0-10.0>,
  "text_coverage": <int 0-100>,
  "overall": <float 0.0-10.0>,
  "strengths": ["...", "...", "..."],
  "improvements": ["...", "...", "..."],
  "comment": "..."
}}"""

_openai_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _openai_client


def _detect_mime_type(audio_bytes: bytes) -> str:
    """Detect audio MIME type from magic bytes."""
    if len(audio_bytes) < 4:
        return "audio/webm"
    if audio_bytes[:4] == b"\x1a\x45\xdf\xa3":
        return "audio/webm"
    if audio_bytes[:4] == b"OggS":
        return "audio/ogg"
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "audio/mp3"
    if audio_bytes[:4] == b"RIFF":
        return "audio/wav"
    if audio_bytes[:4] == b"fLaC":
        return "audio/flac"
    return "audio/webm"


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise


def _convert_to_mp3(audio_bytes: bytes, output_path: str) -> None:
    from pydub import AudioSegment
    import io

    buf = io.BytesIO(audio_bytes)
    audio = AudioSegment.from_file(buf)
    audio.export(output_path, format="mp3", bitrate="64k")


async def assess_shadowing(
    original_audio: bytes,
    user_audio: bytes,
    level: str,
    text: str,
) -> dict:
    """Assess user's shadowing attempt against the original using OpenAI multimodal."""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-audio-preview")
    user_mime = _detect_mime_type(user_audio)
    logger.info("Assessing shadowing level=%s user_mime=%s orig_bytes=%d user_bytes=%d",
                level, user_mime, len(original_audio), len(user_audio))

    with tempfile.TemporaryDirectory() as tmp_dir:
        orig_mp3_path = os.path.join(tmp_dir, "original.mp3")
        user_mp3_path = os.path.join(tmp_dir, "user.mp3")
        await asyncio.to_thread(_convert_to_mp3, original_audio, orig_mp3_path)
        await asyncio.to_thread(_convert_to_mp3, user_audio, user_mp3_path)
        with open(orig_mp3_path, "rb") as f:
            orig_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(user_mp3_path, "rb") as f:
            user_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = ASSESSMENT_PROMPT_TEMPLATE.format(
        level=level,
        text=text[:600] + ("..." if len(text) > 600 else ""),
    )

    content_parts = [
        {"type": "text", "text": "[ORIGINAL RECORDING — native speaker:]"},
        {"type": "input_audio", "input_audio": {"data": orig_b64, "format": "mp3"}},
        {"type": "text", "text": "[USER RECORDING — shadowing attempt:]"},
        {"type": "input_audio", "input_audio": {"data": user_b64, "format": "mp3"}},
        {"type": "text", "text": prompt},
    ]

    client = _get_client()
    response = await client.chat.completions.create(
        model=model, modalities=["text"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content_parts},
        ],
    )
    result = _parse_json(response.choices[0].message.content)

    # Clamp and validate values
    for key in ("pronunciation", "rhythm", "intonation", "fluency", "overall"):
        result[key] = round(max(0.0, min(10.0, float(result.get(key, 0)))), 1)
    result["text_coverage"] = max(0, min(100, int(result.get("text_coverage", 0))))

    if not isinstance(result.get("strengths"), list):
        result["strengths"] = []
    if not isinstance(result.get("improvements"), list):
        result["improvements"] = []
    if not isinstance(result.get("comment"), str):
        result["comment"] = ""

    logger.info("Assessment result overall=%.1f coverage=%d%%",
                result["overall"], result["text_coverage"])
    return result
