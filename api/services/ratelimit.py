from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import RateLimit
from api.settings import get_settings


async def check_rate_limit(
    session: AsyncSession,
    ip: str,
    limit: int | None = None,
    window_minutes: int | None = None,
) -> bool:
    """True — можно, False — превышен лимит.

    limit/window_minutes можно передать явно (для тестов),
    иначе берутся из настроек.
    """
    settings = get_settings()
    limit = limit if limit is not None else settings.rate_limit_max
    window_minutes = (
        window_minutes if window_minutes is not None else settings.rate_limit_window_minutes
    )

    cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
    stmt = (
        select(func.count(RateLimit.id))
        .where(RateLimit.ip_address == ip)
        .where(RateLimit.created_at > cutoff)
    )
    result = await session.execute(stmt)
    count = result.scalar() or 0
    return count < limit
