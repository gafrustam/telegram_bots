import html

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


def _band_emoji(band: float) -> str:
    return BAND_EMOJI.get(band, "⚪")


def _esc(text: str) -> str:
    return html.escape(text)


def _format_band_bar(band: float) -> str:
    filled = int(band)
    half = 1 if band - filled >= 0.5 else 0
    empty = 9 - filled - half
    return "▓" * filled + ("▒" if half else "") + "░" * empty


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
