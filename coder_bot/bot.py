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


async def _send_chunked(chat_id: int, text: str):
    if not text.strip():
        await bot.send_message(chat_id, "⚠️ Ассистент вернул пустой ответ.")
        return
    for i in range(0, len(text), MAX_MSG_LEN):
        chunk = text[i : i + MAX_MSG_LEN]
        await bot.send_message(chat_id, chunk)


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


async def _collect_poker_stats(db_path: str) -> str | None:
    """Query Poker SQLite for today's activity."""
    try:
        import aiosqlite
        if not Path(db_path).exists():
            return None
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("""
                SELECT user_id FROM game_sessions
                WHERE DATE(updated_at) = DATE('now')
            """) as cur:
                rows = await cur.fetchall()

        if not rows:
            return None

        total = len(rows)
        all_names = [str(r[0]) for r in rows]
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

    # VPR
    s = await _collect_vpr_stats(f"{REPO_ROOT}/vpr_bot/.env")
    if s:
        sections.append(s)

    # Poker
    s = await _collect_poker_stats(f"{REPO_ROOT}/poker_bot/poker.db")
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
                await _send_chunked(message.chat.id, output)
            return

        try:
            await status_msg.edit_text(f"✅ Готово за {mins}:{secs:02d}")
        except Exception:
            pass

        if _is_rate_limited(output):
            await message.answer("⚠️ Ассистент сообщает о rate limit. Попробуй позже.")

        await _send_chunked(message.chat.id, output)

        await _commit_and_push(message.chat.id)

        changed_dirs = _get_changed_dirs(old_head)
        if changed_dirs:
            await _restart_services(changed_dirs, message.chat.id)

        await message.answer(f"\n{random.choice(CREATION_QUOTES)}")

    except Exception as e:
        stop_event.set()
        log.exception("Error running assistant with image")
        await message.answer(f"❌ Ошибка: {e}")
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
                await _send_chunked(message.chat.id, output)
            return

        try:
            await status_msg.edit_text(f"✅ Готово за {mins}:{secs:02d}")
        except Exception:
            pass

        if _is_rate_limited(output):
            await message.answer("⚠️ Ассистент сообщает о rate limit. Попробуй позже.")

        await _send_chunked(message.chat.id, output)

        await _commit_and_push(message.chat.id)

        changed_dirs = _get_changed_dirs(old_head)
        if changed_dirs:
            await _restart_services(changed_dirs, message.chat.id)

        await message.answer(f"\n{random.choice(CREATION_QUOTES)}")

    except Exception as e:
        stop_event.set()
        log.exception("Error running assistant")
        await message.answer(f"❌ Ошибка: {e}")
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
