from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.database import get_session
from api.index import app
from api.models import Base
from api.settings import get_settings


@pytest_asyncio.fixture(autouse=True)
def _clear_settings_cache():
    """Сбрасываем lru_cache, чтобы monkeypatch/env не протекали между тестами."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def override_settings(monkeypatch):
    """Хелпер: override_settings(RATE_LIMIT_MAX=2) меняет env и сбрасывает кэш."""

    def _override(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key.upper(), str(value))
        get_settings.cache_clear()
        return get_settings()

    return _override


@pytest_asyncio.fixture
async def test_engine():
    # StaticPool — критично для SQLite :memory:, чтобы все соединения видели одну БД
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
