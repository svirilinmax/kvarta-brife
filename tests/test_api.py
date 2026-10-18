import pytest
from sqlalchemy import func, select

from api.models import Lead


@pytest.mark.asyncio
async def test_health(test_client):
    resp = await test_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


@pytest.mark.asyncio
async def test_lead_success(test_client, test_session):
    payload = {
        "name": "Анна",
        "phone": "+375 (29) 123-45-67",
        "interest": "subscription",
        "comment": "Позвоните после 18:00",
    }
    resp = await test_client.post("/api/lead", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_lead_invalid_phone(test_client):
    payload = {"name": "Пётр", "phone": "+7 999 123-45-67", "interest": "order"}
    resp = await test_client.post("/api/lead", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert "errors" in body
    assert "phone" in body["errors"]


@pytest.mark.asyncio
async def test_lead_honeypot(test_client, test_session):
    payload = {
        "name": "Bot",
        "phone": "+375291119999",
        "interest": "order",
        "website": "spam",
    }
    resp = await test_client.post("/api/lead", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 0


@pytest.mark.asyncio
async def test_lead_duplicate(test_client, test_session):
    payload = {"name": "Анна", "phone": "+375291234567", "interest": "subscription"}
    r1 = await test_client.post("/api/lead", json=payload)
    assert r1.json()["status"] == "ok"

    r2 = await test_client.post("/api/lead", json=payload)
    assert r2.json()["status"] == "duplicate"

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 1
