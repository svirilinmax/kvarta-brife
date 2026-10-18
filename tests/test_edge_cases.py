"""Тесты на граничные случаи: 415, 500, health с ошибкой БД, rate limit, LeadIn edge cases."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import api.index as index_module
from api.models import Lead
from api.schemas import LeadIn

# ---------- API edge cases ----------


@pytest.mark.asyncio
async def test_lead_unsupported_media_type(test_client):
    """Content-Type не JSON и не form → 415."""
    resp = await test_client.post(
        "/api/lead",
        content="name=test",
        headers={"content-type": "text/plain"},
    )
    assert resp.status_code == 415
    assert resp.json()["status"] == "error"


@pytest.mark.asyncio
async def test_lead_server_error(test_client, monkeypatch):
    """create_lead бросает → 500 с fallback-телефоном."""

    async def boom(**kwargs):
        raise RuntimeError("DB down")

    monkeypatch.setattr(index_module, "create_lead", boom)

    payload = {"name": "Анна", "phone": "+375291234567", "interest": "order"}
    resp = await test_client.post("/api/lead", json=payload)

    assert resp.status_code == 500
    body = resp.json()
    assert body["status"] == "error"
    assert "Позвоните нам" in body["message"]


@pytest.mark.asyncio
async def test_health_db_error(test_client, monkeypatch):
    """Если SELECT 1 падает — health отвечает 200, но db=error."""

    async def broken_execute(self, *args, **kwargs):
        raise RuntimeError("DB is down")

    monkeypatch.setattr(AsyncSession, "execute", broken_execute)

    resp = await test_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "error"


@pytest.mark.asyncio
async def test_lead_no_forwarded_header(test_client, test_session):
    """Без X-Forwarded-For — IP берётся из request.client."""
    payload = {"name": "Анна", "phone": "+375291111222", "interest": "order"}
    resp = await test_client.post("/api/lead", json=payload)
    assert resp.status_code == 200

    lead = (await test_session.execute(select(Lead))).scalars().first()
    assert lead is not None
    assert lead.ip_address


@pytest.mark.asyncio
async def test_rate_limit_429(test_client, override_settings):
    """Лимит из env — ставим 2, третья заявка → 429."""
    override_settings(RATE_LIMIT_MAX=2)

    payloads = [
        {"name": "Анна", "phone": "+375291000001", "interest": "order"},
        {"name": "Борис", "phone": "+375291000002", "interest": "order"},
        {"name": "Вера", "phone": "+375291000003", "interest": "order"},
    ]
    for p in payloads[:2]:
        r = await test_client.post("/api/lead", json=p)
        assert r.status_code == 200, r.text

    r3 = await test_client.post("/api/lead", json=payloads[2])
    assert r3.status_code == 429


# ---------- LeadIn edge cases ----------


def test_leadin_name_too_short():
    """Имя из 1 символа → ValidationError."""
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises(PydanticValidationError):
        LeadIn(name="A", phone="+375291234567", interest="order")


def test_leadin_strip_optional_empty():
    """Пустые строки в optional-полях → None."""
    lead = LeadIn(
        name="Анна",
        phone="+375291234567",
        interest="order",
        comment="   ",
        utm_source="",
    )
    assert lead.comment is None
    assert lead.utm_source is None


@pytest.mark.asyncio
async def test_lead_form_data_with_prefix(test_client, test_session):
    """Fallback без JS: телефон приходит без 375, склеивается через phone_prefix."""
    resp = await test_client.post(
        "/api/lead",
        data={
            "name": "Анна",
            "phone": "291234567",  # без 375
            "phone_prefix": "375",  # скрытое поле
            "interest": "order",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    lead = (await test_session.execute(select(Lead))).scalars().first()
    assert lead.phone == "375291234567"
