# Правила для ассистента (ОБЯЗАТЕЛЬНО)

## После деплоя любого нового сервиса

**ВСЕГДА** выполнять эти шаги — без исключений:

1. Проверить что сервис запустился:
   ```
   systemctl status <service>.service
   ```
2. Перезапустить error-monitor, чтобы он подхватил новый сервис:
   ```
   sudo systemctl restart error-monitor.service
   ```
3. Убедиться что новый сервис появился в процессах error-monitor:
   ```
   systemctl status error-monitor.service | grep <service>
   ```

> Error monitor (`/home/ubuntu/telegram_bots/error_monitor/monitor.py`) автоматически
> обнаруживает все systemd-сервисы с `WorkingDirectory` в `/home/ubuntu/telegram_bots/`,
> но только при **запуске** — поэтому перезапуск обязателен после добавления нового сервиса.

## Структура проекта

- Все боты в `/home/ubuntu/telegram_bots/<name>_bot/`
- Сервисы: `/etc/systemd/system/<name>.service`
- Error monitor: `error-monitor.service`
- Admin: gafrustam (Telegram ID: 138468116)
