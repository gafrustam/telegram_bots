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
- **Ассистент** — это `coder_bot` (`/home/ubuntu/telegram_bots/coder_bot/bot.py`), бот который вызывает Claude Code

---

## Стандарты для каждого нового приложения (ОБЯЗАТЕЛЬНО, уровень — ПРЕМИУМ)

Каждое новое приложение должно быть готово к коммерческой продаже. Качество, архитектура и UX должны соответствовать production-уровню.

### 1. База данных — PostgreSQL

- **Всегда использовать PostgreSQL** для новых приложений.
- Создавать отдельную базу данных для каждого приложения:
  ```bash
  sudo -u postgres psql -c "CREATE USER <app>_user WITH PASSWORD '<password>';"
  sudo -u postgres psql -c "CREATE DATABASE <app>_db OWNER <app>_user;"
  ```
- Использовать `asyncpg` или `SQLAlchemy` (async) для работы с БД.
- Хранить `DATABASE_URL` в `.env` файле.
- Обязательны миграции через `alembic`.

### 2. AI-инструмент — Google (Gemini)

- По умолчанию использовать **Google Gemini API** (`google-generativeai` SDK).
- Модели: `gemini-2.5-flash` (текст и аудио), `gemini-2.5-pro` для сложных задач.
- API ключ хранить в `.env` как `GOOGLE_API_KEY`.

### 3. Логирование ошибок (ОБЯЗАТЕЛЬНО)

- Использовать стандартный `logging` модуль Python с уровнем `INFO` по умолчанию.
- Все ошибки логировать в файл `logs/<app>.log` с ротацией (`RotatingFileHandler`, max 5MB, 3 backup).
- Формат лога: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Все `except` блоки должны логировать traceback: `logger.exception("...")`.
- Пример настройки:
  ```python
  import logging
  from logging.handlers import RotatingFileHandler

  handler = RotatingFileHandler("logs/<app>.log", maxBytes=5_000_000, backupCount=3)
  logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()])
  logger = logging.getLogger(__name__)
  ```

### 4. Тесты — обязательная папка `tests/`

Структура папки `tests/`:
```
tests/
  unit/          # юнит-тесты бизнес-логики
  integration/   # тесты интеграций (БД, API, внешние сервисы)
  ui_ux/         # тесты UI/UX (Selenium/Playwright для веб, сценарные для ботов)
  conftest.py    # фикстуры pytest
```

**Требования к тестам:**
- Минимум 80% coverage для бизнес-логики.
- Unit-тесты: pytest, мокировать внешние зависимости (`unittest.mock`).
- Integration-тесты: тестовая БД PostgreSQL (`<app>_test_db`).
- UI/UX-тесты для веб-приложений: Playwright (`playwright`), проверять:
  - Все основные user flows (happy path)
  - Адаптивность (mobile/desktop)
  - Доступность (aria-labels, contrast)
  - Ошибки валидации форм
- Сценарные тесты для ботов: симуляция FSM-переходов.

**После написания кода — прогнать все тесты:**
```bash
cd /home/ubuntu/telegram_bots/<app>/
python -m pytest tests/ -v --tb=short
```
Все тесты должны проходить перед деплоем. Если тест падает — исправить, не пропускать.

### 5. Чек-лист лучших практик (спросить перед стартом)

Перед началом разработки нового приложения **задать пользователю вопрос**:

> "Какие дополнительные лучшие практики применить к этому приложению? Например:
> - Rate limiting и защита от флуда
> - Кэширование (Redis)
> - CI/CD pipeline
> - Метрики и мониторинг (Prometheus/Grafana)
> - Internationalisation (i18n)
> - Webhook vs polling для бота
> - A/B тестирование
> - Документация API (OpenAPI/Swagger)"

### 6. Защита от prompt injection (где уместно)

Везде, где пользовательский ввод передаётся в AI-запрос:
- Санитизировать ввод: убирать системные-подобные инструкции.
- Добавлять явные границы в промпт:
  ```
  [USER INPUT START]
  {user_text}
  [USER INPUT END]
  ```
- Ограничивать длину пользовательского ввода перед передачей в AI.
- Логировать подозрительные попытки (ввод содержит "ignore previous", "system:", "assistant:", "you are", "disregard").
- Пример проверки:
  ```python
  INJECTION_PATTERNS = ["ignore previous", "system:", "you are now", "disregard", "assistant:"]

  def is_suspicious(text: str) -> bool:
      lower = text.lower()
      return any(p in lower for p in INJECTION_PATTERNS)
  ```

### 7. Структура нового приложения (шаблон)

```
<app>_bot/
  bot.py              # точка входа
  config.py           # настройки из .env
  db/
    models.py         # SQLAlchemy модели
    migrations/       # alembic миграции
  handlers/           # обработчики команд/колбэков
  services/           # бизнес-логика
  ai/                 # интеграция с Google Gemini
  logs/               # файлы логов
  tests/
    unit/
    integration/
    ui_ux/
    conftest.py
  .env                # секреты (не в git)
  requirements.txt
```
