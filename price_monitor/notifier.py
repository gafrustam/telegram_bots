import logging
from typing import Optional

import aiohttp

from config import Config

logger = logging.getLogger(__name__)


def _fmt_price(price: float) -> str:
    """Format a price nicely depending on magnitude."""
    if price >= 1:
        return f"${price:,.4f}"
    elif price >= 0.01:
        return f"${price:.6f}"
    elif price >= 0.0001:
        return f"${price:.8f}"
    else:
        return f"${price:.10f}"


def _fmt_change(change_pct: Optional[float]) -> str:
    if change_pct is None:
        return "н/д"
    arrow = "📈" if change_pct >= 0 else "📉"
    sign = "+" if change_pct >= 0 else ""
    return f"{arrow} {sign}{change_pct:.2f}%"


async def send_message(text: str) -> bool:
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                resp.raise_for_status()
                return True
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False


async def send_price_alert(token: dict, current_price: float, target_price: float, new_target: float) -> None:
    name = token["name"]
    symbol = token["symbol"]
    cmc_url = token.get("cmc_url", "")

    text = (
        f"🎯 <b>{name} ({symbol}) — Целевая цена достигнута!</b>\n\n"
        f"💰 Текущая цена: <b>{_fmt_price(current_price)}</b>\n"
        f"🎯 Была цель: <b>{_fmt_price(target_price)}</b>\n"
        f"🔄 Новая цель (−20%): <b>{_fmt_price(new_target)}</b>\n\n"
        f'<a href="{cmc_url}">Открыть на бирже →</a>'
    )
    await send_message(text)
    logger.info("Price alert sent for %s: $%.8f <= $%.8f", name, current_price, target_price)


async def send_biweekly_report(
    token: dict,
    current_price: float,
    prev_price: Optional[float],
    change_pct: Optional[float],
    target_price: Optional[float],
    scenario_list: list[dict],
) -> None:
    name = token["name"]
    symbol = token["symbol"]
    cmc_url = token.get("cmc_url", "")

    change_str = _fmt_change(change_pct)
    prev_str = _fmt_price(prev_price) if prev_price else "первый отчёт"
    target_str = _fmt_price(target_price) if target_price else "не задана"

    lines = [
        f"📊 <b>{name} ({symbol}) — Двухнедельный отчёт</b>\n",
        f"💰 Текущая цена: <b>{_fmt_price(current_price)}</b>",
        f"📅 2 недели назад: {prev_str}",
        f"Изменение: {change_str}",
        f"🎯 Целевой алерт: {target_str}",
        "",
    ]

    if scenario_list:
        lines.append("🔮 <b>Прогноз на 3 года</b>")
        lines.append("")
        # Fixed-width formatting
        for s in scenario_list:
            prob = s["probability"]
            price = s["price"]
            label = s["label"]
            emoji = s["emoji"]
            rationale = s.get("rationale", "")
            lines.append(
                f"{emoji} <b>{label}</b> ({prob}%) → <b>{_fmt_price(price)}</b>"
            )
            if rationale:
                lines.append(f"   <i>{rationale}</i>")
        lines.append("")

    lines.append(f'<a href="{cmc_url}">Открыть →</a>')

    await send_message("\n".join(lines))
    logger.info("Biweekly report sent for %s", name)


async def send_startup_message(tokens: list[dict]) -> None:
    names = ", ".join(f"{t['name']} ({t['symbol']})" for t in tokens)
    text = (
        f"✅ <b>Crypto Monitor запущен</b>\n\n"
        f"Отслеживаю: {names}\n"
        f"• Проверка цены: каждые 2 часа\n"
        f"• Двухнедельный отчёт: раз в 14 дней"
    )
    await send_message(text)
