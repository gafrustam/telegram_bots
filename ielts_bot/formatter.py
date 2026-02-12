import html
from datetime import datetime

CRITERIA = [
    ("fluency_coherence", "Fluency & Coherence"),
    ("lexical_resource", "Lexical Resource"),
    ("grammatical_range_accuracy", "Grammatical Range & Accuracy"),
    ("pronunciation", "Pronunciation"),
]

BAND_EMOJI = {
    9.0: "💎",                                      # C2
    8.5: "🟢", 8.0: "🟢", 7.5: "🟢", 7.0: "🟢",  # C1
    6.5: "🟡", 6.0: "🟡", 5.5: "🟡",              # B2
    5.0: "🟠", 4.5: "🟠", 4.0: "🟠",              # B1
    3.5: "🔴", 3.0: "🔴", 2.5: "🔴", 2.0: "🔴",  # < B1
    1.5: "🔴", 1.0: "🔴", 0.5: "🔴", 0.0: "🔴",
}

PART_NAMES = {1: "Part 1", 2: "Part 2", 3: "Part 3"}


def _band_emoji(band: float) -> str:
    return BAND_EMOJI.get(band, "⚪")


def _esc(text: str) -> str:
    return html.escape(text)


def _format_band_bar(band: float) -> str:
    filled = int(band)
    half = 1 if band - filled >= 0.5 else 0
    empty = 9 - filled - half
    return "▓" * filled + ("▒" if half else "") + "░" * empty


def _val(v, default="—") -> str:
    return str(v) if v is not None else default


def format_assessment(data: dict) -> str:
    if "error" in data:
        return f"⚠️ {_esc(data['error'])}"

    overall = data.get("overall_band", 0)
    lines = []

    # Header
    lines.append("🎯 <b>IELTS Speaking Assessment</b>")
    lines.append("")
    lines.append(f"━━━━━━━━━━━━━━━")
    lines.append(f"  {_band_emoji(overall)}  <b>Overall Band Score:  {overall}</b>")
    lines.append(f"━━━━━━━━━━━━━━━")
    lines.append("")

    # Criteria scores summary
    for key, label in CRITERIA:
        criterion = data.get(key, {})
        band = criterion.get("band", "–")
        band_f = float(band) if band != "–" else 0
        lines.append(f"  {_band_emoji(band_f)}  {label}:  <b>{band}</b>")
    lines.append("")

    # Detailed explanations
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("📋 <b>Подробный разбор</b>")
    lines.append("━━━━━━━━━━━━━━━")

    for key, label in CRITERIA:
        criterion = data.get(key, {})
        band = criterion.get("band", "–")
        explanation = criterion.get("explanation", "")
        lines.append("")
        lines.append(f"📌 <b>{label}</b>  —  <b>Band {band}</b>")
        if explanation:
            lines.append(f"<i>{_esc(explanation)}</i>")
        examples = criterion.get("examples", [])
        if examples:
            lines.append("")
            for ex in examples:
                lines.append(f"  ▸ {_esc(ex)}")

    lines.append("")
    lines.append("─────────────────────")
    lines.append("<i>Оценка по официальным IELTS Band Descriptors</i>")

    return "\n".join(lines)


def format_error(error_text: str) -> str:
    return (
        "❌ <b>Произошла ошибка</b>\n\n"
        f"{_esc(error_text)}\n\n"
        "Попробуйте отправить голосовое сообщение ещё раз."
    )


# ── User statistics ─────────────────────────────────────

def format_user_stats(stats: dict, recent: list[dict]) -> str:
    lines = [
        "📊 <b>Моя статистика</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📈 <b>Общие показатели</b>",
        "━━━━━━━━━━━━━━━",
        f"  Всего сессий: <b>{stats['total_sessions']}</b>",
        f"  Завершено: <b>{stats['completed']}</b>",
        f"  Средний балл: <b>{_val(stats['avg_overall'])}</b>",
        f"  Лучший балл: <b>{_val(stats['best_overall'])}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📅 <b>За последние 7 дней</b>",
        "━━━━━━━━━━━━━━━",
        f"  Сессий: <b>{stats['sessions_7d']}</b>",
        f"  Средний балл: <b>{_val(stats['avg_7d'])}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📋 <b>По разделам</b>",
        "━━━━━━━━━━━━━━━",
        f"  Part 1: <b>{stats['part1_count']}</b> сессий",
        f"  Part 2: <b>{stats['part2_count']}</b> сессий",
        f"  Part 3: <b>{stats['part3_count']}</b> сессий",
        "",
        "━━━━━━━━━━━━━━━",
        "🔬 <b>Средний балл по критериям</b>",
        "━━━━━━━━━━━━━━━",
    ]

    criteria_map = [
        ("avg_fc", "Fluency & Coherence"),
        ("avg_lr", "Lexical Resource"),
        ("avg_gra", "Grammar Range & Accuracy"),
        ("avg_pron", "Pronunciation"),
    ]
    for key, label in criteria_map:
        val = stats.get(key)
        emoji = _band_emoji(float(val)) if val is not None else "⚪"
        lines.append(f"  {emoji}  {label}: <b>{_val(val)}</b>")

    if recent:
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append("🕐 <b>Последние результаты</b>")
        lines.append("━━━━━━━━━━━━━━━")
        for r in recent:
            dt: datetime = r["created_at"]
            date_str = dt.strftime("%d.%m")
            part = PART_NAMES.get(r["part"], f"Part {r['part']}")
            topic = _esc(r["topic"])
            band = r["overall_band"]
            lines.append(f"  {part} «{topic}» — <b>{band}</b>  ({date_str})")

    return "\n".join(lines)


# ── Admin formatting ────────────────────────────────────

def format_admin_overview(data: dict | None) -> str:
    if not data:
        return "⚠️ Нет данных"
    return "\n".join([
        "🔧 <b>Панель администратора</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📊 <b>Общая статистика</b>",
        "━━━━━━━━━━━━━━━",
        f"  Пользователей: <b>{data['total_users']}</b>",
        f"  Активных (7 дней): <b>{data['active_7d']}</b>",
        f"  Активных (24 часа): <b>{data['active_24h']}</b>",
        "",
        f"  Всего сессий: <b>{data['total_sessions']}</b>",
        f"  Завершённых: <b>{data['completed_sessions']}</b>",
        f"  Оценок: <b>{data['total_assessments']}</b>",
        f"  Средний балл: <b>{_val(data['global_avg_band'])}</b>",
    ])


def format_admin_daily(rows: list[dict]) -> str:
    lines = [
        "🔧 <b>Панель администратора</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📅 <b>Статистика по дням (7 дней)</b>",
        "━━━━━━━━━━━━━━━",
    ]
    for r in rows:
        day = r["day"].strftime("%d.%m") if r["day"] else "?"
        users = r["unique_users"]
        sessions = r["sessions"]
        band = _val(r["avg_band"])
        lines.append(f"  {day} — 👤 {users}  📝 {sessions}  🎯 {band}")
    return "\n".join(lines)


def format_admin_top_users(rows: list[dict]) -> str:
    lines = [
        "🔧 <b>Панель администратора</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "👥 <b>Топ пользователей</b>",
        "━━━━━━━━━━━━━━━",
    ]
    for i, r in enumerate(rows, 1):
        name = _esc(r["first_name"] or "?")
        uname = f" (@{_esc(r['username'])})" if r.get("username") else ""
        lines.append(
            f"  {i}. {name}{uname} — "
            f"{r['session_count']} сесс., "
            f"∅ {_val(r['avg_band'])}, "
            f"лучший {_val(r['best_band'])}"
        )
    if not rows:
        lines.append("  <i>Нет данных</i>")
    return "\n".join(lines)


def format_admin_parts(rows: list[dict]) -> str:
    lines = [
        "🔧 <b>Панель администратора</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📋 <b>Распределение по разделам</b>",
        "━━━━━━━━━━━━━━━",
    ]
    for r in rows:
        part = PART_NAMES.get(r["part"], f"Part {r['part']}")
        lines.append(f"  {part}: <b>{r['cnt']}</b> сессий, ∅ балл <b>{_val(r['avg_band'])}</b>")
    if not rows:
        lines.append("  <i>Нет данных</i>")
    return "\n".join(lines)
