import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session
from api.schemas import HealthOut, LeadIn, LeadOut
from api.services.leads import create_lead
from api.services.ratelimit import check_rate_limit
from api.settings import get_settings
from api.validators import PHONE_ERROR

settings = get_settings()

VERSION = "1.0"

app = FastAPI(title="Кварта API", version=VERSION)

logger = logging.getLogger("kvarta")
logger.setLevel(settings.log_level.upper())


# ---------- Helpers ----------


def get_client_ip(request: Request) -> str:
    """Vercel прокидывает реальный IP в X-Forwarded-For."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "0.0.0.0"


def _format_errors(exc: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc = err.get("loc", [])
        field = str(loc[-1]) if loc else "body"
        msg = err.get("msg", "Ошибка валидации")
        if field == "phone":
            msg = PHONE_ERROR
        errors[field] = msg
    return errors


# ---------- Routes ----------


@app.get("/api/health", response_model=HealthOut)
async def health(session: AsyncSession = Depends(get_session)):
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return HealthOut(status="ok", db=db_status, version=VERSION)


@app.post("/api/lead", response_model=LeadOut)
async def create_lead_endpoint(request: Request, session: AsyncSession = Depends(get_session)):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        payload = await request.json()
    elif (
        "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type
    ):
        form = await request.form()
        payload = dict(form)
        # Fallback без JS: склеиваем фиксированный префикс и введённый номер
        if "phone_prefix" in payload:
            prefix = str(payload.get("phone_prefix", "") or "")
            phone = str(payload.get("phone", "") or "")
            if prefix and phone:
                digits = "".join(ch for ch in phone if ch.isdigit())
                if not digits.startswith(prefix):
                    payload["phone"] = prefix + digits
                else:
                    payload["phone"] = digits
    else:
        return JSONResponse(
            status_code=415,
            content={"status": "error", "message": "Unsupported Media Type"},
        )

    # Honeypot
    if payload.get("website"):
        return LeadOut(status="ok", message="Заявка принята")

    # Валидация
    try:
        data = LeadIn(**payload)
    except ValidationError as e:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Проверьте поля",
                "errors": _format_errors(e),
            },
        )

    ip = get_client_ip(request)

    # Rate limit
    allowed = await check_rate_limit(session, ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "status": "error",
                "message": "Слишком много заявок. Попробуйте позже",
            },
        )

    # Создание
    try:
        result = await create_lead(
            session=session,
            data=data,
            ip=ip,
            user_agent=request.headers.get("user-agent", ""),
        )
        return LeadOut(**result)
    except Exception:
        await session.rollback()
        logger.exception("Failed to create lead")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Не удалось отправить. Позвоните нам: {settings.fallback_phone}",
            },
        )


# ---------- Vercel ----------

handler = Mangum(app, lifespan="off")
