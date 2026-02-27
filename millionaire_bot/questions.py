"""AI-powered question generation, phone-a-friend, and ask-the-audience."""

import json
import logging
import os
import random
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, GOOGLE_AI_API_KEY, AI_PROVIDER, get_difficulty
from database import get_recent_questions, save_question

log = logging.getLogger(__name__)

_GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
_GOOGLE_MODEL = os.getenv("GOOGLE_TEXT_MODEL", "gemini-2.0-flash")


def _get_client() -> AsyncOpenAI:
    if AI_PROVIDER.lower() == "google":
        return AsyncOpenAI(api_key=GOOGLE_AI_API_KEY, base_url=_GOOGLE_BASE_URL)
    return AsyncOpenAI(api_key=OPENAI_API_KEY)


def _get_model() -> str:
    return _GOOGLE_MODEL if AI_PROVIDER.lower() == "google" else OPENAI_MODEL

# ── Types ─────────────────────────────────────────────────────────────────────
type QuestionData = dict  # {question, options: {A,B,C,D}, correct}


# ── Authentic TV-show examples per difficulty tier ────────────────────────────
_EXAMPLES: dict[str, list[str]] = {
    "easy": [
        "Сколько минут в одном часе? (Правильный ответ: 60)",
        "Как называется детёныш собаки? (Правильный ответ: Щенок)",
        "Какой цвет светофора означает «стоп»? (Правильный ответ: Красный)",
        "Сколько дней в неделе? (Правильный ответ: Семь)",
        "Как называется самая большая планета Солнечной системы? (Правильный ответ: Юпитер)",
    ],
    "medium": [
        "В каком году Юрий Гагарин совершил первый полёт в космос? (Правильный ответ: 1961)",
        "Кто написал роман «Преступление и наказание»? (Правильный ответ: Достоевский)",
        "Как называется столица Австралии? (Правильный ответ: Канберра)",
        "Какой химический элемент обозначается символом Fe? (Правильный ответ: Железо)",
        "В каком году завершилась Вторая мировая война? (Правильный ответ: 1945)",
    ],
    "hard": [
        "В каком году Россия продала Аляску Соединённым Штатам? (Правильный ответ: 1867)",
        "Как называется наука о законах наследственности и изменчивости организмов? (Правильный ответ: Генетика)",
        "Кто является автором философского труда «Критика чистого разума»? (Правильный ответ: Кант)",
        "В каком веке был основан Московский университет? (Правильный ответ: XVIII)",
        "Какой орган человеческого тела вырабатывает желчь? (Правильный ответ: Печень)",
    ],
}


def _tier_key(level: int) -> str:
    if level <= 5:
        return "easy"
    elif level <= 10:
        return "medium"
    return "hard"


def _jaccard(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    union = wa | wb
    if not union:
        return 0.0
    return len(wa & wb) / len(union)


def _is_similar(new_q: str, existing: list[str], threshold: float = 0.55) -> bool:
    """Return True if new_q is too similar to any previously used question."""
    for q in existing:
        if _jaccard(new_q, q) >= threshold:
            return True
    return False


async def _generate_one(
    level: int,
    diff_name: str,
    diff_desc: str,
    examples: list[str],
    recent: list[str],
) -> QuestionData:
    examples_block = "\n".join(f"  • {e}" for e in examples)

    if recent:
        avoid_lines = "\n".join(f"  — {q}" for q in recent[:20])
        avoid_block = (
            f"УЖЕ ЗАДАВАЛИСЬ ВОПРОСЫ (не повторять и не перефразировать близко):\n"
            f"{avoid_lines}\n\n"
        )
    else:
        avoid_block = ""

    prompt = (
        "Ты составляешь вопросы для российской телевизионной игры «Кто хочет стать миллионером?».\n"
        f"Сгенерируй ОДИН новый вопрос для уровня {level} из 15.\n\n"
        f"УРОВЕНЬ СЛОЖНОСТИ: {diff_name}\n"
        f"{diff_desc}\n\n"
        f"СТИЛЬ ВОПРОСОВ ДЛЯ ЭТОГО УРОВНЯ (реальные примеры из телепередачи):\n"
        f"{examples_block}\n\n"
        "ПРАВИЛА:\n"
        "• Вопрос — одно чёткое предложение в стиле телепередачи.\n"
        "• Начинается с «Как называется…», «Кто…», «В каком году…», «Сколько…», «Что является…» и т.п.\n"
        "• Все 4 варианта ответа правдоподобны, ни один не выглядит явно лишним.\n"
        "• Ровно один правильный ответ.\n"
        "• Варианты ответа — короткие (1–5 слов): существительные, имена, числа, даты.\n"
        "• Правильный ответ равномерно распределён между A/B/C/D.\n"
        "• Вопрос и ответы — строго на русском языке.\n\n"
        f"{avoid_block}"
        "Верни строго JSON без пояснений:\n"
        '{"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct": "A"}'
    )

    resp = await _get_client().chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.9,
        max_tokens=300,
    )

    data: dict = json.loads(resp.choices[0].message.content)
    _validate(data)
    return data


# ── Question generation with dedup ────────────────────────────────────────────
async def generate_question(level: int, max_retries: int = 3) -> QuestionData:
    diff_name, diff_desc = get_difficulty(level)
    examples = _EXAMPLES[_tier_key(level)]
    recent = await get_recent_questions(level)

    last_data: QuestionData | None = None
    for attempt in range(max_retries):
        try:
            q_data = await _generate_one(level, diff_name, diff_desc, examples, recent)
        except Exception as e:
            log.warning("Generation attempt %d/%d failed: %s", attempt + 1, max_retries, e)
            continue

        last_data = q_data

        if _is_similar(q_data["question"], recent):
            log.info(
                "Attempt %d/%d: similar question detected, retrying…",
                attempt + 1,
                max_retries,
            )
            # Add it to local recent list so next attempt avoids it too
            recent = [q_data["question"]] + recent
            continue

        # Good question — save and return
        await save_question(level, q_data["question"], q_data["options"], q_data["correct"])
        log.info("Generated question for level %d (attempt %d)", level, attempt + 1)
        return q_data

    # Exhausted retries — use the last generated (or raise if all attempts failed)
    if last_data is None:
        raise RuntimeError(f"Failed to generate question for level {level} after {max_retries} attempts")

    log.warning("Saving possibly-similar question after %d retries", max_retries)
    await save_question(level, last_data["question"], last_data["options"], last_data["correct"])
    return last_data


def _validate(data: dict) -> None:
    required = {"question", "options", "correct"}
    assert required <= data.keys(), f"Missing keys: {required - data.keys()}"
    assert set(data["options"].keys()) == {"A", "B", "C", "D"}, "Bad options keys"
    assert data["correct"] in ("A", "B", "C", "D"), "Bad correct key"


# ── Lifeline: 50/50 ───────────────────────────────────────────────────────────
def fifty_fifty(options: dict[str, str], correct: str, already_removed: list[str]) -> list[str]:
    """Return 2 wrong options to remove. Respects already-removed options."""
    wrong = [k for k in options if k != correct and k not in already_removed]
    return random.sample(wrong, min(2, len(wrong)))


# ── Lifeline: Phone a Friend ──────────────────────────────────────────────────
async def phone_a_friend(
    question: str,
    options: dict[str, str],
    correct: str,
    removed: list[str],
) -> str:
    visible = {k: v for k, v in options.items() if k not in removed}
    opts_text = "\n".join(f"{k}) {v}" for k, v in visible.items())

    prompt = (
        "Тебе позвонил друг, который играет в «Кто хочет стать миллионером?».\n"
        f"Вопрос: {question}\n"
        f"Варианты ответа:\n{opts_text}\n\n"
        f"(Правильный ответ для тебя: {correct}) {options[correct]})\n\n"
        "Сыграй роль умного, но немного волнующегося друга. Дай совет:\n"
        "• Говори разговорным языком, 2–3 предложения.\n"
        "• Объясни свою логику коротко.\n"
        "• Склоняйся к правильному ответу, но с лёгкой неуверенностью — не называй букву прямо.\n"
        "• Не упоминай, что ты ИИ."
    )

    resp = await _get_client().chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        max_tokens=180,
    )

    return resp.choices[0].message.content.strip()


# ── Lifeline: Ask the Audience ────────────────────────────────────────────────
async def ask_audience(
    question: str,
    options: dict[str, str],
    correct: str,
    removed: list[str],
) -> dict[str, int]:
    """Return dict {letter: percentage} for visible options, summing to 100."""
    visible = {k: v for k, v in options.items() if k not in removed}
    opts_text = "\n".join(f"{k}) {v}" for k, v in visible.items())

    prompt = (
        "В игре «Кто хочет стать миллионером?» зрители голосуют за вариант ответа.\n"
        f"Вопрос: {question}\n"
        f"Варианты:\n{opts_text}\n\n"
        f"(Правильный ответ: {correct}) {options[correct]})\n\n"
        "Сгенерируй реалистичное распределение голосов зрителей в процентах.\n"
        "Зрители обычно склоняются к правильному ответу, но не всегда единогласно — "
        "чем сложнее вопрос, тем более равномерно распределены голоса.\n"
        f"Верни строго JSON только для видимых вариантов ({', '.join(visible.keys())}), "
        "сумма должна равняться ровно 100. Пример: "
        '{"A": 45, "B": 12, "C": 35, "D": 8}'
    )

    resp = await _get_client().chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.6,
        max_tokens=80,
    )

    raw: dict = json.loads(resp.choices[0].message.content)
    result = {k: int(v) for k, v in raw.items() if k in visible}

    # Normalise so total == 100
    total = sum(result.values())
    if total != 100 and total > 0:
        keys = list(result.keys())
        result = {k: round(result[k] * 100 / total) for k in keys}
        diff = 100 - sum(result.values())
        result[keys[0]] += diff

    return result


# ── Audience bar chart formatter ──────────────────────────────────────────────
def format_audience_bars(votes: dict[str, int], options: dict[str, str]) -> str:
    BAR = "█"
    EMPTY = "░"
    BAR_WIDTH = 12

    lines = ["👥 <b>ПОМОЩЬ ЗАЛА</b>"]
    for letter in ("A", "B", "C", "D"):
        if letter not in votes:
            continue
        pct = votes[letter]
        filled = round(pct / 100 * BAR_WIDTH)
        bar = BAR * filled + EMPTY * (BAR_WIDTH - filled)
        label = f"{letter}) {options[letter]}"
        lines.append(f"<code>{bar}</code> <b>{pct}%</b>  {label}")

    return "\n".join(lines)
