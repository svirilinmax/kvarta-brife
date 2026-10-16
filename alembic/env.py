import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Добавляем корень проекта в sys.path, чтобы импортировать api.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.models import Base  # noqa: E402
from api.settings import get_settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
url = settings.direct_url or settings.database_url
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме."""
    # Используем асинхронный URL напрямую
    url = settings.direct_url or settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Синхронный контекст внутри асинхронного соединения."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()



async def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме (асинхронно)."""
    # Создаем асинхронный движок на основе оригинального URL из .env
    connectable = create_async_engine(
        settings.direct_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # run_sync выполняет синхронную функцию do_run_migrations в асинхронной среде
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запускаем асинхронную функцию через asyncio loop
    asyncio.run(run_migrations_online())
