import html
from datetime import datetime


def _esc(text: str) -> str:
    return html.escape(text)


def _val(v, default="—") -> str:
    return str(v) if v is not None else default


# ── Scenario display ────────────────────────────────────

def format_scenario(
    topic: str, scenario: str,
    vocabulary: list[dict], constructions: list[dict] = None,
) -> str:
    if constructions is None:
        constructions = []

    lines = [
        f"🗣 <b>{_esc(topic)}</b>",
        "",
        f"<i>{_esc(scenario)}</i>",
        "",
        "━━━━━━━━━━━━━━━",
        "📚 <b>Слова</b>",
        "━━━━━━━━━━━━━━━",
    ]

    for w in vocabulary:
        english = _esc(w.get("english", ""))
        russian = _esc(w.get("russian", ""))
        example = _esc(w.get("example", ""))
        lines.append(f"  • <b>{english}</b> — {russian}")
        if example:
            lines.append(f"    <i>{example}</i>")

    if constructions:
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append("🧩 <b>Конструкции</b>")
        lines.append("━━━━━━━━━━━━━━━")
        for c in constructions:
            english = _esc(c.get("english", ""))
            russian = _esc(c.get("russian", ""))
            example = _esc(c.get("example", ""))
            lines.append(f"  • <b>{english}</b>")
            if russian:
                lines.append(f"    {russian}")
            if example:
                lines.append(f"    <i>{example}</i>")

    return "\n".join(lines)


# ── Assessment display ──────────────────────────────────

def format_assessment(data: dict) -> str:
    if "error" in data:
        return f"⚠️ {_esc(data['error'])}"

    lines = []

    # Praise
    praise = data.get("praise", "")
    if praise:
        lines.append(f"👏 {_esc(praise)}")
        lines.append("")

    # Mistakes
    mistakes = data.get("mistakes", [])
    if mistakes:
        lines.append("✏️ <b>Обрати внимание:</b>")
        for m in mistakes:
            said = _esc(m.get("said", ""))
            correction = _esc(m.get("correction", ""))
            note = _esc(m.get("note", ""))
            lines.append(f"  • <s>{said}</s> → <b>{correction}</b>")
            if note:
                lines.append(f"    <i>{note}</i>")
        lines.append("")

    # Suggestions
    suggestions = data.get("suggestions", [])
    if suggestions:
        lines.append("💡 <b>Слова на заметку:</b>")
        for s in suggestions:
            if isinstance(s, dict):
                word = _esc(s.get("word", ""))
                translation = _esc(s.get("translation", ""))
                lines.append(f"  • <b>{word}</b> — {translation}")
            else:
                lines.append(f"  • {_esc(str(s))}")
        lines.append("")

    # Feedback
    feedback = data.get("feedback_text", "")
    if feedback:
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
        f"<b>Level {new_level} — {_esc(label)} ({cefr})</b>"
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
    ]

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
