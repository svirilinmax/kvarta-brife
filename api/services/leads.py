from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Lead, RateLimit
from api.schemas import LeadIn
from api.settings import get_settings
from api.validators import normalize_phone, sanitize_text

DUPLICATE_MESSAGE = "Заявка уже принята, мы свяжемся"
SUCCESS_MESSAGE = "Заявка принята"


async def _acquire_phone_lock(session: AsyncSession, phone: str) -> None:
    """Postgres-only advisory lock. На других диалектах — no-op."""
    dialect = session.bind.dialect.name if session.bind else "unknown"
    if dialect == "postgresql":
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:phone))"),
            {"phone": phone},
        )


async def create_lead(
    session: AsyncSession,
    data: LeadIn,
    ip: str,
    user_agent: str,
) -> dict:
    settings = get_settings()
    phone = normalize_phone(data.phone)

    # Защита от гонки при двойном клике (Postgres-only)
    await _acquire_phone_lock(session, phone)

    # Проверка дубля — окно из настроек, считаем время в Python
    cutoff = datetime.now(UTC) - timedelta(minutes=settings.duplicate_window_minutes)
    dup_stmt = select(Lead.id).where(Lead.phone == phone).where(Lead.created_at > cutoff).limit(1)
    dup_result = await session.execute(dup_stmt)
    if dup_result.first() is not None:
        await session.rollback()
        return {"status": "duplicate", "message": DUPLICATE_MESSAGE}

    # INSERT через ORM
    lead = Lead(
        name=data.name,
        phone=phone,
        interest=data.interest,
        comment=sanitize_text(data.comment, 500),
        utm_source=sanitize_text(data.utm_source, 255),
        utm_medium=sanitize_text(data.utm_medium, 255),
        utm_campaign=sanitize_text(data.utm_campaign, 255),
        utm_content=sanitize_text(data.utm_content, 255),
        utm_term=sanitize_text(data.utm_term, 255),
        referrer=sanitize_text(data.referrer, 2048),
        landing_page=sanitize_text(data.landing_page, 2048),
        user_agent=sanitize_text(user_agent, 1024),
        ip_address=ip,
    )
    session.add(lead)

    # Учёт rate limit
    session.add(RateLimit(ip_address=ip))

    await session.commit()
    return {"status": "ok", "message": SUCCESS_MESSAGE}
