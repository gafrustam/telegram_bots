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
        f"  Part 1: <b>{stats['part1_count']}</b> сессий — ∅ <b>{_val(stats.get('avg_part1'))}</b>",
        f"  Part 2: <b>{stats['part2_count']}</b> сессий — ∅ <b>{_val(stats.get('avg_part2'))}</b>",
        f"  Part 3: <b>{stats['part3_count']}</b> сессий — ∅ <b>{_val(stats.get('avg_part3'))}</b>",
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

def _trend(current, previous) -> str:
    if not current or not previous or previous == 0:
        return ""
    diff = current - previous
    pct = round(100 * diff / previous)
    if diff > 0:
        return f" <i>(+{pct}%)</i>"
    if diff < 0:
        return f" <i>({pct}%)</i>"
    return ""


def format_admin_overview(data: dict | None) -> str:
    if not data:
        return "⚠️ Нет данных"

    completed = data["completed_sessions"]
    total_s = data["total_sessions"]
    compl_pct = round(100 * completed / total_s) if total_s else 0
    avg_sess_per_user = round(completed / data["active_7d"], 1) if data["active_7d"] else 0

    return "\n".join([
        "🔧 <b>Админ-панель — Обзор</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "👥 <b>Пользователи</b>",
        "━━━━━━━━━━━━━━━",
        f"  Всего: <b>{data['total_users']}</b>"
        f"{_trend(data['users_this_week'], data['users_last_week'])}",
        "",
        "  <b>Новые:</b>",
        f"    24ч: <b>{data['new_users_24h']}</b>"
        f"  •  7д: <b>{data['new_users_7d']}</b>"
        f"  •  30д: <b>{data['new_users_30d']}</b>",
        "",
        "  <b>Активные:</b>",
        f"    24ч: <b>{data['active_24h']}</b>"
        f"  •  7д: <b>{data['active_7d']}</b>"
        f"  •  30д: <b>{data['active_30d']}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📝 <b>Сессии</b>",
        "━━━━━━━━━━━━━━━",
        f"  Всего: <b>{total_s}</b>"
        f"  (за 7д: <b>{data['sessions_this_week']}</b>"
        f"{_trend(data['sessions_this_week'], data['sessions_last_week'])})",
        f"  Завершено: <b>{completed}</b> ({compl_pct}%)"
        f"  • Провалено: <b>{data['failed_sessions']}</b>",
        f"  Ср. сессий / активный юзер (7д): <b>{avg_sess_per_user}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "🎯 <b>Баллы и аудио</b>",
        "━━━━━━━━━━━━━━━",
        f"  Средний балл: <b>{_val(data['global_avg_band'])}</b>"
        f"  • Лучший: <b>{_val(data['best_band'])}</b>",
        f"  Аудио всего: <b>{_val(data['total_audio_min'])}</b> мин"
        f"  • Ср. ответ: <b>{_val(data['avg_audio_sec'])}</b> сек",
    ])


def format_admin_scores(summary: dict | None, parts: list[dict]) -> str:
    if not summary or not summary.get("total"):
        return "🔧 <b>Админ-панель — Баллы</b>\n\n<i>Нет данных</i>"

    lines = [
        "🔧 <b>Админ-панель — Баллы</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "📊 <b>Глобальные показатели</b>",
        "━━━━━━━━━━━━━━━",
        f"  Overall: <b>{_val(summary['avg_overall'])}</b>"
        f"  (лучший: {_val(summary['best_overall'])}"
        f"  • худший: {_val(summary['worst_overall'])})",
        "",
        f"  Fluency & Coherence: <b>{_val(summary['avg_fc'])}</b>",
        f"  Lexical Resource: <b>{_val(summary['avg_lr'])}</b>",
        f"  Grammar Range & Accuracy: <b>{_val(summary['avg_gra'])}</b>",
        f"  Pronunciation: <b>{_val(summary['avg_pron'])}</b>",
    ]

    if parts:
        lines += [
            "",
            "━━━━━━━━━━━━━━━",
            "📋 <b>По разделам</b>",
            "━━━━━━━━━━━━━━━",
        ]
        for r in parts:
            part = PART_NAMES.get(r["part"], f"Part {r['part']}")
            total = r.get("cnt", 0)
            completed = r.get("completed", 0)
            audio = _val(r.get("audio_min"))
            lines.append(
                f"  {part}: <b>{completed}</b>/{total} сессий"
                f"  • ∅ <b>{_val(r['avg_band'])}</b>"
                f"  • {audio} мин"
            )

    return "\n".join(lines)


def format_admin_users(rows: list[dict]) -> str:
    lines = [
        "🔧 <b>Админ-панель — Пользователи</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "👥 <b>Топ по активности</b>",
        "━━━━━━━━━━━━━━━",
    ]
    for i, r in enumerate(rows, 1):
        name = _esc(r["first_name"] or "?")
        uname = f" @{_esc(r['username'])}" if r.get("username") else ""
        last = ""
        if r.get("last_session"):
            last = r["last_session"].strftime(" (%d.%m)")
        lines.append(
            f"  {i}. <b>{name}</b>{uname}\n"
            f"      {r['session_count']} сесс."
            f"  ∅ {_val(r['avg_band'])}"
            f"  best {_val(r['best_band'])}"
            f"  {_val(r.get('audio_min'))} мин{last}"
        )
    if not rows:
        lines.append("  <i>Нет данных</i>")
    return "\n".join(lines)


def format_admin_outliers(data: dict) -> str:
    lines = [
        "🔧 <b>Админ-панель — Выбросы</b>",
    ]

    power = data.get("power_users", [])
    if power:
        lines += [
            "",
            "━━━━━━━━━━━━━━━",
            "💪 <b>Power Users (5+ сессий или 10+ мин)</b>",
            "━━━━━━━━━━━━━━━",
        ]
        for r in power:
            name = _esc(r["first_name"] or "?")
            uname = f" @{_esc(r['username'])}" if r.get("username") else ""
            lines.append(
                f"  {name}{uname}: "
                f"{r['sessions']} сесс., "
                f"{_val(r.get('audio_min'))} мин, "
                f"∅ {_val(r['avg_band'])}"
            )

    top = data.get("top_scorers", [])
    if top:
        lines += [
            "",
            "━━━━━━━━━━━━━━━",
            "🏆 <b>Лучшие результаты</b>",
            "━━━━━━━━━━━━━━━",
        ]
        for r in top:
            name = _esc(r["first_name"] or "?")
            uname = f" @{_esc(r['username'])}" if r.get("username") else ""
            part = PART_NAMES.get(r["part"], f"Part {r['part']}")
            dt = r["created_at"].strftime("%d.%m")
            lines.append(
                f"  {name}{uname}: "
                f"<b>{r['overall_band']}</b> — {part} «{_esc(r['topic'])}» ({dt})"
            )

    drops = data.get("dropoffs", [])
    if drops:
        lines += [
            "",
            "━━━━━━━━━━━━━━━",
            "📉 <b>Высокий % недозавершений</b>",
            "━━━━━━━━━━━━━━━",
        ]
        for r in drops:
            name = _esc(r["first_name"] or "?")
            uname = f" @{_esc(r['username'])}" if r.get("username") else ""
            lines.append(
                f"  {name}{uname}: "
                f"{r['failed']}/{r['total']} провалено ({r['fail_pct']}%)"
            )

    if not power and not top and not drops:
        lines.append("\n<i>Пока недостаточно данных для выбросов</i>")

    return "\n".join(lines)
