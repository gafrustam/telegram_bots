"""AI-based solution feedback for the interview prep bot.

Set AI_PROVIDER=google in .env to use Google Gemini, default is OpenAI.
"""
import json
import logging
import os

from openai import AsyncOpenAI

log = logging.getLogger(__name__)

# ── AI provider config ────────────────────────────────────────────────────────
# Change AI_PROVIDER in .env to switch between openai and google
_GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _get_client() -> AsyncOpenAI:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "google":
        return AsyncOpenAI(
            api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
            base_url=_GOOGLE_BASE_URL,
        )
    return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def _get_model() -> str:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "google":
        return os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.5-flash")
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


SYSTEM_PROMPT = """\
Ты — опытный Senior-инженер и ментор по алгоритмам. Ты оцениваешь решения задач кандидатов.
Будь конструктивным, точным и поддерживающим. Отвечай СТРОГО в формате JSON без markdown-оберток.\
"""

USER_PROMPT_TEMPLATE = """\
ЗАДАЧА: {title}

{description}

Примеры:
{examples}

Ограничения:
{constraints}

Кандидат пишет на языке: {prog_language}

РЕШЕНИЕ КАНДИДАТА:
```
{code}
```

Оцени решение и ответь СТРОГО в формате JSON (без ```json, без пояснений вне JSON):
{{
  "is_correct": true или false,
  "verdict": "одно предложение — верно ли решение и почему",
  "efficiency": "комментарий о сложности по времени и памяти (1-2 предложения)",
  "improvement": "как улучшить, если решение верно но не оптимально. null если уже оптимально",
  "failing_test": "конкретный входной тест-кейс где решение неверно (если is_correct=false), иначе null",
  "mistake": "краткое описание основной ошибки (если is_correct=false), иначе null"
}}
"""

TRANSLATE_PROMPT = """\
Переведи следующий текст с русского на английский. Сохрани форматирование и технические термины.
Верни ТОЛЬКО переведённый текст, без пояснений.

Текст:
{text}
"""


async def check_solution(
    problem: dict,
    code: str,
    prog_language: str,
) -> dict:
    """
    Returns dict with keys:
      is_correct, verdict, efficiency, improvement, failing_test, mistake
    """
    examples_text = "\n".join(
        f"  Вход: {ex['input']} → Выход: {ex['output']}"
        + (f"  ({ex['explanation']})" if ex.get("explanation") else "")
        for ex in problem.get("examples", [])
    )
    constraints_text = "\n".join(f"  • {c}" for c in problem.get("constraints", []))

    prompt = USER_PROMPT_TEMPLATE.format(
        title=problem["title"],
        description=problem["description"],
        examples=examples_text,
        constraints=constraints_text,
        prog_language=prog_language,
        code=code,
    )

    try:
        response = await _get_client().chat.completions.create(
            model=_get_model(),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        raw = response.choices[0].message.content.strip()
        # Strip possible markdown code fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.error("JSON parse error in feedback: %s", e)
        return {
            "is_correct": None,
            "verdict": "Не удалось разобрать ответ AI. Попробуй ещё раз.",
            "efficiency": "",
            "improvement": None,
            "failing_test": None,
            "mistake": None,
        }
    except Exception as e:
        log.exception("AI error in feedback: %s", e)
        return {
            "is_correct": None,
            "verdict": "Ошибка при проверке. Попробуй ещё раз.",
            "efficiency": "",
            "improvement": None,
            "failing_test": None,
            "mistake": None,
        }


async def translate_text(text: str) -> str:
    """Translate Russian text to English."""
    try:
        response = await _get_client().chat.completions.create(
            model=_get_model(),
            messages=[
                {"role": "user", "content": TRANSLATE_PROMPT.format(text=text)},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.exception("Translation error: %s", e)
        return text  # fallback to original
