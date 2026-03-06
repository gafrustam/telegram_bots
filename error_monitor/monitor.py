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

# ── Nginx config ──────────────────────────────────────────
NGINX_ACCESS_LOG = "/var/log/nginx/ru.access.log"
NGINX_ERROR_LOG  = "/var/log/nginx/ru.error.log"

# URL path prefix → systemd service name (for error attribution)
URL_TO_SERVICE: dict[str, str] = {
    "/monopoly": "monopoly-server",
    "/ielts":    "ielts-server",
    "/poker":    "poker-server",
}

# Populated by discover_services() in main(); shared with nginx watchers
_discovered_services: dict[str, str] = {}


def _url_to_service(path: str) -> tuple[str | None, str | None]:
    """Map a URL path to (service_name, working_dir), or (None, None) if unknown."""
    for prefix, svc in URL_TO_SERVICE.items():
        if path.startswith(prefix):
            wd = _discovered_services.get(svc)
            return svc, wd
    return None, None


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
known_transient: set[str]     = set()  # hashes of errors that don't need intervention (silent after first time)

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

# ── Nginx helpers ─────────────────────────────────────────

NGINX_5XX_RE    = re.compile(r'" (5\d{2}) ')
NGINX_ERROR_LINE_RE = re.compile(r'\[error\]|\[crit\]|\[alert\]|\[emerg\]', re.IGNORECASE)
# Parse "METHOD /path HTTP/x" from access log line
NGINX_REQUEST_RE = re.compile(r'"(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) ([^ ]+) HTTP/')


def get_nginx_error_context(lines: int = 20) -> str:
    try:
        r = subprocess.run(
            ["tail", "-n", str(lines), NGINX_ERROR_LOG],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout or "(пусто)"
    except Exception as e:
        return f"(не удалось прочитать nginx error log: {e})"


async def handle_nginx_error(trigger_line: str, service: str | None, working_dir: str | None) -> None:
    """Handle an nginx error: alert admin and optionally restart/fix the service."""
    if service and service in fixing_now:
        logger.info("Already fixing %s, skip nginx error", service)
        return

    key = hashlib.md5(f"nginx:{trigger_line[:200]}".encode()).hexdigest()
    now = time.time()
    if key in seen_errors and now - seen_errors[key] < COOLDOWN_SEC:
        logger.info("Suppressed duplicate nginx error (cooldown)")
        return
    if key in known_transient:
        logger.info("Suppressed known transient nginx error")
        return
    seen_errors[key] = now

    excerpt = trigger_line.strip()[:400]
    svc_label = f"<code>{service}</code>" if service else "сайт (путь вне известных сервисов)"

    await tg(
        f"🌐 <b>Ошибка nginx</b> → {svc_label}\n\n"
        f"<code>{excerpt}</code>"
    )

    if not service or not working_dir:
        known_transient.add(key)
        return

    fixing_now.add(service)
    try:
        svc_logs = get_recent_logs(service, lines=30)
        nginx_ctx = get_nginx_error_context(20)
        log_context = (
            f"=== Nginx error log (последние строки) ===\n{nginx_ctx}\n\n"
            f"=== Логи сервиса {service} ===\n{svc_logs}"
        )

        # Check if service is simply not running → restart it
        r = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, timeout=5,
        )
        if r.stdout.strip() != "active":
            restart_status = await restart_service(service)
            await tg(
                f"♻️ <b>{service}</b> не был активен — перезапустил.\n{restart_status}"
            )
            return

        is_our_code = OUR_CODE_RE.search(svc_logs) is not None
        has_traceback = "Traceback (most recent call last)" in svc_logs

        if not (is_our_code or has_traceback):
            await tg(
                f"ℹ️ <b>{service}</b>: nginx вернул ошибку, но сервис активен и "
                f"трейсбека нет. Скорее всего сетевая/временная проблема."
            )
            known_transient.add(key)
            return

        await tg(f"🔧 <b>Исправляю ошибку в <code>{service}</code>…</b>")
        fix_result = await run_claude(service, log_context, working_dir)
        restart_status = await restart_service(service)
        await tg(
            f"✅ <b>Готово — <code>{service}</code></b>\n\n"
            f"{fix_result[:3500]}\n\n{restart_status}"
        )

    except Exception as e:
        logger.exception("handle_nginx_error crashed for %s", service)
        await tg(f"❌ <b>Monitor internal error (nginx/{service})</b>: {e}")
    finally:
        fixing_now.discard(service)


# ── Nginx log watchers ─────────────────────────────────────

async def watch_nginx_access_log() -> None:
    logger.info("Watching nginx access log: %s", NGINX_ACCESS_LOG)
    backoff = 5
    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                "tail", "-F", "-n", "0", NGINX_ACCESS_LOG,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            assert proc.stdout
            backoff = 5
            async for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                m = NGINX_5XX_RE.search(line)
                if not m:
                    continue
                pm = NGINX_REQUEST_RE.search(line)
                path = pm.group(1) if pm else "/"
                service, working_dir = _url_to_service(path)
                logger.info("Nginx 5xx detected: %s → %s", path, service)
                asyncio.create_task(handle_nginx_error(line, service, working_dir))
        except Exception as e:
            logger.error("watch_nginx_access_log crashed: %s — retrying in %ds", e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def watch_nginx_error_log() -> None:
    logger.info("Watching nginx error log: %s", NGINX_ERROR_LOG)
    backoff = 5
    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                "tail", "-F", "-n", "0", NGINX_ERROR_LOG,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            assert proc.stdout
            backoff = 5
            async for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line or not NGINX_ERROR_LINE_RE.search(line):
                    continue
                # Try to extract upstream path from error message
                pm = re.search(r'while (?:reading|sending|connecting to) upstream.*?"([^"]+)"', line)
                path = pm.group(1) if pm else ""
                service, working_dir = _url_to_service(path)
                logger.info("Nginx error log entry detected (service=%s): %s", service, line[:120])
                asyncio.create_task(handle_nginx_error(line, service, working_dir))
        except Exception as e:
            logger.error("watch_nginx_error_log crashed: %s — retrying in %ds", e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


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
    # If this error previously required no intervention, stay silent forever
    if key in known_transient:
        logger.info("Suppressed known transient error in %s", service)
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
            known_transient.add(key)
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
    global _discovered_services
    services = discover_services()
    _discovered_services = services

    if not services:
        logger.error("No services discovered — check BOT_ROOT or systemd. Exiting.")
        return

    logger.info("Starting error monitor. Services: %s", list(services))

    await tg(
        "🟢 <b>Error monitor запущен</b>\n"
        "Мониторю сервисы: " + ", ".join(f"<code>{s}</code>" for s in services) + "\n"
        "Мониторю nginx: access + error log"
    )

    tasks = [
        asyncio.create_task(watch_service(svc, wd))
        for svc, wd in services.items()
    ]
    tasks.append(asyncio.create_task(watch_nginx_access_log()))
    tasks.append(asyncio.create_task(watch_nginx_error_log()))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
