from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import LeadIn
from api.services.ratelimit import record_rate_limit
from api.validators import normalize_phone, sanitize_text

DUPLICATE_MESSAGE = "Заявка уже принята, мы свяжемся"
SUCCESS_MESSAGE = "Заявка принята"


async def create_lead(
    session: AsyncSession,
    data: LeadIn,
    ip: str,
    user_agent: str,
) -> dict:
    phone = normalize_phone(data.phone)

    # Advisory lock по номеру — закрывает гонку при двойном клике
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:phone))"),
        {"phone": phone},
    )

    # Проверка дубля в окне 10 минут
    dup = await session.execute(
        text(
            "SELECT 1 FROM leads "
            "WHERE phone = :phone "
            "AND created_at > NOW() - INTERVAL '10 minutes' "
            "LIMIT 1"
        ),
        {"phone": phone},
    )
    if dup.first() is not None:
        await session.rollback()
        return {"status": "duplicate", "message": DUPLICATE_MESSAGE}

    # INSERT заявки
    await session.execute(
        text(
            """
            INSERT INTO leads (
                name, phone, interest, comment,
                utm_source, utm_medium, utm_campaign, utm_content, utm_term,
                referrer, landing_page, user_agent, ip_address
            ) VALUES (
                :name, :phone, :interest, :comment,
                :utm_source, :utm_medium, :utm_campaign, :utm_content, :utm_term,
                :referrer, :landing_page, :user_agent, :ip
            )
            """
        ),
        {
            "name": data.name,
            "phone": phone,
            "interest": data.interest,
            "comment": sanitize_text(data.comment, 500),
            "utm_source": sanitize_text(data.utm_source, 255),
            "utm_medium": sanitize_text(data.utm_medium, 255),
            "utm_campaign": sanitize_text(data.utm_campaign, 255),
            "utm_content": sanitize_text(data.utm_content, 255),
            "utm_term": sanitize_text(data.utm_term, 255),
            "referrer": sanitize_text(data.referrer, 2048),
            "landing_page": sanitize_text(data.landing_page, 2048),
            "user_agent": sanitize_text(user_agent, 1024),
            "ip": ip,
        },
    )

    await record_rate_limit(session, ip)
    await session.commit()
    return {"status": "ok", "message": SUCCESS_MESSAGE}
