import asyncio
import glob
import logging
import os
import random
import re
import time
from configparser import ConfigParser
from pathlib import Path

from dotenv import load_dotenv

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


def _get_head() -> str:
    """Get current git HEAD sha."""
    import subprocess

    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def _get_changed_dirs(old_head: str) -> set[str]:
    """Return set of top-level directory names committed since old_head."""
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
    """Commit any uncommitted changes and push to remote."""
    import subprocess

    # Stage and commit if anything is left uncommitted
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

    # Push
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
    """Parse systemd service files to map WorkingDirectory basename → service name."""
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
    """Restart systemd services whose working directories were modified."""
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
        proc = await asyncio.create_subprocess_exec(
            "sudo", "systemctl", "restart", "coder-bot",
        )
        # won't reach here after restart


async def _update_status(msg: Message, start_time: float, stop_event: asyncio.Event):
    """Edit status message every 30s with elapsed time."""
    while not stop_event.is_set():
        await asyncio.sleep(30)
        if stop_event.is_set():
            break
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        try:
            await msg.edit_text(
                f"⏳ Claude Code работает... ({mins}:{secs:02d})",
                reply_markup=STOP_KB,
            )
        except Exception:
            pass


def _is_rate_limited(output: str) -> bool:
    """Check if output indicates a rate limit error."""
    lower = output.lower()
    return any(
        phrase in lower
        for phrase in ["rate limit", "rate_limit", "too many requests", "overloaded"]
    )


async def _send_chunked(chat_id: int, text: str):
    """Send text split into 4096-char chunks."""
    if not text.strip():
        await bot.send_message(chat_id, "⚠️ Claude Code вернул пустой ответ.")
        return
    for i in range(0, len(text), MAX_MSG_LEN):
        chunk = text[i : i + MAX_MSG_LEN]
        await bot.send_message(chat_id, chunk)


@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Лимиты", callback_data="limits")]
        ]
    )
    await message.answer(
        "⚡️ <b>Твой код — твоя суперсила.</b>\n"
        "🚀 Опиши задачу — и она оживёт.",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "limits")
async def cb_limits(callback: CallbackQuery):
    # Try to find usage info from Claude's cache files
    info_lines = []
    cache_dir = Path.home() / ".claude"
    try:
        # Check statsig cache for usage data
        cache_files = list(cache_dir.glob("statsig/cache_v2*"))
        if cache_files:
            info_lines.append(f"Найдено кэш-файлов: {len(cache_files)}")

        # Check if there's a recent rate limit log
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

        # Build command
        cmd = [CLAUDE_PATH, "-p", text, "--dangerously-skip-permissions", "--output-format", "text"]
        if text.lower() in CONTINUE_WORDS:
            cmd.append("--continue")

        # Env: remove CLAUDECODE to avoid nesting error
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

        # Edit status to show completion time
        try:
            await status_msg.edit_text(f"✅ Готово за {mins}:{secs:02d}")
        except Exception:
            pass

        # Check for rate limit
        if _is_rate_limited(output):
            await message.answer("⚠️ Claude Code сообщает о rate limit. Попробуй позже.")

        # Send output
        await _send_chunked(message.chat.id, output)

        # Commit remaining changes and push
        await _commit_and_push(message.chat.id)

        # Restart only services whose dirs were touched in this run
        changed_dirs = _get_changed_dirs(old_head)
        if changed_dirs:
            await _restart_services(changed_dirs, message.chat.id)

        # Send a creation quote
        await message.answer(f"\n{random.choice(CREATION_QUOTES)}")

    except Exception as e:
        stop_event.set()
        log.exception("Error running Claude Code")
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        _busy = False
        _proc = None
        if not updater_task.done():
            stop_event.set()
            updater_task.cancel()


async def main():
    log.info("Coder bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
