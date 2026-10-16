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
   
**Скриншот:** !)



