import asyncio
import glob
import logging
import os
import random
import re
import tempfile
import time
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv, dotenv_values

load_dotenv()

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USER = "gafrustam"
ADMIN_CHAT_ID = 138468116
CLAUDE_PATH = "/home/ubuntu/.local/bin/claude"
REPO_ROOT = "/home/ubuntu/telegram_bots"
MAX_MSG_LEN = 4096
CONTINUE_WORDS = {"закончи", "продолжи", "дальше"}

CREATION_QUOTES = [
    "🔥 «Лучший способ предсказать будущее — создать его.» — Алан Кэй",
    "⚡️ «Всё, что можно представить — можно запрограммировать.» — Никлаус Вирт",
    "🚀 «Сначала реши проблему. Потом напиши код.» — Джон Джонсон",
    "💎 «Простота — необходимое условие надёжности.» — Эдсгер Дейкстра",
    "🌊 «Код — это поэзия, которая ещё и работает.» — dev-фольклор",
    "🔨 «Строить — значит верить в завтрашний день.» — Ле Корбюзье",
    "🎯 «Совершенство достигается не тогда, когда нечего добавить, а когда нечего убрать.» — Сент-Экзюпери",
    "🌱 «Каждая строка кода — это инвестиция в будущее.» — Мартин Фаулер",
    "⭐️ «Делай то, что не масштабируется.» — Пол Грэм",
    "🏗 «Великие вещи складываются из маленьких деталей.» — Рэй Крок",
    "🧠 «Воображение важнее знания.» — Альберт Эйнштейн",
    "🔑 «Единственный способ делать великую работу — любить то, что делаешь.» — Стив Джобс",
    "🌟 «Начни. Остальное приложится.» — Лао-цзы",
    "💡 «Ошибка — это не провал, а черновик успеха.» — dev-фольклор",
    "🛠 «Инструменты усиливают талант, но не заменяют их.» — Фред Брукс",
]

bot = Bot(token=TELEGRAM_TOKEN)
router = Router()
router.message.filter(F.from_user.username == ALLOWED_USER)
router.callback_query.filter(F.from_user.username == ALLOWED_USER)
dp = Dispatcher()
dp.include_router(router)

_busy = False
_proc: asyncio.subprocess.Process | None = None
_stop_requested = False

STOP_KB = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⏹ Остановить", callback_data="stop_task")]]
)


# ── Git helpers ─────────────────────────────────────────────────────────────

def _get_head() -> str:
    import subprocess
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def _get_changed_dirs(old_head: str) -> set[str]:
    import subprocess
    r = subprocess.run(
        ["git", "diff", "--name-only", f"{old_head}..HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    changed_files = set(r.stdout.strip().splitlines())
    dirs = set()
    for f in changed_files:
        if not f:
            continue
        parts = Path(f).parts
        if parts:
            dirs.add(parts[0])
    return dirs


async def _commit_and_push(chat_id: int):
    import subprocess
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if status.stdout.strip():
        subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT)
        subprocess.run(
            ["git", "commit", "-m", "coder-bot: auto commit"],
            cwd=REPO_ROOT,
            capture_output=True,
        )
    r = subprocess.run(
        ["git", "push"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        await bot.send_message(chat_id, "📤 Изменения запушены")
    else:
        err = r.stderr.strip()[:300]
        await bot.send_message(chat_id, f"⚠️ Push не удался:\n{err}")


def _map_dirs_to_services() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in glob.glob("/etc/systemd/system/*bot*.service"):
        cp = ConfigParser()
        cp.read(path)
        if cp.has_option("Service", "WorkingDirectory"):
            workdir = cp.get("Service", "WorkingDirectory")
            dirname = Path(workdir).name
            service_name = Path(path).stem
            mapping[dirname] = service_name
    return mapping


async def _restart_services(changed_dirs: set[str], chat_id: int):
    dir_to_service = _map_dirs_to_services()
    restart_self = False
    restarted = []

    for d in changed_dirs:
        service = dir_to_service.get(d)
        if not service:
            continue
        if service == "coder-bot":
            restart_self = True
            continue
        proc = await asyncio.create_subprocess_exec(
            "sudo", "systemctl", "restart", service,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        restarted.append(service)

    if restarted:
        await bot.send_message(
            chat_id,
            f"🔄 Перезапущены сервисы: {', '.join(restarted)}",
        )

    if restart_self:
        await bot.send_message(chat_id, "🔄 Перезапускаю себя...")
        await asyncio.sleep(1)
        await asyncio.create_subprocess_exec("sudo", "systemctl", "restart", "coder-bot")


async def _update_status(msg: Message, start_time: float, stop_event: asyncio.Event):
    while not stop_event.is_set():
        await asyncio.sleep(30)
        if stop_event.is_set():
            break
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        try:
            await msg.edit_text(
                f"⏳ Ассистент работает... ({mins}:{secs:02d})",
                reply_markup=STOP_KB,
            )
        except Exception:
            pass


def _is_rate_limited(output: str) -> bool:
    lower = output.lower()
    return any(
        phrase in lower
        for phrase in ["rate limit", "rate_limit", "too many requests", "overloaded"]
    )


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _markdown_to_html(text: str) -> str:
    """Convert Claude markdown output to Telegram HTML."""
    result = []
    i = 0
    lines = text.split("\n")
    in_code_block = False
    code_lang = ""
    code_lines: list[str] = []

    for line in lines:
        # Code block start/end
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                code_lines = []
            else:
                # Close code block
                in_code_block = False
                code_content = _escape_html("\n".join(code_lines))
                if code_lang:
                    result.append(f'<pre><code class="language-{code_lang}">{code_content}</code></pre>')
                else:
                    result.append(f"<pre>{code_content}</pre>")
                code_lang = ""
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", line):
            result.append("─" * 20)
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            content = _inline_markdown_to_html(m.group(2).strip())
            if level <= 2:
                result.append(f"\n<b>{content.upper()}</b>")
            else:
                result.append(f"<b>{content}</b>")
            continue

        # Bullet list
        m = re.match(r"^(\s*)[*\-+]\s+(.*)", line)
        if m:
            indent = len(m.group(1)) // 2
            content = _inline_markdown_to_html(m.group(2))
            prefix = "  " * indent + "•"
            result.append(f"{prefix} {content}")
            continue

        # Numbered list
        m = re.match(r"^(\s*)\d+\.\s+(.*)", line)
        if m:
            indent = len(m.group(1)) // 2
            content = _inline_markdown_to_html(m.group(2))
            prefix = "  " * indent
            result.append(f"{prefix}{content}")
            continue

        # Normal line
        result.append(_inline_markdown_to_html(line))

    # Unclosed code block
    if in_code_block and code_lines:
        code_content = _escape_html("\n".join(code_lines))
        result.append(f"<pre>{code_content}</pre>")

    return "\n".join(result)


def _inline_markdown_to_html(text: str) -> str:
    """Convert inline markdown (bold, italic, code) to Telegram HTML."""
    # Protect inline code first
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            code = _escape_html(part[1:-1])
            out.append(f"<code>{code}</code>")
        else:
            p = _escape_html(part)
            # Bold: **text** or __text__
            p = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", p)
            p = re.sub(r"__(.+?)__", r"<b>\1</b>", p)
            # Italic: *text* or _text_ (not inside words)
            p = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", p)
            p = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<i>\1</i>", p)
            # Strikethrough: ~~text~~
            p = re.sub(r"~~(.+?)~~", r"<s>\1</s>", p)
            out.append(p)
    return "".join(out)


def _extract_tables(text: str) -> list[tuple[str, bool]]:
    """
    Split text into (segment, is_table) chunks.
    Returns list of (text, is_table) tuples.
    """
    lines = text.split("\n")
    segments: list[tuple[str, bool]] = []
    current: list[str] = []
    in_table = False

    for line in lines:
        is_table_line = bool(re.match(r"^\s*\|", line))
        if is_table_line != in_table:
            if current:
                segments.append(("\n".join(current), in_table))
            current = [line]
            in_table = is_table_line
        else:
            current.append(line)

    if current:
        segments.append(("\n".join(current), in_table))

    return segments


def _parse_md_table(table_text: str) -> tuple[list[str], list[list[str]]]:
    """Parse markdown table into headers and rows."""
    lines = [l.strip() for l in table_text.strip().splitlines() if l.strip()]
    # Filter out separator lines (---|---)
    data_lines = [l for l in lines if not re.match(r"^[\|\s\-:]+$", l)]

    def split_row(line: str) -> list[str]:
        parts = line.strip("|").split("|")
        return [p.strip() for p in parts]

    if not data_lines:
        return [], []

    headers = split_row(data_lines[0])
    rows = [split_row(l) for l in data_lines[1:]]
    return headers, rows


def _table_to_image(table_text: str) -> bytes | None:
    """Render a markdown table as a PNG image. Returns PNG bytes or None."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import io

        headers, rows = _parse_md_table(table_text)
        if not headers or not rows:
            return None

        # Normalize column count
        ncols = max(len(headers), max((len(r) for r in rows), default=0))
        headers = headers + [""] * (ncols - len(headers))
        rows = [r + [""] * (ncols - len(r)) for r in rows]

        nrows = len(rows)
        col_width = max(2.0, 10.0 / ncols)
        fig_w = col_width * ncols + 0.5
        fig_h = 0.5 + (nrows + 1) * 0.4

        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.axis("off")
        fig.patch.set_facecolor("#1e2128")

        # Build table data
        cell_text = rows
        table = ax.table(
            cellText=cell_text,
            colLabels=headers,
            cellLoc="center",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.4)

        # Style: dark theme
        for (row_idx, col_idx), cell in table.get_celld().items():
            cell.set_edgecolor("#444")
            if row_idx == 0:
                cell.set_facecolor("#2d5a8e")
                cell.set_text_props(color="white", fontweight="bold")
            elif row_idx % 2 == 0:
                cell.set_facecolor("#2a2d35")
                cell.set_text_props(color="#e0e0e0")
            else:
                cell.set_facecolor("#22252c")
                cell.set_text_props(color="#e0e0e0")

        plt.tight_layout(pad=0.3)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception:
        log.exception("Table image generation failed")
        return None


async def _send_formatted(chat_id: int, text: str):
    """Send Claude output with proper Telegram HTML formatting and table images."""
    if not text.strip():
        await bot.send_message(chat_id, "⚠️ Ассистент вернул пустой ответ.")
        return

    # Split code blocks out — protect them from table detection
    # First handle the full text: split into table / non-table segments
    # But we must not split inside code fences
    segments = _extract_tables_safe(text)

    for segment, is_table in segments:
        if not segment.strip():
            continue
        if is_table:
            img_bytes = await asyncio.to_thread(_table_to_image, segment)
            if img_bytes:
                from aiogram.types import BufferedInputFile
                await bot.send_photo(
                    chat_id,
                    BufferedInputFile(img_bytes, filename="table.png"),
                )
                continue
            # Fallback: monospace
            html = "<pre>" + _escape_html(segment) + "</pre>"
            await _send_html_chunked(chat_id, html)
        else:
            html = _markdown_to_html(segment)
            await _send_html_chunked(chat_id, html)


def _extract_tables_safe(text: str) -> list[tuple[str, bool]]:
    """
    Split text into (segment, is_table) tuples, but do NOT look inside code fences.
    """
    # First, extract code fences and replace with placeholders
    code_blocks: dict[str, str] = {}
    counter = [0]

    def replace_code(m):
        key = f"\x00CODE{counter[0]}\x00"
        code_blocks[key] = m.group(0)
        counter[0] += 1
        return key

    safe_text = re.sub(r"```[\s\S]*?```", replace_code, text)

    # Now split by tables
    segments = _extract_tables(safe_text)

    # Restore code blocks
    result = []
    for seg, is_table in segments:
        restored = seg
        for key, val in code_blocks.items():
            restored = restored.replace(key, val)
        result.append((restored, is_table))

    return result


async def _send_html_chunked(chat_id: int, html: str):
    """Send HTML-formatted text, chunking at MAX_MSG_LEN."""
    if not html.strip():
        return
    # Split by newlines to avoid cutting in the middle of a tag
    # Simple approach: chunk by character limit
    while html:
        chunk = html[:MAX_MSG_LEN]
        html = html[MAX_MSG_LEN:]
        try:
            await bot.send_message(chat_id, chunk, parse_mode="HTML")
        except Exception:
            # If HTML parse error, send as plain text
            try:
                plain = re.sub(r"<[^>]+>", "", chunk)
                await bot.send_message(chat_id, plain)
            except Exception:
                log.exception("Failed to send message chunk")


# ── Daily stats ──────────────────────────────────────────────────────────────

def _format_user_list(users: list[str], total: int, new_users: list[str]) -> str:
    """
    Format user display according to rules:
    - total <= 10: show all usernames
    - total > 10, new_users <= 20: show only new users with names
    - new_users > 20: show only numbers
    """
    n_new = len(new_users)
    if total <= 10:
        return f"  Активных: {total}, новых: {n_new}\n  Пользователи: {', '.join(users) or '—'}"
    elif n_new <= 20:
        names = ', '.join(new_users) if new_users else 'нет новых'
        return f"  Активных: {total}, новых: {n_new}\n  Новые: {names}"
    else:
        return f"  Активных: {total}, новых: {n_new}"


async def _collect_ielts_stats(env_path: str) -> str | None:
    """Query IELTS PostgreSQL for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT DISTINCT u.username, u.id,
                       (DATE(u.created_at) = CURRENT_DATE) AS is_new
                FROM users u
                JOIN sessions s ON s.user_id = u.id
                WHERE DATE(s.started_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        total = len(rows)
        all_names = [
            f"@{r['username']}" if r['username'] else f"id{r['id']}"
            for r in rows
        ]
        new_names = [
            f"@{r['username']}" if r['username'] else f"id{r['id']}"
            for r in rows if r['is_new']
        ]
        body = _format_user_list(all_names, total, new_names)
        return f"🎓 IELTS Speaking Bot\n{body}"
    except Exception as e:
        log.warning("IELTS stats error: %s", e)
        return None


async def _collect_vpr_stats(env_path: str) -> str | None:
    """Query VPR PostgreSQL for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT DISTINCT u.username, u.user_id,
                       (DATE(u.created_at) = CURRENT_DATE) AS is_new
                FROM users u
                JOIN task_attempts ta ON ta.user_id = u.user_id
                WHERE DATE(ta.attempted_at) = CURRENT_DATE
                UNION
                SELECT DISTINCT u.username, u.user_id,
                       (DATE(u.created_at) = CURRENT_DATE) AS is_new
                FROM users u
                JOIN test_sessions ts ON ts.user_id = u.user_id
                WHERE DATE(ts.started_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        # Deduplicate (UNION may return dupes across both tables)
        seen = set()
        unique_rows = []
        for r in rows:
            uid = r['user_id']
            if uid not in seen:
                seen.add(uid)
                unique_rows.append(r)

        total = len(unique_rows)
        all_names = [
            f"@{r['username']}" if r['username'] else f"id{r['user_id']}"
            for r in unique_rows
        ]
        new_names = [
            f"@{r['username']}" if r['username'] else f"id{r['user_id']}"
            for r in unique_rows if r['is_new']
        ]
        body = _format_user_list(all_names, total, new_names)
        return f"📝 ВПР Бот\n{body}"
    except Exception as e:
        log.warning("VPR stats error: %s", e)
        return None


async def _collect_convo_bot_stats(env_path: str, label: str) -> str | None:
    """Query English/Spanish PostgreSQL (conversations table) for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT DISTINCT u.username, u.id,
                       (DATE(u.created_at) = CURRENT_DATE) AS is_new
                FROM users u
                JOIN conversations c ON c.user_id = u.id
                WHERE DATE(c.created_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        total = len(rows)
        all_names = [
            f"@{r['username']}" if r['username'] else f"id{r['id']}"
            for r in rows
        ]
        new_names = [
            f"@{r['username']}" if r['username'] else f"id{r['id']}"
            for r in rows if r['is_new']
        ]
        body = _format_user_list(all_names, total, new_names)
        return f"{label}\n{body}"
    except Exception as e:
        log.warning("%s stats error: %s", label, e)
        return None


async def _collect_voice_stats(env_path: str) -> str | None:
    """Query Voice bot PostgreSQL for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT DISTINCT u.username, u.id,
                       (DATE(u.created_at) = CURRENT_DATE) AS is_new
                FROM users u
                JOIN transcriptions t ON t.user_id = u.id
                WHERE DATE(t.created_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        total = len(rows)
        all_names = [
            f"@{r['username']}" if r['username'] else f"id{r['id']}"
            for r in rows
        ]
        new_names = [
            f"@{r['username']}" if r['username'] else f"id{r['id']}"
            for r in rows if r['is_new']
        ]
        body = _format_user_list(all_names, total, new_names)
        return f"🎙 Voice Bot\n{body}"
    except Exception as e:
        log.warning("Voice stats error: %s", e)
        return None


async def _collect_interview_stats(env_path: str) -> str | None:
    """Query Interview PostgreSQL for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT DISTINCT u.user_id, u.username,
                       (DATE(u.created_at) = CURRENT_DATE) AS is_new
                FROM users u
                JOIN user_problems up ON up.user_id = u.user_id
                WHERE DATE(up.sent_at) = CURRENT_DATE
                   OR DATE(up.solved_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        total = len(rows)
        all_names = [
            f"@{r['username']}" if r['username'] else f"id{r['user_id']}"
            for r in rows
        ]
        new_names = [
            f"@{r['username']}" if r['username'] else f"id{r['user_id']}"
            for r in rows if r['is_new']
        ]
        body = _format_user_list(all_names, total, new_names)
        return f"💼 Interview Bot\n{body}"
    except Exception as e:
        log.warning("Interview stats error: %s", e)
        return None


async def _collect_millionaire_stats(env_path: str) -> str | None:
    """Query Millionaire PostgreSQL for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT user_id, username,
                       (DATE(created_at) = CURRENT_DATE) AS is_new
                FROM users
                WHERE DATE(last_visit) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        total = len(rows)
        all_names = [
            f"@{r['username']}" if r['username'] else f"id{r['user_id']}"
            for r in rows
        ]
        new_names = [
            f"@{r['username']}" if r['username'] else f"id{r['user_id']}"
            for r in rows if r['is_new']
        ]
        body = _format_user_list(all_names, total, new_names)
        return f"🏆 Millionaire Bot\n{body}"
    except Exception as e:
        log.warning("Millionaire stats error: %s", e)
        return None


async def _collect_monopoly_stats(env_path: str) -> str | None:
    """Query Monopoly PostgreSQL visits for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            row = await conn.fetchrow("""
                SELECT COUNT(DISTINCT player_id) AS cnt FROM visits
                WHERE DATE(visited_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        count = row['cnt'] if row else 0
        if not count:
            return None

        return f"🎲 Monopoly\n  Активных: {count}"
    except Exception as e:
        log.warning("Monopoly stats error: %s", e)
        return None


async def _collect_poker_stats(env_path: str) -> str | None:
    """Query Poker PostgreSQL for today's activity."""
    try:
        import asyncpg
        env = dotenv_values(env_path)
        dsn = env.get("DATABASE_URL")
        if not dsn:
            return None
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch("""
                SELECT user_id FROM game_sessions
                WHERE DATE(updated_at) = CURRENT_DATE
            """)
        finally:
            await conn.close()

        if not rows:
            return None

        total = len(rows)
        all_names = [str(r['user_id']) for r in rows]
        # Poker DB has no registration date, so no "new" distinction
        if total <= 10:
            body = f"  Активных: {total}\n  Пользователи: {', '.join(all_names)}"
        else:
            body = f"  Активных: {total}"
        return f"🃏 Poker Bot\n{body}"
    except Exception as e:
        log.warning("Poker stats error: %s", e)
        return None


async def _send_daily_stats():
    """Collect and send daily usage statistics."""
    date_str = datetime.now().strftime("%d.%m.%Y")
    sections = []

    # IELTS
    s = await _collect_ielts_stats(f"{REPO_ROOT}/ielts_bot/.env")
    if s:
        sections.append(s)

    # English bot
    s = await _collect_convo_bot_stats(f"{REPO_ROOT}/english_bot/.env", "🇬🇧 English Bot")
    if s:
        sections.append(s)

    # Spanish bot
    s = await _collect_convo_bot_stats(f"{REPO_ROOT}/spanish_bot/.env", "🇪🇸 Spanish Bot")
    if s:
        sections.append(s)

    # Voice bot
    s = await _collect_voice_stats(f"{REPO_ROOT}/voice_bot/.env")
    if s:
        sections.append(s)

    # VPR
    s = await _collect_vpr_stats(f"{REPO_ROOT}/vpr_bot/.env")
    if s:
        sections.append(s)

    # Interview bot
    s = await _collect_interview_stats(f"{REPO_ROOT}/interview_bot/.env")
    if s:
        sections.append(s)

    # Millionaire bot
    s = await _collect_millionaire_stats(f"{REPO_ROOT}/millionaire_bot/.env")
    if s:
        sections.append(s)

    # Monopoly
    s = await _collect_monopoly_stats(f"{REPO_ROOT}/monopoly_bot/.env")
    if s:
        sections.append(s)

    # Poker
    s = await _collect_poker_stats(f"{REPO_ROOT}/poker_bot/.env")
    if s:
        sections.append(s)

    if not sections:
        text = f"📊 Статистика за {date_str}\n\nНикто не пользовался сервисами сегодня."
    else:
        text = f"📊 Статистика за {date_str}\n\n" + "\n\n".join(sections)

    try:
        await bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        log.error("Failed to send daily stats: %s", e)


async def _daily_stats_scheduler():
    """Background task: sends stats every day at 00:00 Thailand time (UTC+7)."""
    TZ_TH = ZoneInfo("Asia/Bangkok")
    while True:
        now = datetime.now(TZ_TH)
        target = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_secs = (target - now).total_seconds()
        log.info("Daily stats scheduled in %.0f seconds (at %s TH)", wait_secs, target.strftime("%H:%M %d.%m"))
        await asyncio.sleep(wait_secs)
        await _send_daily_stats()


# ── Bot handlers ─────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Лимиты", callback_data="limits")]
        ]
    )
    await message.answer(
        "🤖 <b>Ассистент</b>\n"
        "Опиши задачу — выполню.",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "limits")
async def cb_limits(callback: CallbackQuery):
    info_lines = []
    cache_dir = Path.home() / ".claude"
    try:
        cache_files = list(cache_dir.glob("statsig/cache_v2*"))
        if cache_files:
            info_lines.append(f"Найдено кэш-файлов: {len(cache_files)}")
        settings = cache_dir / "settings.json"
        if settings.exists():
            info_lines.append("Конфигурация Claude: ✅")
    except Exception:
        pass

    if not info_lines:
        text = (
            "📊 Информация о лимитах появляется, когда Claude Code "
            "сообщает о rate limit в ответе."
        )
    else:
        text = "📊 Claude Code:\n" + "\n".join(info_lines)

    await callback.answer()
    await callback.message.answer(text)


@router.callback_query(F.data == "stop_task")
async def cb_stop_task(callback: CallbackQuery):
    global _stop_requested, _proc
    if _proc is not None and _proc.returncode is None:
        _stop_requested = True
        _proc.kill()
        await callback.answer("⏹ Останавливаю...")
    else:
        await callback.answer("Нет активной задачи.")


async def _transcribe_voice(path: str, mime: str) -> str | None:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))
    model_name = os.getenv("GOOGLE_AUDIO_MODEL", "gemini-2.5-flash")

    def _do():
        with open(path, "rb") as f:
            audio_bytes = f.read()
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                types.Part.from_text(
                    text="Transcribe the speech in this audio. Return only the transcribed text, nothing else."
                ),
            ],
        )
        return response.text.strip() or None

    return await asyncio.to_thread(_do)


EXT_BY_MIME = {
    "audio/ogg": ".ogg",
    "audio/oga": ".oga",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
}


@router.message(F.voice)
async def handle_voice(message: Message):
    global _busy, _proc, _stop_requested
    if _busy:
        await message.answer("⏳ Уже выполняю задачу. Дождись завершения.")
        return

    _busy = True
    _stop_requested = False
    start_time = time.time()

    status_msg = await message.answer("🎙 Транскрибирую голосовое сообщение...")
    tmp_path = None

    try:
        voice = message.voice
        mime = voice.mime_type or "audio/ogg"
        tg_file = await message.bot.get_file(voice.file_id)
        ext = EXT_BY_MIME.get(mime, ".ogg")

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name
        await message.bot.download_file(tg_file.file_path, tmp_path)

        text = await _transcribe_voice(tmp_path, mime)
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    if not text or not text.strip():
        _busy = False
        await status_msg.edit_text("❌ Не удалось распознать голосовое сообщение.")
        return

    text = text.strip()
    await status_msg.edit_text(f"🎙 <i>{text}</i>", parse_mode="HTML")

    # Now process transcribed text exactly like a text command
    status_msg2 = await message.answer("⏳ Запускаю Claude Code...", reply_markup=STOP_KB)
    stop_event = asyncio.Event()
    updater_task = asyncio.create_task(
        _update_status(status_msg2, start_time, stop_event)
    )

    try:
        old_head = _get_head()

        cmd = [CLAUDE_PATH, "-p", text, "--dangerously-skip-permissions", "--output-format", "text"]
        if text.lower() in CONTINUE_WORDS:
            cmd.append("--continue")

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        _proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=REPO_ROOT,
            env=env,
        )

        stdout, _ = await _proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)

        stop_event.set()

        if _stop_requested:
            try:
                await status_msg2.edit_text(f"⏹ Остановлено ({mins}:{secs:02d})")
            except Exception:
                pass
            if output.strip():
                await _send_formatted(message.chat.id, output)
            return

        try:
            await status_msg2.edit_text(f"✅ Готово за {mins}:{secs:02d}")
        except Exception:
            pass

        if _is_rate_limited(output):
            await message.answer("⚠️ Ассистент сообщает о rate limit. Попробуй позже.")

        await _send_formatted(message.chat.id, output)
        await _commit_and_push(message.chat.id)

        changed_dirs = _get_changed_dirs(old_head)
        if changed_dirs:
            await _restart_services(changed_dirs, message.chat.id)

        try:
            await message.answer(f"\n{random.choice(CREATION_QUOTES)}")
        except Exception:
            pass

    except Exception as e:
        stop_event.set()
        log.exception("Error running assistant (voice)")
        try:
            await message.answer(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _busy = False
        _proc = None
        if not updater_task.done():
            stop_event.set()
            updater_task.cancel()


@router.message(F.photo)
async def handle_photo(message: Message):
    global _busy, _proc, _stop_requested
    if _busy:
        await message.answer("⏳ Уже выполняю задачу. Дождись завершения.")
        return

    _busy = True
    _stop_requested = False
    caption = (message.caption or "").strip()
    start_time = time.time()

    status_msg = await message.answer("⏳ Запускаю Claude Code...", reply_markup=STOP_KB)
    stop_event = asyncio.Event()
    updater_task = asyncio.create_task(
        _update_status(status_msg, start_time, stop_event)
    )

    tmp_path = None
    try:
        photo = message.photo[-1]  # largest available size
        tg_file = await message.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        await message.bot.download_file(tg_file.file_path, tmp_path)

        if caption:
            text = f"{caption}\n\n(Изображение сохранено в: {tmp_path})"
        else:
            text = f"Пользователь прислал изображение без подписи. Файл: {tmp_path}"

        old_head = _get_head()

        cmd = [CLAUDE_PATH, "-p", text, "--dangerously-skip-permissions", "--output-format", "text"]
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        _proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=REPO_ROOT,
            env=env,
        )

        stdout, _ = await _proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)

        stop_event.set()

        if _stop_requested:
            try:
                await status_msg.edit_text(f"⏹ Остановлено ({mins}:{secs:02d})")
            except Exception:
                pass
            if output.strip():
                await _send_formatted(message.chat.id, output)
            return

        try:
            await status_msg.edit_text(f"✅ Готово за {mins}:{secs:02d}")
        except Exception:
            pass

        if _is_rate_limited(output):
            await message.answer("⚠️ Ассистент сообщает о rate limit. Попробуй позже.")

        await _send_formatted(message.chat.id, output)

        await _commit_and_push(message.chat.id)

        changed_dirs = _get_changed_dirs(old_head)
        if changed_dirs:
            await _restart_services(changed_dirs, message.chat.id)

        try:
            await message.answer(f"\n{random.choice(CREATION_QUOTES)}")
        except Exception:
            pass

    except Exception as e:
        stop_event.set()
        log.exception("Error running assistant with image")
        try:
            await message.answer(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _busy = False
        _proc = None
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        if not updater_task.done():
            stop_event.set()
            updater_task.cancel()


@router.message(F.text)
async def handle_task(message: Message):
    global _busy, _proc, _stop_requested
    if _busy:
        await message.answer("⏳ Уже выполняю задачу. Дождись завершения.")
        return

    _busy = True
    _stop_requested = False
    text = message.text.strip()
    start_time = time.time()

    status_msg = await message.answer("⏳ Запускаю Claude Code...", reply_markup=STOP_KB)
    stop_event = asyncio.Event()
    updater_task = asyncio.create_task(
        _update_status(status_msg, start_time, stop_event)
    )

    try:
        old_head = _get_head()

        cmd = [CLAUDE_PATH, "-p", text, "--dangerously-skip-permissions", "--output-format", "text"]
        if text.lower() in CONTINUE_WORDS:
            cmd.append("--continue")

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        _proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=REPO_ROOT,
            env=env,
        )

        stdout, _ = await _proc.communicate()

        output = stdout.decode("utf-8", errors="replace")
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)

        stop_event.set()

        if _stop_requested:
            try:
                await status_msg.edit_text(f"⏹ Остановлено ({mins}:{secs:02d})")
            except Exception:
                pass
            if output.strip():
                await _send_formatted(message.chat.id, output)
            return

        try:
            await status_msg.edit_text(f"✅ Готово за {mins}:{secs:02d}")
        except Exception:
            pass

        if _is_rate_limited(output):
            await message.answer("⚠️ Ассистент сообщает о rate limit. Попробуй позже.")

        await _send_formatted(message.chat.id, output)

        await _commit_and_push(message.chat.id)

        changed_dirs = _get_changed_dirs(old_head)
        if changed_dirs:
            await _restart_services(changed_dirs, message.chat.id)

        try:
            await message.answer(f"\n{random.choice(CREATION_QUOTES)}")
        except Exception:
            pass

    except Exception as e:
        stop_event.set()
        log.exception("Error running assistant")
        try:
            await message.answer(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _busy = False
        _proc = None
        if not updater_task.done():
            stop_event.set()
            updater_task.cancel()


async def main():
    log.info("Assistant bot starting...")
    asyncio.create_task(_daily_stats_scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
