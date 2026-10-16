from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

RATE_LIMIT_MAX = 5


async def check_rate_limit(session: AsyncSession, ip: str, limit: int = RATE_LIMIT_MAX) -> bool:
    """True — можно, False — превышен лимит."""
    result = await session.execute(
        text(
            "SELECT COUNT(*) FROM rate_limits "
            "WHERE ip_address = :ip "
            "AND created_at > NOW() - INTERVAL '1 hour'"
        ),
        {"ip": ip},
    )
    count = result.scalar() or 0
    return count < limit


async def record_rate_limit(session: AsyncSession, ip: str) -> None:
    await session.execute(
        text("INSERT INTO rate_limits (ip_address) VALUES (:ip)"),
        {"ip": ip},
    )
