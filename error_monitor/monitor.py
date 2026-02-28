#!/usr/bin/env python3
"""
error_monitor.py — Watches all bot/app systemd services for errors.

On error:
  1. Sends Telegram alert to admin with error excerpt
  2. If traceback found → tells admin "fixing...", runs Claude Code
  3. Sends result of fix
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ── Config ────────────────────────────────────────────────

# Uses the coder-bot token so messages look like they're from Claude Code bot
TELEGRAM_TOKEN = "8549917399:AAGMkkcouoQxSIdTJPNcD7Ec3qXab3aUqWk"
ADMIN_CHAT_ID  = 138468116

CLAUDE_PATH = "/home/ubuntu/.local/bin/claude"

# Root directory — any service whose WorkingDirectory is under here gets monitored
BOT_ROOT = "/home/ubuntu/telegram_bots"

# Services to always exclude from monitoring (e.g. the monitor itself)
EXCLUDED_SERVICES: set[str] = {"error-monitor"}


def discover_services() -> dict[str, str]:
    """
    Auto-discover all systemd services whose WorkingDirectory is under BOT_ROOT.
    Returns {service_name: working_directory}.
    """
    try:
        # Step 1: collect names of all loaded .service units
        r = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--state=loaded",
             "--no-pager", "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=10,
        )
        names = []
        for line in r.stdout.splitlines():
            parts = line.split()
            if parts and parts[0].endswith(".service"):
                names.append(parts[0])

        if not names:
            return {}

        # Step 2: batch-query WorkingDirectory for all of them at once
        r2 = subprocess.run(
            ["systemctl", "show", *names, "--property=Id,WorkingDirectory"],
            capture_output=True, text=True, timeout=15,
        )

        services: dict[str, str] = {}
        current_id = ""
        current_wd = ""

        def _flush():
            if current_id and current_wd.startswith(BOT_ROOT) and current_id not in EXCLUDED_SERVICES:
                services[current_id] = current_wd

        for line in r2.stdout.splitlines():
            if not line.strip():
                _flush()
                current_id = ""
                current_wd = ""
            elif line.startswith("Id="):
                val = line.split("=", 1)[1].strip()
                current_id = val[: -len(".service")] if val.endswith(".service") else val
            elif line.startswith("WorkingDirectory="):
                current_wd = line.split("=", 1)[1].strip()

        _flush()  # last block has no trailing blank line
        return services

    except Exception as e:
        # Fall back gracefully — log will appear at startup
        print(f"[monitor] Service discovery failed: {e}", flush=True)
        return {}

# Cooldown: same error won't trigger again for this many seconds
COOLDOWN_SEC = 300

# Max time given to Claude to fix (seconds)
CLAUDE_TIMEOUT = 360

# ── Patterns ─────────────────────────────────────────────

# Lines that should trigger error handling
ERROR_RE = re.compile(
    r"\b(ERROR|CRITICAL|Traceback \(most recent call last\)|"
    r"raise \w+|unhandled exception|FAILED TO START|"
    r"NameError|AttributeError|ImportError|ModuleNotFoundError|"
    r"SyntaxError|TypeError|ValueError|KeyError|IndexError|RuntimeError)\b",
    re.IGNORECASE,
)

# Lines that look like errors but are actually noise — skip them
IGNORE_RE = re.compile(
    r"(Connection (refused|reset|closed|timed out)|TimeoutError|ConnectionError|"
    r"aiohttp.*ClientConnector|NetworkError|RetryAfter|"
    r"Failed to fetch update|TelegramNetworkError|"
    r"Polling (stopped|started)|Run polling|"
    r"INFO.*aiogram|DEBUG.*|"
    r"WARN.*retry|WARN.*reconnect|"
    r"SSL.*handshake|certificate verify|"
    r"error_monitor)",  # don't react to our own logs
    re.IGNORECASE,
)

# If ANY of these strings appear in the log context, we consider it "our code's fault"
# and worth trying to auto-fix
OUR_CODE_RE = re.compile(r'File "/home/ubuntu/telegram_bots/')

# ── State ────────────────────────────────────────────────

seen_errors: dict[str, float] = {}     # hash → last_seen_ts
fixing_now: set[str]          = set()  # services currently being fixed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("monitor")

# ── Telegram helper ───────────────────────────────────────

def tg_send_sync(text: str) -> None:
    """Send a Telegram message (synchronous, runs in thread)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": ADMIN_CHAT_ID,
        "text":    text[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        logger.error("tg_send failed: %s", e)


async def tg(text: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, tg_send_sync, text)

# ── Log collection ────────────────────────────────────────

def get_recent_logs(service: str, lines: int = 40) -> str:
    try:
        r = subprocess.run(
            ["journalctl", "-u", service, "-n", str(lines),
             "--no-pager", "--output=short-precise"],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout
    except Exception as e:
        return f"(could not read logs: {e})"

# ── Claude fixer ─────────────────────────────────────────

async def run_claude(service: str, log_context: str, working_dir: str) -> str:
    prompt = (
        f"The systemd service '{service}' has an error in production right now.\n"
        f"Here are the recent logs (most recent at bottom):\n\n"
        f"```\n{log_context[-4000:]}\n```\n\n"
        f"Please:\n"
        f"1. Identify the root cause by reading the relevant source files\n"
        f"2. Fix the bug in the code\n\n"
        f"Note: the service will be restarted automatically after your fix — "
        f"do NOT run systemctl restart yourself.\n\n"
        f"If this is a transient issue (network, external API outage, rate limit) "
        f"that cannot be fixed by changing code, say so in one sentence.\n\n"
        f"End your response with a brief summary of what you changed (or why no change was needed)."
    )

    cmd = [
        CLAUDE_PATH,
        "--dangerously-skip-permissions",
        "--print",
        prompt,
    ]

    logger.info("Starting Claude for %s in %s", service, working_dir)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "HOME": "/home/ubuntu"},
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=CLAUDE_TIMEOUT
        )
        out = (stdout or b"").decode("utf-8", errors="replace").strip()
        err = (stderr or b"").decode("utf-8", errors="replace").strip()
        if not out and err:
            out = f"(stderr): {err[:500]}"
        return out or "(Claude вернул пустой ответ)"
    except asyncio.TimeoutError:
        return f"⏱ Claude не уложился в {CLAUDE_TIMEOUT}с — завершаю."
    except Exception as e:
        return f"Ошибка запуска Claude: {e}"

# ── Service restarter ─────────────────────────────────────

async def restart_service(service: str) -> str:
    """Restart a systemd service and return a status string."""
    loop = asyncio.get_event_loop()
    def _restart():
        try:
            r = subprocess.run(
                ["sudo", "systemctl", "restart", service],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                return f"♻️ <b>{service}</b> перезапущен успешно."
            else:
                return (
                    f"⚠️ Не удалось перезапустить <b>{service}</b> "
                    f"(код {r.returncode}): {r.stderr.strip()[:200]}"
                )
        except Exception as e:
            return f"⚠️ Ошибка при перезапуске <b>{service}</b>: {e}"
    return await loop.run_in_executor(None, _restart)

# ── Main error handler ────────────────────────────────────

async def handle_error(service: str, trigger_line: str, working_dir: str) -> None:
    if service in fixing_now:
        logger.info("Already fixing %s, skip duplicate error", service)
        return

    # Deduplicate by hash (first 200 chars of trigger)
    key = hashlib.md5(f"{service}:{trigger_line[:200]}".encode()).hexdigest()
    now = time.time()
    if key in seen_errors and now - seen_errors[key] < COOLDOWN_SEC:
        logger.info("Suppressed duplicate error in %s (cooldown)", service)
        return
    seen_errors[key] = now

    fixing_now.add(service)
    try:
        log_context = get_recent_logs(service, lines=40)
        excerpt = trigger_line.strip()[:400]

        # ── Step 1: alert ──────────────────────────────────
        await tg(
            f"🚨 <b>Ошибка в <code>{service}</code></b>\n\n"
            f"<code>{excerpt}</code>"
        )

        # ── Step 2: decide if code fix is possible ─────────
        is_our_code = OUR_CODE_RE.search(log_context) is not None
        has_traceback = "Traceback (most recent call last)" in log_context

        if not (is_our_code or has_traceback):
            await tg(
                f"ℹ️ <b>{service}</b>: ошибка не в коде "
                f"(сеть / внешний сервис). Ручное вмешательство не требуется."
            )
            return

        # ── Step 3: fix ────────────────────────────────────
        await tg(f"🔧 <b>Исправляю ошибку в <code>{service}</code>…</b>")
        fix_result = await run_claude(service, log_context, working_dir)

        # ── Step 4: restart service after fix ──────────────
        restart_status = await restart_service(service)

        # ── Step 5: report ─────────────────────────────────
        summary = fix_result[:3500]
        await tg(
            f"✅ <b>Готово — <code>{service}</code></b>\n\n"
            f"{summary}\n\n"
            f"{restart_status}"
        )

    except Exception as e:
        logger.exception("handle_error crashed for %s", service)
        await tg(f"❌ <b>Monitor internal error</b> ({service}): {e}")
    finally:
        fixing_now.discard(service)

# ── Per-service log watcher ───────────────────────────────

async def watch_service(service: str, working_dir: str) -> None:
    logger.info("Watching %s", service)
    backoff = 5

    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                "journalctl", "-fu", service, "--output=short", "--since=now",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            assert proc.stdout
            backoff = 5  # reset on successful start

            async for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                if IGNORE_RE.search(line):
                    continue
                if ERROR_RE.search(line):
                    logger.info("Error detected in %s: %s", service, line[:120])
                    asyncio.create_task(handle_error(service, line, working_dir))

        except Exception as e:
            logger.error("watch_service(%s) crashed: %s — retrying in %ds", service, e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue

        # journalctl exited — restart
        await asyncio.sleep(backoff)

# ── Entry point ───────────────────────────────────────────

async def main() -> None:
    services = discover_services()

    if not services:
        logger.error("No services discovered — check BOT_ROOT or systemd. Exiting.")
        return

    logger.info("Starting error monitor. Services: %s", list(services))

    await tg(
        "🟢 <b>Error monitor запущен</b>\n"
        "Мониторю: " + ", ".join(f"<code>{s}</code>" for s in services)
    )

    tasks = [
        asyncio.create_task(watch_service(svc, wd))
        for svc, wd in services.items()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
