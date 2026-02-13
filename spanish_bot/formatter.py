import html
from datetime import datetime

CRITERIA = [
    ("vocab_use", "Vocabulario"),
    ("grammar", "Gramatica"),
    ("fluency", "Fluidez"),
    ("comprehension", "Comprension"),
    ("pronunciation", "Pronunciacion"),
]

SCORE_EMOJI = {
    10: "💎", 9: "🟢", 8: "🟢", 7: "🟡", 6: "🟡",
    5: "🟠", 4: "🟠", 3: "🔴", 2: "🔴", 1: "🔴",
}


def _score_emoji(score: float) -> str:
    return SCORE_EMOJI.get(int(round(score)), "⚪")


def _esc(text: str) -> str:
    return html.escape(text)


def _val(v, default="—") -> str:
    return str(v) if v is not None else default


# ── Scenario display ────────────────────────────────────

def format_scenario(topic: str, scenario: str, vocabulary: list[dict]) -> str:
    lines = [
        f"🗣 <b>{_esc(topic)}</b>",
        "",
        f"<i>{_esc(scenario)}</i>",
        "",
        "━━━━━━━━━━━━━━━",
        "📚 <b>Vocabulario</b>",
        "━━━━━━━━━━━━━━━",
    ]

    for w in vocabulary:
        spanish = _esc(w.get("spanish", ""))
        english = _esc(w.get("english", ""))
        example = _esc(w.get("example", ""))
        lines.append(f"  • <b>{spanish}</b> — {english}")
        if example:
            lines.append(f"    <i>{example}</i>")

    return "\n".join(lines)


# ── Assessment display ──────────────────────────────────

def format_assessment(data: dict) -> str:
    if "error" in data:
        return f"⚠️ {_esc(data['error'])}"

    overall = data.get("overall_score", 0)
    lines = []

    lines.append("🎯 <b>Результаты разговора</b>")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"  {_score_emoji(overall)}  <b>Общий балл:  {overall}/10</b>")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("")

    # Summary scores
    for key, label in CRITERIA:
        criterion = data.get(key, {})
        score = criterion.get("score", "–")
        score_f = float(score) if score != "–" else 0
        lines.append(f"  {_score_emoji(score_f)}  {label}:  <b>{score}/10</b>")
    lines.append("")

    # Detailed explanations
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("📋 <b>Подробный разбор</b>")
    lines.append("━━━━━━━━━━━━━━━")

    for key, label in CRITERIA:
        criterion = data.get(key, {})
        score = criterion.get("score", "–")
        explanation = criterion.get("explanation", "")
        lines.append("")
        lines.append(f"📌 <b>{label}</b>  —  <b>{score}/10</b>")
        if explanation:
            lines.append(f"<i>{_esc(explanation)}</i>")
        examples = criterion.get("examples", [])
        if examples:
            for ex in examples:
                lines.append(f"  ▸ {_esc(ex)}")

    # General feedback
    feedback = data.get("feedback_text", "")
    if feedback:
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append(f"💬 {_esc(feedback)}")

    return "\n".join(lines)


# ── Level change ────────────────────────────────────────

def format_level_change(old_level: int, new_level: int, label: str, cefr: str) -> str:
    if new_level > old_level:
        emoji = "📈"
        action = "повышен"
    else:
        emoji = "📉"
        action = "понижен"

    return (
        f"{emoji} Уровень {action}!\n\n"
        f"<b>Nivel {new_level} — {_esc(label)} ({cefr})</b>"
    )


# ── User stats ──────────────────────────────────────────

def format_user_stats(stats: dict, recent: list[dict]) -> str:
    lines = [
        "📊 <b>Моя статистика</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📈 <b>Общие показатели</b>",
        "━━━━━━━━━━━━━━━",
        f"  Всего диалогов: <b>{stats['total_conversations']}</b>",
        f"  Завершено: <b>{stats['completed']}</b>",
        f"  Средний балл: <b>{_val(stats['avg_score'])}</b>",
        f"  Лучший балл: <b>{_val(stats['best_score'])}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📅 <b>За последние 7 дней</b>",
        "━━━━━━━━━━━━━━━",
        f"  Диалогов: <b>{stats['sessions_7d']}</b>",
        f"  Средний балл: <b>{_val(stats['avg_7d'])}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "🔬 <b>Средний балл по критериям</b>",
        "━━━━━━━━━━━━━━━",
    ]

    criteria_map = [
        ("avg_vocab", "Vocabulario"),
        ("avg_grammar", "Gramatica"),
        ("avg_fluency", "Fluidez"),
        ("avg_comprehension", "Comprension"),
        ("avg_pronunciation", "Pronunciacion"),
    ]
    for key, label in criteria_map:
        val = stats.get(key)
        emoji = _score_emoji(float(val)) if val is not None else "⚪"
        lines.append(f"  {emoji}  {label}: <b>{_val(val)}</b>")

    if recent:
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append("🕐 <b>Последние результаты</b>")
        lines.append("━━━━━━━━━━━━━━━")
        for r in recent:
            dt: datetime = r["created_at"]
            date_str = dt.strftime("%d.%m")
            topic = _esc(r["scenario_topic"])
            score = r["overall_score"]
            lvl = r["difficulty_level"]
            lines.append(f"  Lvl {lvl} «{topic}» — <b>{score}</b>  ({date_str})")

    return "\n".join(lines)


def format_error(error_text: str) -> str:
    return (
        "❌ <b>Произошла ошибка</b>\n\n"
        f"{_esc(error_text)}\n\n"
        "Попробуйте начать новый диалог."
    )
