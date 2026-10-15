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



