"""
AI-based task generation, theory generation, and answer evaluation.
"""

import json
import logging
import os
import re

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, GOOGLE_AI_API_KEY, AI_PROVIDER

logger = logging.getLogger(__name__)

_GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
_GOOGLE_MODEL = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.0-flash")


def _get_client() -> AsyncOpenAI:
    if AI_PROVIDER.lower() == "google":
        return AsyncOpenAI(api_key=GOOGLE_AI_API_KEY, base_url=_GOOGLE_BASE_URL)
    return AsyncOpenAI(api_key=OPENAI_API_KEY)


def _get_model() -> str:
    return _GOOGLE_MODEL if AI_PROVIDER.lower() == "google" else OPENAI_MODEL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Extract first JSON object from a string (handles markdown code blocks)."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Find first { ... }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in: {text[:200]}")
    return json.loads(text[start:end])


async def _chat(system: str, user: str, temperature: float = 0.8) -> str:
    response = await _get_client().chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Task generation
# ---------------------------------------------------------------------------

TASK_SYSTEM = (
    "Ты — опытный учитель математики, составляющий задания для ВПР "
    "(Всероссийской проверочной работы). "
    "Задания должны точно соответствовать официальным демоверсиям ВПР, "
    "быть чёткими, однозначными и иметь конкретный числовой ответ. "
    "Отвечай ТОЛЬКО валидным JSON без дополнительных пояснений."
)

TASK_USER_TEMPLATE = """
Создай задание для ВПР по математике.

Класс: {grade}
Номер задания: {task_num}
Тема задания: {topic}
Подсказка к типу: {hint}

Верни JSON строго в формате:
{{
  "task_text": "Полный текст задания для ученика (без ответа)",
  "correct_answer": "Точный правильный ответ (число, выражение или краткая фраза)",
  "solution": "Краткое решение/объяснение в 2–4 строки"
}}

Требования:
- Числа и условия задачи должны быть реалистичными
- Ответ должен быть однозначным
- Уровень сложности должен соответствовать ВПР
- Используй разные числа каждый раз (это важно!)
"""


async def generate_task(grade: int, task_num: int, topic: str, hint: str) -> dict:
    """
    Returns dict with keys: task_text, correct_answer, solution
    """
    user_prompt = TASK_USER_TEMPLATE.format(
        grade=grade, task_num=task_num, topic=topic, hint=hint
    )
    for attempt in range(3):
        try:
            raw = await _chat(TASK_SYSTEM, user_prompt)
            data = _extract_json(raw)
            if all(k in data for k in ("task_text", "correct_answer", "solution")):
                return data
        except Exception as e:
            logger.warning("generate_task attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError("Failed to generate task after 3 attempts")


# ---------------------------------------------------------------------------
# Theory generation
# ---------------------------------------------------------------------------

THEORY_SYSTEM = (
    "Ты — репетитор по математике для школьников. "
    "Объясняй материал ясно, структурированно, с примерами. "
    "Используй язык, понятный ученику соответствующего класса."
)

THEORY_USER_TEMPLATE = """
Объясни теорию для задания ВПР по математике.

Класс: {grade}
Номер задания в ВПР: {task_num}
Тема: {topic}
Подсказка: {hint}

Структура ответа (используй Markdown-подобное форматирование для Telegram HTML):
1. <b>📖 Ключевые понятия</b> — основные термины и определения
2. <b>📐 Формулы и правила</b> — все нужные формулы
3. <b>🪜 Алгоритм решения</b> — пошаговый план
4. <b>✏️ Разобранный пример</b> — типичное задание с полным решением
5. <b>⚠️ Типичные ошибки</b> — на что обратить внимание

Пиши на русском языке. Ответ должен быть информативным, но компактным (не более 600 слов).
"""


async def generate_theory(grade: int, task_num: int, topic: str, hint: str) -> str:
    user_prompt = THEORY_USER_TEMPLATE.format(
        grade=grade, task_num=task_num, topic=topic, hint=hint
    )
    return await _chat(THEORY_SYSTEM, user_prompt, temperature=0.5)


# ---------------------------------------------------------------------------
# Answer evaluation
# ---------------------------------------------------------------------------

EVAL_SYSTEM = (
    "Ты — строгий, но справедливый учитель математики. "
    "Оценивай ответ ученика объективно. "
    "Засчитывай эквивалентные формы ответа (например, 2.5 и 5/2, или 'треугольник ABC' и 'ABC'). "
    "Отвечай ТОЛЬКО валидным JSON без дополнительных пояснений."
)

EVAL_USER_TEMPLATE = """
Оцени ответ ученика на задание ВПР по математике.

Задание: {task_text}
Правильный ответ: {correct_answer}
Ответ ученика: {user_answer}
Максимальный балл за задание: {max_points}

Верни JSON строго в формате:
{{
  "points": <число от 0 до {max_points}>,
  "is_correct": <true или false>,
  "verdict": "<одна строка: 'Верно ✅', 'Частично верно ⚠️' или 'Неверно ❌'>",
  "explanation": "<2–4 предложения: почему ответ верен/неверен и правильное решение>"
}}
"""


async def evaluate_answer(
    task_text: str,
    correct_answer: str,
    user_answer: str,
    max_points: int,
) -> dict:
    """
    Returns dict: points, is_correct, verdict, explanation
    """
    user_prompt = EVAL_USER_TEMPLATE.format(
        task_text=task_text,
        correct_answer=correct_answer,
        user_answer=user_answer,
        max_points=max_points,
    )
    for attempt in range(3):
        try:
            raw = await _chat(EVAL_SYSTEM, user_prompt, temperature=0.2)
            data = _extract_json(raw)
            if "points" in data and "is_correct" in data:
                data["points"] = min(int(data["points"]), max_points)
                return data
        except Exception as e:
            logger.warning("evaluate_answer attempt %d failed: %s", attempt + 1, e)
    # Fallback: manual comparison
    norm_correct = correct_answer.strip().lower()
    norm_user = user_answer.strip().lower()
    is_correct = norm_correct == norm_user
    return {
        "points": max_points if is_correct else 0,
        "is_correct": is_correct,
        "verdict": "Верно ✅" if is_correct else "Неверно ❌",
        "explanation": f"Правильный ответ: {correct_answer}",
    }


# ---------------------------------------------------------------------------
# Batch evaluation (used in test mode)
# ---------------------------------------------------------------------------

async def evaluate_all_answers(tasks: list[dict]) -> list[dict]:
    """
    tasks: list of dicts with keys: task_text, correct_answer, user_answer, max_points
    Returns same list with added keys: points, is_correct, verdict, explanation
    """
    import asyncio

    async def eval_one(t: dict) -> dict:
        result = await evaluate_answer(
            t["task_text"], t["correct_answer"], t["user_answer"], t["max_points"]
        )
        return {**t, **result}

    return await asyncio.gather(*[eval_one(t) for t in tasks])
