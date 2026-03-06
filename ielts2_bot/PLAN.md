# IELTS Complete Bot — Plan

**Bot token:** `8372950989:AAH-jowbVrmrUIoaxO3jHUBZqb0yAJ9zTdA`
**Bot username:** to be confirmed after @BotFather setup

---

## 1. Обзор продукта

Полноценный IELTS-тренажёр, покрывающий все 4 секции экзамена:

| Секция    | Интерфейс        | AI-роль                                     |
|-----------|------------------|---------------------------------------------|
| Listening | Telegram         | Генерация аудио + оценка ответов            |
| Reading   | Telegram         | Подбор/генерация текстов + проверка ответов |
| Writing   | Telegram         | Оценка эссе / письма по IELTS-критериям     |
| Speaking  | Web App (WebRTC) | Оценка речи (fluency, lexis, grammar, pron) |

---

## 2. Архитектура системы

```
ielts2_bot/
  bot.py                  # точка входа (aiogram 3.x, webhook)
  config.py               # настройки из .env
  db/
    models.py             # SQLAlchemy async модели
    repository.py         # CRUD-операции
    migrations/           # Alembic
  handlers/
    __init__.py
    menu.py               # главное меню, навигация
    listening.py          # FSM Listening
    reading.py            # FSM Reading
    writing.py            # FSM Writing
    speaking.py           # кнопка → открыть Web App
    admin.py              # /admin панель
  services/
    listening_service.py  # логика Listening-теста
    reading_service.py    # логика Reading-теста
    writing_service.py    # логика Writing-теста
    speaking_service.py   # управление speaking-сессиями
    ai_service.py         # единый фасад к Gemini/OpenAI
    progress_service.py   # прогресс пользователя, статистика
    scheduler.py          # ежедневные задачи, напоминания
  ai/
    prompts/              # шаблоны промптов по секциям
    gemini_client.py      # Google Gemini API
    tts_client.py         # Text-to-Speech (аудио вопросы)
    stt_client.py         # Speech-to-Text (Speaking fallback)
  webapp/                 # SPA для Speaking
    index.html
    css/main.css
    js/
      recorder.js         # WebRTC MediaRecorder
      api.js              # общение с FastAPI
      app.js              # логика SPA
  server.py               # FastAPI (порт 8004): Speaking API + webhook
  logs/
  tests/
    unit/
    integration/
    ui_ux/
    conftest.py
  .env
  requirements.txt
  alembic.ini
```

---

## 3. Технологический стек

| Слой             | Технология                                      |
|------------------|-------------------------------------------------|
| Bot framework    | aiogram 3.x (FSM, InlineKeyboard, WebApp)       |
| Web backend      | FastAPI + uvicorn (async)                       |
| База данных       | PostgreSQL 15 + asyncpg + SQLAlchemy 2 (async)  |
| Миграции         | Alembic                                         |
| AI (текст)       | Google Gemini 2.5 Flash / 2.5 Pro               |
| AI (аудио оценка)| Google Gemini 2.5 Flash (multimodal audio)      |
| TTS              | Google Cloud TTS или OpenAI TTS                 |
| STT (fallback)   | Google Speech-to-Text или Whisper API           |
| Кэш              | Redis (rate limiting, сессии, очередь задач)    |
| Очередь задач    | Celery + Redis (генерация контента асинхронно)  |
| WebRTC/Audio     | Browser MediaRecorder API (WebM/OGG → сервер)  |
| Frontend         | Vanilla JS + Telegram WebApp SDK                |
| Деплой           | systemd, nginx reverse proxy                    |
| Мониторинг       | error-monitor.service (уже существует)          |

---

## 4. База данных — схема

### users
```sql
id BIGINT PRIMARY KEY          -- Telegram user ID
username TEXT
full_name TEXT
language TEXT DEFAULT 'ru'     -- ru / en
target_band NUMERIC(2,1)       -- целевой балл (5.0 – 9.0)
created_at TIMESTAMPTZ
last_active TIMESTAMPTZ
notification_time TIME         -- время ежедневного напоминания (UTC)
```

### sessions
```sql
id UUID PRIMARY KEY
user_id BIGINT FK users
section TEXT                   -- listening|reading|writing|speaking
mode TEXT                      -- practice|mock_test
started_at TIMESTAMPTZ
finished_at TIMESTAMPTZ
band_score NUMERIC(2,1)
detailed_scores JSONB          -- {"task_achievement": 7, "coherence": 6, ...}
raw_input TEXT / BYTEA         -- пользовательский ответ
ai_feedback TEXT
```

### content_items
```sql
id UUID PRIMARY KEY
section TEXT                   -- listening|reading|writing|speaking
difficulty TEXT                -- band_5|band_6|band_7|band_8|band_9
topic TEXT
content JSONB                  -- структура зависит от секции
created_at TIMESTAMPTZ
source TEXT                    -- ai_generated|cambridge|custom
```

### user_progress
```sql
user_id BIGINT FK users
section TEXT
sessions_count INT
avg_band NUMERIC(2,1)
last_session_at TIMESTAMPTZ
weak_areas JSONB               -- {"vocabulary": true, "coherence": false}
streak_days INT
```

### daily_tasks
```sql
id UUID PRIMARY KEY
user_id BIGINT FK
section TEXT
content_item_id UUID FK
assigned_at DATE
completed_at TIMESTAMPTZ
```

---

## 5. Секция: Listening

### Формат IELTS Listening
- 4 секции, 40 вопросов, ~30 минут
- Типы: multiple choice, matching, plan/map labelling, form/note completion, sentence completion

### Логика в боте

1. Пользователь выбирает режим: **Practice** (1 секция) или **Mock Test** (4 секции)
2. Бот отправляет аудио (MP3) через Telegram `send_audio` / `send_voice`
3. Аудио генерируется через TTS из заранее подготовленных скриптов (Cambridge-style)
4. После аудио — вопросы инлайн-клавиатурой (MC) или текстом (form completion)
5. Пользователь отвечает. После секции — AI оценка + ключи ответов
6. Финал: band score + детальный разбор ошибок

### Генерация контента
- Gemini 2.5 Pro генерирует скрипт диалога/монолога по теме
- TTS (Google Cloud / OpenAI) озвучивает скрипт
- Вопросы и ключи ответов генерируются вместе со скриптом
- Контент кэшируется в `content_items` (не генерировать каждый раз)

### FSM состояния
```
ListeningState:
  choosing_mode
  choosing_topic
  playing_audio
  answering_questions
  viewing_results
```

---

## 6. Секция: Reading

### Формат IELTS Reading
- Academic: 3 длинных текста (~2700 слов), 40 вопросов, 60 минут
- General: 3 секции (объявления → длинный текст), 40 вопросов
- Типы: T/F/NG, multiple choice, matching headings, sentence completion, summary completion

### Логика в боте

1. Выбор типа: Academic / General Training
2. Выбор темы или случайная
3. Бот отправляет текст **частями** (Telegram ограничение 4096 символов на сообщение)
   - Текст разбивается на части, каждая с нумерацией параграфов
   - Дополнительно: возможность отправить как документ (PDF)
4. Вопросы по очереди или блоками
5. Таймер (опционально, через callback с обновлением сообщения)
6. AI проверяет ответы, объясняет правильные ответы со ссылкой на абзацы

### Типы вопросов — реализация в Telegram

| Тип вопроса              | UI в боте                                    |
|--------------------------|----------------------------------------------|
| Multiple choice (A/B/C/D)| InlineKeyboard с 4 кнопками                  |
| True/False/Not Given     | InlineKeyboard с 3 кнопками                  |
| Matching headings        | Numbered inline buttons (1-8 + A-H)          |
| Sentence/summary compl.  | Text input от пользователя                   |
| Short answer             | Text input                                   |

### FSM состояния
```
ReadingState:
  choosing_type         -- Academic / General
  choosing_topic
  reading_text          -- текст разбит на страницы
  answering_questions
  viewing_results
```

---

## 7. Секция: Writing

### Формат IELTS Writing
- **Task 1 Academic**: описание графика/таблицы/диаграммы/карты (минимум 150 слов, 20 мин)
- **Task 1 General**: формальное или полуформальное письмо (минимум 150 слов, 20 мин)
- **Task 2**: эссе-аргументация на тему (минимум 250 слов, 40 мин)

### Логика в боте

1. Выбор задания: Task 1 (Academic / General) или Task 2
2. Для Task 1 Academic — бот присылает описание графика (текстом) или изображение
3. Пользователь пишет ответ в Telegram (текстовое сообщение)
4. Если ответ в нескольких сообщениях — бот накапливает с кнопкой "Готово"
5. AI оценивает по 4 критериям IELTS:
   - Task Achievement / Task Response
   - Coherence and Cohesion
   - Lexical Resource
   - Grammatical Range and Accuracy
6. Feedback: общий band + по каждому критерию + конкретные примеры ошибок + исправленный вариант

### AI-промпт структура (Writing)
```
System: Ты — эксперт-экзаменатор IELTS с 15-летним опытом. Оценивай строго и честно.
Критерии: [детальные дескрипторы band 1-9 для каждого критерия]
Task: [формулировка задания]
[USER INPUT START]
{essay_text}
[USER INPUT END]
Output: JSON с полями band_score, criteria, feedback, corrected_sample
```

### Подсчёт слов
- Бот считает слова перед отправкой на оценку
- Предупреждение если < 150 / < 250 слов

### FSM состояния
```
WritingState:
  choosing_task         -- Task 1 / Task 2
  choosing_type         -- Academic / General (для Task 1)
  choosing_topic
  receiving_input       -- накопление текста
  waiting_for_done      -- пользователь нажал "Готово"
  viewing_feedback
```

---

## 8. Секция: Speaking (Web App)

### Формат IELTS Speaking
- **Part 1**: Введение + вопросы на личные темы (4-5 мин)
- **Part 2**: Cue card (индивидуальный монолог, 3-4 мин, 1 мин подготовки)
- **Part 3**: Дискуссия на абстрактные темы (4-5 мин)

### Почему Web App
- Telegram не позволяет записать голос внутри бота в реальном времени (только присылать голосовые)
- Нужен WebRTC + MediaRecorder в браузере
- Web App открывается кнопкой `WebAppInfo` прямо в Telegram (без перехода в браузер)

### Web App архитектура

```
Browser (Telegram WebApp)
  ↓ открытие
  WebApp SPA (React или Vanilla JS)
    - получает initData от Telegram.WebApp
    - аутентификация через HMAC на сервере
    - Part 1: вопросы → запись голоса → upload → пауза → следующий вопрос
    - Part 2: cue card → таймер 1 мин подготовки → запись 2 мин → upload
    - Part 3: вопросы → запись голоса → upload
    ↓ WebSocket / HTTP
  FastAPI server (порт 8004)
    - validate initData
    - manage speaking session state
    - receive audio chunks → store temp
    - after each part: send to Gemini for partial feedback
    - after full session: aggregate scores → send results to Telegram via bot.send_message
```

### Speaking — аудио pipeline

```
Browser MediaRecorder (WebM/Opus, 48kHz)
  → chunked upload to FastAPI
  → ffmpeg конвертация → MP3/WAV
  → Gemini 2.5 Flash (multimodal audio input)
  → JSON: {band, fluency, lexical, grammar, pronunciation, transcript, feedback}
```

### Критерии оценки Speaking (IELTS)
- **Fluency and Coherence** (FC): темп речи, паузы, связность
- **Lexical Resource** (LR): разнообразие и точность лексики
- **Grammatical Range and Accuracy** (GRA): сложность и корректность грамматики
- **Pronunciation** (P): чёткость, интонация, ударение

### FSM состояния Speaking (в боте — минимально)
```
SpeakingState:
  idle
  session_active        -- ожидание пока Web App завершит сессию
```

---

## 9. Главное меню и навигация

```
/start → приветствие + выбор секции

Главное меню:
  [Listening] [Reading]
  [Writing]   [Speaking]
  [Мой прогресс] [Настройки]

/practice → быстрая практика случайной секции
/test → полный mock test (все 4 секции подряд)
/progress → статистика и прогресс
/settings → язык, цель балла, уведомления
/help → справка
```

---

## 10. Прогресс и геймификация

- **Streak**: дней подряд практики (огонёк в UI)
- **Band history**: график прогресса по каждой секции
- **Weak areas**: автоматическое определение слабых мест (на основе AI-оценок)
- **Daily task**: ежедневное задание (scheduler, отправка утром)
- **Achievements**: первый тест, серия 7 дней, первый band 7.0, etc.
- **Leaderboard**: опциональный рейтинг (если несколько пользователей)

---

## 11. Режимы работы

### Practice Mode
- Пользователь выбирает секцию и тему
- 1 задание / 1 секция / 10 вопросов
- Мгновенная обратная связь после каждого ответа или в конце
- Подходит для ежедневной практики

### Mock Test Mode
- Все 4 секции подряд с таймером
- Формат максимально приближен к реальному IELTS
- Результат сохраняется как полный тест
- Детальный отчёт в конце

---

## 12. Защита и безопасность

- **Prompt injection**: проверка всего пользовательского текста перед отправкой в AI
  ```python
  INJECTION_PATTERNS = ["ignore previous", "system:", "you are now", "disregard", "forget"]
  ```
- **Rate limiting**: через Redis — не более 10 AI-запросов в минуту на пользователя
- **Auth для Web App**: HMAC-SHA256 проверка Telegram initData
- **Ограничение длины**: Writing max 1500 слов, Speaking audio max 5 минут
- **Анти-флуд**: aiogram ThrottlingMiddleware

---

## 13. AI-провайдер

Основной: **Google Gemini 2.5 Flash** для всего (текст + аудио в Speaking/Listening)
Fallback: **OpenAI GPT-4o-mini** для текстовых задач (Writing, Reading)

Конфигурация через `.env`:
```
AI_PROVIDER=google
GOOGLE_API_KEY=...
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_AUDIO_MODEL=gemini-2.5-flash
OPENAI_API_KEY=...         # fallback
OPENAI_MODEL=gpt-4o-mini   # fallback
```

---

## 14. Контентная стратегия

### Откуда брать контент

1. **Cambridge IELTS Books (1-18)**: тексты для Reading (public knowledge), аудио-скрипты
   - Использовать как reference при генерации AI (стиль, сложность, форматы)
   - Не копировать напрямую (copyright)

2. **AI-генерация**: все тексты, аудио-скрипты, writing prompts генерирует Gemini
   - Параметры: тема, уровень сложности (band target), тип вопросов
   - Строгие инструкции имитировать Cambridge IELTS style

3. **Пул заготовленного контента**: 50+ текстов / скриптов сохраняются в БД при первом запуске
   - Seed script для наполнения контент-базы
   - Новый контент догенерируется через Celery воркер

### Темы (Listening & Reading)
```
Education, Technology, Environment, Health, Society,
Business, Science, History, Travel, Arts & Culture,
Architecture, Wildlife, Space, Food & Agriculture
```

---

## 15. Localisation

- Интерфейс бота: **русский** (default) и **английский**
- Задания IELTS: всегда на **английском** (это и есть тест)
- AI-фидбек: на языке интерфейса пользователя
- i18n через `fluent.runtime` или простой dict с ключами

---

## 16. Деплой

```
systemd-сервисы:
  ielts2-bot.service      # aiogram polling или webhook
  ielts2-server.service   # FastAPI (Speaking API + webhook endpoint)

nginx:
  /ielts2/                → порт 8004 (FastAPI)
  /ielts2/webapp/         → статика Web App

PostgreSQL:
  ielts2_db, ielts2_user

Redis:
  уже установлен (используется poker-ботом)
```

---

## 17. Тесты

```
tests/
  unit/
    test_band_calculator.py    # подсчёт итогового балла
    test_word_counter.py       # подсчёт слов (Writing)
    test_prompt_injection.py   # детекция инжектов
    test_content_validator.py  # валидация JSON от AI
  integration/
    test_db_operations.py      # CRUD операции
    test_ai_service.py         # мок AI-ответов
    test_speaking_session.py   # Speaking flow через API
  ui_ux/
    test_listening_flow.py     # FSM Listening сценарий
    test_reading_flow.py       # FSM Reading сценарий
    test_writing_flow.py       # FSM Writing сценарий
    test_speaking_webapp.py    # Playwright: Speaking Web App
  conftest.py
```

---

## 18. Фазы разработки

### Фаза 1 — Core (MVP)
- [ ] Проект-структура, .env, config, DB setup + Alembic
- [ ] /start, главное меню, настройки
- [ ] Writing Task 2 (самое простое для AI-оценки)
- [ ] Базовый прогресс пользователя

### Фаза 2 — Reading
- [ ] Контент-генерация текстов Academic/General
- [ ] FSM Reading с поддержкой T/F/NG и MC
- [ ] Оценка, разбор ошибок

### Фаза 3 — Listening
- [ ] TTS pipeline (скрипт → аудио)
- [ ] FSM Listening с разными типами вопросов
- [ ] Оценка

### Фаза 4 — Speaking Web App
- [ ] FastAPI speaking server
- [ ] Web App SPA (Vanilla JS, WebRTC)
- [ ] Gemini audio assessment
- [ ] Интеграция с ботом

### Фаза 5 — Polish
- [ ] Mock Test mode (все 4 секции)
- [ ] Streak + ачивки
- [ ] Daily tasks scheduler
- [ ] Writing Task 1 (с описанием графиков)
- [ ] Полное покрытие тестами
- [ ] Оптимизация промптов

---

## 19. Открытые вопросы (для обсуждения)

1. **Webhook vs Polling** для бота? (Webhook рекомендуется для продакшена)
2. **Порт для FastAPI**: 8004 свободен? Проверить конфликты
3. **TTS провайдер**: Google Cloud TTS (лучше качество) vs OpenAI TTS (уже настроен)?
4. **Writing Task 1 Academic**: присылать графики изображениями (AI-генерация картинок?) или только текстовое описание?
5. **Платёжная модель**: бесплатно vs freemium (X тестов в день, потом подписка)?
6. **Celery vs asyncio tasks** для фоновой генерации контента?
7. **Язык Web App**: отдельный репо или встроен в ielts2_bot/webapp/?
