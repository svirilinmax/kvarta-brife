### Коммит 1. `init: project structure, configs, env example`

```
Ты — опытный Python-разработчик. Помоги настроить структуру проекта для лендинга обжарки кофе «Кварта».

Стек: FastAPI + Supabase (PostgreSQL) + Vercel (serverless). Python 3.12. Фронт — чистая статика (HTML/CSS/JS), без Jinja2.

Создай:
1. Структуру папок:
   - api/ (index.py, database.py, models.py, schemas.py, validators.py, settings.py, services/)
   - public/ (index.html, style.css, script.js, img/)
   - alembic/ (versions/)
   - tests/ (conftest.py, test_validators.py, test_dedup.py, test_api.py)
   - docs/ (ai-log.md)
   - .github/workflows/ (lint.yml)

2. Файл requirements.txt с версиями:
   fastapi, uvicorn, mangum, sqlalchemy[asyncio], asyncpg, alembic, pydantic, pydantic-settings, python-dotenv, pytest, pytest-asyncio, httpx, ruff, black, psycopg2-binary (для alembic)

3. Файл .python-version с "3.12"

4. Файл .gitignore для Python + .env + .vercel + __pycache__ + .pytest_cache

5. Файл .env.example:
   DATABASE_URL=postgresql+asyncpg://postgres.[project]:[password]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?prepared_statement_cache_size=0
   ENVIRONMENT=development

6. Файл vercel.json:
   - functions: api/index.py, runtime python3.12, maxDuration 10
   - rewrites: /api/(.*) → /api/index.py

7. Файл pyproject.toml с конфигом ruff (line-length 100, target py312) и black (line-length 100)

8. Пустые __init__.py в api/ и api/services/

9. README.md с заголовком «Кварта — лендинг обжарки кофе» и заглушками разделов: Стек, Локальный запуск, Деплой, Что делал сам vs ИИ, Что не успел.

Не пиши логику приложения — только структура и конфиги. Дай команды для создания venv и установки зависимостей.
```

**Проверь:** структура совпадает с ТЗ, `vercel.json` корректен, `.env.example` без реальных секретов.
**Результат:** структура папок, конфиги, requirements.txt
**Ошибки ИИ:** (не правильная версия в requirements.txt в ruff, в докере повторяющаяся инвормация)
**Что исправил:** — gitignor requirements.txt
| Шаг | Что предложил ИИ | В чём ошибка | Как исправил |
| 1 | runtime "python3.12" (я уточнил до 3.12.7) | Vercel не принимает патч-версию | Вернул python3.12 |

**Скриншот:** ![init](./screenshots/01-init.png)

## Шаг 2: Alembic + Supabase — настройка миграций

**Промпт:** [Коммит 2. `feat: supabase connection and alembic migration`

```
Контекст: FastAPI + Supabase (Postgres) + Vercel. Python 3.12. Проект «Кварта» — лендинг обжарки кофе с формой заявки.

Задача: настроить подключение к Supabase и первую миграцию Alembic.

Создай:

1. api/settings.py:
   - класс Settings(BaseSettings) из pydantic-settings
   - поля: database_url: str, environment: str = "development"
   - чтение из .env
   - синглтон get_settings() с @lru_cache

2. api/database.py:
   - create_async_engine с database_url
   - async_sessionmaker (expire_on_commit=False)
   - зависимость get_session() для FastAPI (async generator)
   - функция init_db() — заглушка, не нужна (миграции через Alembic)

3. api/models.py:
   - Base = declarative_base()
   - Модель Lead:
     - id: UUID, primary_key, default=uuid4
     - name: str, not null
     - phone: str, not null, index
     - interest: str, not null
     - comment: str, nullable
     - utm_source, utm_medium, utm_campaign, utm_content, utm_term: str, nullable
     - referrer: str, nullable
     - landing_page: str, nullable
     - user_agent: str, nullable
     - ip_address: str, nullable
     - created_at: DateTime(timezone=True), server_default=func.now()
   - Модель RateLimit:
     - id: BigInteger, primary_key, autoincrement
     - ip_address: str, not null, index
     - created_at: DateTime(timezone=True), server_default=func.now()

4. alembic.ini — стандартный, но sqlalchemy.url оставь пустым (берём из env)

5. alembic/env.py:
   - синхронный движок для миграций (psycopg2), берёт URL из settings, заменяет asyncpg на psycopg2
   - target_metadata = Base.metadata
   - поддержка offline и online режимов

6. alembic/versions/0001_init.py — миграция:
   - CREATE EXTENSION IF NOT EXISTS pgcrypto
   - create_table leads со всеми полями
   - create_table rate_limits
   - индексы: idx_leads_phone_created (phone, created_at DESC), idx_rate_limits_ip_created (ip_address, created_at DESC)
   - downgrade: drop обеих таблиц

Дай команды: alembic init (если нужно), alembic revision, alembic upgrade head.
У меня есть `settings.py` (pydantic-settings) и `env.py` для Alembic. Нужно настроить асинхронные миграции в Supabase. Проверь конфиги и исправь ошибки при `alembic revision --autogenerate`».

Не пиши API-роуты и валидацию — только подключение, модели, миграцию.
```

**Результат (что предложил ИИ):**
- переписанный `alembic/env.py` с `asyncio.run(...)` и `run_sync(do_run_migrations)`
- `Settings` с полями `database_url`, `direct_url`, `environment`
- разделение URL на transaction pooler (6543) и session pooler (5432)
- рекомендация использовать `DIRECT_URL` для миграций, а `DATABASE_URL` — для приложения

**Что сделал сам:**
- установил `asyncpg` в venv
- добавил `DIRECT_URL` в `.env`
- через панель Supabase (Connect → Direct → Session pooler) скопировал реальную строку подключения
- прогнал `python -c "from api.settings import get_settings; ..."` для проверки, что URL читается корректно

**Ошибки ИИ / несоответствия:**
1. **Битый хардкод URL в `env.py`:**
   ```python
   direct_url = "postgresql+asyncpg://postgres...:VY8...@://supabase.com"
**Скриншот:** ![init](./screenshots/02-feat.png)
## Шаг 2.1: правки после ревью

**Ошибки, которые нашёл сам при проверке:**
- Alembic брал `database_url` (pooler :6543) вместо `direct_url` (:5432) — миграция прошла, но неоптимально
- Дубли индексов из-за `index=True` + `Index(...)` в моделях
- Лишние SUPABASE_* переменные в .env

**Исправил:** env.py → direct_url, модели → убрал index=True, миграция → убрал 2 индекса, .env → почистил
**Скриншот:** ![init](./screenshots/02.1-fix.png)

## Шаг 3: API-эндпоинт (validators, schemas, services, index)

**Промпт:** [твой запрос]

**Результат:** 5 файлов — validators.py, schemas.py, services/ratelimit.py, services/leads.py, index.py

**Что тестировал:** health, успешная заявка, дубль, невалидный телефон, honeypot, rate limit.

### Ошибки ИИ и итерации

| # | Что было | Как исправил |
|---|----------|--------------|
| 1 | `?prepared_statement_cache_size=0` в URL не работает — SQLAlchemy не пробрасывает параметр в asyncpg | Перенёс в `connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0}` в `create_async_engine` |
| 2 | Колонка `leads.id` создана без `server_default` — Alembic autogenerate не подхватывает Python-side `default=uuid4` | Новая миграция `ALTER TABLE leads ALTER COLUMN id SET DEFAULT gen_random_uuid()`, плюс `server_default` в модели |

**Скриншоты:** ![init](./screenshots/03-feat.png), ![dedup](./screenshots/03.1-feat.png)

## Шаг 4: тесты pytest

**Промпт:** «Сделай шаг 4 с учётом env-констант»

**Результат:** 38 passed, coverage 90% (`pytest --cov --cov-report=term-missing`).

### Что было сломано и как починил (ошибки ИИ в плане шага 4)

| Проблема | Причина | Решение |
|---|---|---|
| `ModuleNotFoundError: No module named 'api'` | pytest не видел корень проекта | `pythonpath = ["."]` в `pyproject.toml` |
| `near "(": syntax error` в `CREATE TABLE leads` | `PGUUID` + `gen_random_uuid()` — Postgres-only | `Uuid(as_uuid=True)` из `sqlalchemy`, Python-side `default=uuid4` |
| `NOT NULL constraint failed: rate_limits.id` | `BigInteger + autoincrement` не работает на SQLite | `BigInteger().with_variant(Integer, "sqlite")` |
| `asyncio_default_fixture_loop_scope` warning | pytest-asyncio 0.24 требует явного значения | `asyncio_default_fixture_loop_scope = "function"` |
| `fixture 'override_settings' not found` | забыл добавить фикстуру в `conftest.py` | добавил `override_settings` рядом с `_clear_settings_cache` |
| `AssertionError: python-multipart must be installed` | форма с `request.form()` не работает без библиотеки | добавил `python-multipart==0.0.20` в `requirements.txt` |
| `ruff failed: Unknown rule selector B0008` | `B0008` — устаревшее правило из старого `flake8-bugbear` | удалил из `ignore`, добавил `B008` (FastAPI `Depends`) |
| `UP017: Use datetime.UTC alias` | `timezone.utc` — устаревший синтаксис (Python 3.11+) | автофикс через `ruff check --fix .` |
| `I001: Import block is un-sorted` | импорты не по алфавиту | автофикс через `ruff check --fix .` |

### Ошибки ИИ, которые заметил сам

- DeepSeek предложил `PGUUID` — Postgres-only, ломает SQLite-тесты.
- DeepSeek предложил `BigInteger + autoincrement=True` — на SQLite `BIGINT PRIMARY KEY` не rowid-alias, autoincrement не работает.
- DeepSeek не предупредил про `@lru_cache` на `get_settings()` и `cache_clear()` в тестах.
- DeepSeek не упомянул `aiosqlite` в исходном `requirements.txt` — async-тесты на SQLite падали бы.
- DeepSeek не упомянул `python-multipart` — fallback-форма (без JS) падала бы на проде с `AssertionError`.
- DeepSeek сгенерировал `pyproject.toml` с несуществующим правилом `B0008` в `ignore`.
- DeepSeek использовал устаревший `timezone.utc` вместо `UTC`.

### Что понял

- **Тесты на SQLite — лакмус на диалект-зависимость моделей.** «Работает на Postgres» ≠ «переносимо». `with_variant` + Python-side defaults — стандарт для кроссплатформенных моделей.
- **`python-multipart` нужен не только для файлов.** Обычная HTML-форма (`application/x-www-form-urlencoded`) с `request.form()` без него падает. На фронте fallback без JS не работал бы — поймал тестом `test_lead_form_data`.
- **`coverage` врёт с `monkeypatch`.** Тесты на 429/500 зелёные, но строки показываются как непокрытые. Это баг `coverage.py`, не тестов.
- **`@lru_cache` на `get_settings()`** требует `cache_clear()` в тестах, иначе `monkeypatch.setenv` не работает.

### Осознанно не покрыто (90% — это норма)

- `database.py:get_session` (54%) — подменяется через `dependency_overrides`. Rollback проверяется косвенно через `test_lead_server_error`.
- `leads.py:_acquire_phone_lock` (96%) — Postgres-only advisory lock. На SQLite no-op by design.
- `index.py:get_client_ip` fallback `"0.0.0.0"` (67%) — требует мока `request.client = None`.

### Финальный прогон

**Скриншоты:** ![init](./screenshots/04-test.png), ![dedup](./screenshots/05-test.png), ![dedup](./screenshots/06-test.png)

## Шаг 5: фронтенд — структура, дизайн, логика

**Промпт:** «Сделай шаг 5 фронтенд: HTML/CSS/JS для лендинга обжарки кофе».
Затем попросил добавить маску телефона, кнопки «Наверх», «Очистить», передачу продукта в комментарий и prefill для «Задать вопрос».

**Результат:** Полноценный лендинг со всеми блоками (Hero, О мастерской, Свежесть, Ассортимент, Подписка, Доставка, Форма, Footer).

**Что было реализовано:**
- Тёплый минимализм (палитра `--ink`, `--paper`, `--accent`), без градиентов и скруглений, как в референсах (Tim Wendelboe, Coffee Collective).
- **JS-маска телефона:** фиксированный префикс `🇧🇾 +375`, автоформатирование в `(XX) XXX-XX-XX`, сдвиг курсора при удалении.
- **Умные CTA:** при клике на «Заказать» (Эфиопия) селект ставит `order`, а в комментарий пишется «Эфиопия Иргачеффе». «Оформить подписку» → `subscription` + «Подписка». «Задать вопрос» → `question`.
- **Кнопка «Наверх»:** плавающая, появляется при скролле > 400px.
- **Кнопка «Очистить»:** сбрасывает форму и убирает ошибки.
- **Fallback без JS:** если JS отключен, скрытое поле `phone_prefix` (375) склеивается с введённым номером на бэкенде.

### Ошибки ИИ и итерации

| # | Проблема | Как исправил |
|---|----------|--------------|
| 1 | ИИ не передавал `data-product` в комментарий. Кнопка «Заказать» просто скроллила к форме, и менеджер не знал, какой кофе выбрали. | Добавил атрибуты `data-product` в HTML и логику в `bindCtaButtons()`. |
| 2 | Дизайн телефона был без флага и префикса. Пользователю пришлось бы вводить `+375` вручную. | Переделал на flex-контейнер с флагом, скрытым инпутом и JS-маской. |
| 3 | При отключенном JS бэкенд отклонял номер (422), так как `+375` терялся. | Добавил `phone_prefix` в HTML и склейку в `create_lead_endpoint`. |
| 4 | Кнопка «Задать вопрос» в Hero вела на форму, но не переключала селект на «Вопрос». | Добавил `data-interest="question"` на кнопку. |

**Скриншоты:** ![desktop](./screenshots/07-desktop.png), ![desktop](./screenshots/07.1-desktop.png), ![desktop](./screenshots/07.2-desktop.png), ![desktop](./screenshots/07.3-desktop.png), ![desktop](./screenshots/07.4-desktop.png), ![mobile](./screenshots/07-mobile.png), ![mobile](./screenshots/07.1-mobile.png), ![mobile](./screenshots/07.2-mobile.png), ![mobile](./screenshots/07.3-mobile.png)

## Шаг 6: Картинки и финальный дизайн

**Промпт:** «Как подобрать фото? Опиши для каждой картинки размер. Сделай так, чтобы отображалось.»

**Что сделал:**
- Подобрал 7 фотографий на Unsplash/Pexels по теме: обжарка, зёрна, процесс (без стоковых улыбок).
- Сжал их через Squoosh в формат WebP (качество 75–80), настроил точные размеры для каждого блока (чтобы не было сдвига макета).
- Добавил в HTML теги `<img>` с `alt`, `width`, `height`, `loading="lazy"` и `fetchpriority="high"` для главного экрана (важно для LCP).
- Добавил отдельную горизонтальную картинку `og-cover.jpg` (1200×630) для превью в соцсетях.
- Обновил CSS: добавил `object-fit: cover`, лёгкий zoom при наведении на карточки, сдержанную тень и акцентные линии для блока «Свежесть».

**Ошибки ИИ / Сложности:**
- ИИ в шаге 6 дал ссылки на Unsplash, но предупредил, что они могут меняться. Пришлось подбирать фото вручную на сайте, чтобы найти идеальные кадры (руки, ростер, зёрна).
- Сначала я хотел использовать горизонтальное фото на главный экран, но оно обрезалось. ИИ подсказал, что для Hero нужен вертикальный кадр, а для соцсетей — отдельный горизонтальный `og-cover.jpg`.

**Скриншоты:**
![desktop](./screenshots/08-desktop.png),
![desktop](./screenshots/08_1-desktop.png),
![mobile](./screenshots/08-mobile.png),
![lighthouse-mobile](./screenshots/lighthouse.png),
![lighthouse](./screenshots/lighthouse-pc.png),
