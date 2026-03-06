import html
from datetime import datetime, timezone

CRITERIA = [
    ("fluency_coherence",          "Fluency & Coherence"),
    ("lexical_resource",           "Lexical Resource"),
    ("grammatical_range_accuracy", "Grammatical Range & Accuracy"),
    ("pronunciation",              "Pronunciation"),
]

BAND_EMOJI = {
    9.0: "💎",
    8.5: "🟢", 8.0: "🟢", 7.5: "🟢", 7.0: "🟢",
    6.5: "🟡", 6.0: "🟡", 5.5: "🟡",
    5.0: "🟠", 4.5: "🟠", 4.0: "🟠",
    3.5: "🔴", 3.0: "🔴", 2.5: "🔴", 2.0: "🔴",
    1.5: "🔴", 1.0: "🔴", 0.5: "🔴", 0.0: "🔴",
}


def _band_emoji(band: float) -> str:
    rounded = round(band * 2) / 2
    return BAND_EMOJI.get(rounded, "⚪")


def _esc(text: str) -> str:
    return html.escape(str(text))


def format_assessment(data: dict) -> str:
    if "error" in data:
        return f"⚠️ {_esc(data['error'])}"

    overall = data.get("overall_band", 0)
    lines = []

    lines.append("🎯 <b>IELTS Speaking Assessment</b>")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"  {_band_emoji(overall)}  <b>Overall Band Score:  {overall}</b>")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("")

    for key, label in CRITERIA:
        criterion = data.get(key, {})
        band = criterion.get("band", "–")
        band_f = float(band) if band != "–" else 0
        lines.append(f"  {_band_emoji(band_f)}  {label}:  <b>{band}</b>")

    lines.append("")
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


def format_user_stats(stats: dict, first_name: str) -> str:
    completed = stats.get("completed_sessions", 0)
    total = stats.get("total_sessions", 0)
    avg_band = stats.get("avg_band")
    best_band = stats.get("best_band")
    p1 = stats.get("part1_count", 0)
    p2 = stats.get("part2_count", 0)
    p3 = stats.get("part3_count", 0)
    avg_p1 = stats.get("avg_band_p1")
    avg_p2 = stats.get("avg_band_p2")
    avg_p3 = stats.get("avg_band_p3")
    last_session = stats.get("last_session")

    lines = [
        f"📊 <b>Статистика — {_esc(first_name)}</b>",
        "",
        "🗣 <b>Speaking</b>",
        f"  Завершено сессий: <b>{completed}</b>",
    ]

    if avg_band is not None:
        emoji = _band_emoji(float(avg_band))
        lines.append(f"  Средний балл: {emoji} <b>{avg_band}</b>")
    if best_band is not None:
        emoji = _band_emoji(float(best_band))
        lines.append(f"  Лучший балл: {emoji} <b>{best_band}</b>")

    if p1 or p2 or p3:
        lines.append("")
        lines.append("  По частям:")
        if p1:
            s = f" (ср. {avg_p1})" if avg_p1 else ""
            lines.append(f"    Part 1: {p1} сессий{s}")
        if p2:
            s = f" (ср. {avg_p2})" if avg_p2 else ""
            lines.append(f"    Part 2: {p2} сессий{s}")
        if p3:
            s = f" (ср. {avg_p3})" if avg_p3 else ""
            lines.append(f"    Part 3: {p3} сессий{s}")

    if last_session:
        now = datetime.now(timezone.utc)
        if hasattr(last_session, "tzinfo") and last_session.tzinfo:
            delta = now - last_session
        else:
            delta = now - last_session.replace(tzinfo=timezone.utc)
        hours = int(delta.total_seconds() // 3600)
        if hours < 1:
            ago = "менее часа назад"
        elif hours < 24:
            ago = f"{hours} ч. назад"
        else:
            days = hours // 24
            ago = f"{days} дн. назад"
        lines.append("")
        lines.append(f"  Последняя тренировка: <i>{ago}</i>")

    if completed == 0:
        lines.append("")
        lines.append("Начни тренировку — нажми <b>Speaking</b> в меню!")

    return "\n".join(lines)


def format_admin_stats(stats: dict) -> str:
    def v(key, default="0"):
        val = stats.get(key)
        return str(val) if val is not None else default

    lines = [
        "🔧 <b>Админ-панель</b>",
        "",
        f"Пользователей всего: <b>{v('total_users')}</b>",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "<code>             1д    7д   30д</code>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"<code>Новые:      {v('new_1d'):>4}{v('new_7d'):>6}{v('new_30d'):>6}</code>",
        f"<code>Активные:   {v('active_1d'):>4}{v('active_7d'):>6}{v('active_30d'):>6}</code>",
        f"<code>Сессии:     {v('sessions_1d'):>4}{v('sessions_7d'):>6}{v('sessions_30d'):>6}</code>",
    ]

    avg = stats.get("avg_band_30d")
    total_a = stats.get("total_assessments_30d", 0)
    if avg:
        lines += [
            "",
            f"Speaking (30д): оценок <b>{total_a}</b>, средний балл <b>{avg}</b>",
        ]

    taps = stats.get("section_taps_7d", {})
    if taps:
        lines.append("")
        lines.append("Нажатия на разделы (7д):")
        for section, cnt in sorted(taps.items(), key=lambda x: -x[1]):
            lines.append(f"  {section}: <b>{cnt}</b>")

    return "\n".join(lines)
