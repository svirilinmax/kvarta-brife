import pytest
from freezegun import freeze_time
from sqlalchemy import func, select

from api.models import Lead
from api.schemas import LeadIn
from api.services.leads import DUPLICATE_MESSAGE, create_lead


def make_lead_data(phone: str = "+375291234567") -> LeadIn:
    return LeadIn(name="Анна", phone=phone, interest="subscription")


@pytest.mark.asyncio
async def test_first_lead_saved(test_session):
    result = await create_lead(
        session=test_session,
        data=make_lead_data(),
        ip="127.0.0.1",
        user_agent="pytest",
    )
    assert result["status"] == "ok"

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_duplicate_within_10_min(test_session):
    with freeze_time("2026-01-01 12:00:00"):
        r1 = await create_lead(test_session, make_lead_data(), "127.0.0.1", "pytest")
        assert r1["status"] == "ok"

    with freeze_time("2026-01-01 12:05:00"):
        r2 = await create_lead(test_session, make_lead_data(), "127.0.0.1", "pytest")
        assert r2["status"] == "duplicate"
        assert r2["message"] == DUPLICATE_MESSAGE

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_new_lead_after_10_min(test_session):
    with freeze_time("2026-01-01 12:00:00"):
        await create_lead(test_session, make_lead_data(), "127.0.0.1", "pytest")

    with freeze_time("2026-01-01 12:15:00"):
        r2 = await create_lead(test_session, make_lead_data(), "127.0.0.1", "pytest")
        assert r2["status"] == "ok"

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 2


@pytest.mark.asyncio
async def test_different_phone_not_duplicate(test_session):
    await create_lead(test_session, make_lead_data("+375291234567"), "127.0.0.1", "pytest")
    r2 = await create_lead(test_session, make_lead_data("+375291111111"), "127.0.0.1", "pytest")
    assert r2["status"] == "ok"

    count = (await test_session.execute(select(func.count(Lead.id)))).scalar()
    assert count == 2
