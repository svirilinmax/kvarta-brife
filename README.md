
# Кварта — лендинг обжарки кофе

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?logo=vercel)](https://vercel.com/)
[![Lighthouse](https://img.shields.io/badge/Lighthouse-100%2F100%2F100%2F100-brightgreen)](https://developers.google.com/web/tools/lighthouse)

Мастерская обжарки в Минске. Лендинг с формой заявки: клиент оставляет номер — менеджер перезванивает. Без корзины и оплаты.

**🔗 Живой сайт:** [https://kvarta-brife.vercel.app/](https://kvarta-brife.vercel.app/)

---

## Стек и почему
- **FastAPI**: минимальный бэкенд для одного эндпоинта, автодокументация Swagger.
- **Supabase**: managed Postgres. Использую Transaction Pooler (порт 6543), чтобы не исчерпать лимит соединений на serverless.
- **Vercel**: CDN для статики + бесплатные serverless-функции.
- **Alembic**: миграции в коде.
- **Статика (HTML/CSS/JS)**: без фреймворков, каждый килобайт на счету.

*Альтернативы:* SQLite не подошёл (эфемтерная ФС на Vercel), Netlify не поддерживает Python из коробки.

---

## Локальный запуск

```bash
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env  # Заполнить DATABASE_URL и DIRECT_URL
    alembic upgrade head
    uvicorn api.index:app --reload
```
**Тесты:** `pytest -v` (38 тестов, покрытие 90%).

---

## Решения, которые принимал сам (и почему)

1. **Два URL для БД:** `DATABASE_URL` (pooler, 6543) для приложения, `DIRECT_URL` (5432) только для Alembic. На serverless прямое подключение быстро исчерпывает лимиты.
2. **Prepared statements:** параметр `?prepared_statement_cache_size=0` в URL не работает в SQLAlchemy. Вынес в `connect_args={"statement_cache_size": 0}`.
3. **Дедупликация:** `pg_advisory_xact_lock(hashtext(phone))`. Блокирует транзакцию по хэшу телефона, защищает от двойных кликов.
4. **Rate limit:** считается в Python (`datetime.now() - 60 min`), а не в SQL. Это позволило тестировать на SQLite без моков.
5. **Дизайн:** тёплый минимализм без «премиального глянца». Убрал градиенты, скругления 12px, стоковые улыбки.

---

## Где ИИ ошибся (и как исправил)

| Что предложил ИИ | Проблема | Решение |
|---|---|---|
| `runtime: "python3.12.7"` в `vercel.json` | Vercel принимает только мажор.минор | Вернул `python3.12` |
| `?prepared_statement_cache_size=0` в URL | SQLAlchemy не пробрасывает в asyncpg | Перенёс в `connect_args` |
| `sa.UUID()` без `server_default` | Alembic не подхватывает `default=uuid4`, INSERT падал | Добавил `DEFAULT gen_random_uuid()` |
| `BigInteger` для `rate_limits.id` | На SQLite не работает autoincrement | `.with_variant(Integer, "sqlite")` |
| «Премиальный» дизайн | Не соответствует ТЗ («тёплый, простой») | Переписал CSS, убрал градиенты |
| `+7` в тестах телефона | Не белорусский номер | Заменил на `+375` |
| `rewrites` в `vercel.json` | Vercel переписывал `/api/lead`, FastAPI отдавал 404 | Удалил rewrites |
| `root_path="/api"` в FastAPI | Сбил маршрутизацию | Убрал `root_path` |

**Главный урок:** ИИ генерирует «средний» код. Специфику serverless (pooler, rewrites) нужно проверять руками и читать логи Vercel.

---

## Что не успел / сделал бы иначе
- **Не сделал:** Telegram-бот для заявок, Sentry, E2E-тесты.
- **Сделал бы иначе:** rate limit вынес бы в Redis (дешевле, чем COUNT в Postgres). Добавил бы динамическую OG-картинку.

---

## Контакты

Проект разработан в рамках тестового задания.

- **Telegram**: [@svirilinmax](https://t.me/svirilinmax)
- **Email**: [svirilin.work@mail.ru](mailto:svirilin.work@mail.ru)

---

## Лицензия

Этот проект лицензирован под лицензией MIT - см. файл [LICENSE](LICENSE).