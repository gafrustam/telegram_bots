import html
from datetime import date, datetime

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
    rounded = round(band * 2) / 2
    return BAND_EMOJI.get(rounded, "⚪")


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


# ── Admin formatting ────────────────────────────────────

def format_admin_summary(stats: dict, retention: dict) -> str:
    if not stats:
        return "🔧 <b>Админ-панель</b>\n\n<i>Нет данных</i>"

    def v(key, default="0"):
        val = stats.get(key)
        return str(val) if val is not None else default

    lines = [
        "🔧 <b>Админ-панель</b>",
        "",
        f"Всего пользователей: <b>{v('total_users')}</b>",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "<code>           1д   2д   3д   7д  14д  30д</code>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"<code>Новые:    {v('new_1d'):>4}{v('new_2d'):>5}{v('new_3d'):>5}{v('new_7d'):>5}{v('new_14d'):>5}{v('new_30d'):>5}</code>",
        f"<code>Активные: {v('active_1d'):>4}{v('active_2d'):>5}{v('active_3d'):>5}{v('active_7d'):>5}{v('active_14d'):>5}{v('active_30d'):>5}</code>",
        f"<code>Заверш:   {v('completed_users_1d'):>4}{v('completed_users_2d'):>5}{v('completed_users_3d'):>5}{v('completed_users_7d'):>5}{v('completed_users_14d'):>5}{v('completed_users_30d'):>5}</code>",
        f"<code>Сессий:   {v('sessions_1d'):>4}{v('sessions_2d'):>5}{v('sessions_3d'):>5}{v('sessions_7d'):>5}{v('sessions_14d'):>5}{v('sessions_30d'):>5}</code>",
        f"<code>Минуты:   {v('minutes_1d'):>4}{v('minutes_2d'):>5}{v('minutes_3d'):>5}{v('minutes_7d'):>5}{v('minutes_14d'):>5}{v('minutes_30d'):>5}</code>",
    ]

    cohort = retention.get("cohort_size", 0)
    if cohort:
        def pct(key):
            val = retention.get(key, 0)
            return f"{round(100 * val / cohort)}%"

        lines += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 <b>Ретеншн</b> (когорта: {cohort})",
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            f"  D1: <b>{pct('ret_d1')}</b>"
            f"  D3: <b>{pct('ret_d3')}</b>"
            f"  D7: <b>{pct('ret_d7')}</b>"
            f"  D14: <b>{pct('ret_d14')}</b>"
            f"  D30: <b>{pct('ret_d30')}</b>",
        ]

    return "\n".join(lines)
