from typing import Literal

from pydantic import BaseModel, Field, field_validator

from api.validators import PHONE_ERROR, PHONE_RE, normalize_phone

InterestType = Literal["subscription", "order", "question"]


class LeadIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=25)
    interest: InterestType
    comment: str | None = Field(None, max_length=500)

    utm_source: str | None = Field(None, max_length=255)
    utm_medium: str | None = Field(None, max_length=255)
    utm_campaign: str | None = Field(None, max_length=255)
    utm_content: str | None = Field(None, max_length=255)
    utm_term: str | None = Field(None, max_length=255)
    referrer: str | None = Field(None, max_length=2048)
    landing_page: str | None = Field(None, max_length=2048)

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Имя должно быть не короче 2 символов")
        return v

    @field_validator("phone")
    @classmethod
    def phone_check(cls, v: str) -> str:
        normalized = normalize_phone(v)
        if not PHONE_RE.match(normalized):
            raise ValueError(PHONE_ERROR)
        return v

    @field_validator(
        "comment",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "referrer",
        "landing_page",
        mode="before",
    )
    @classmethod
    def strip_optional(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        return v


class LeadOut(BaseModel):
    status: str
    message: str


class ErrorOut(BaseModel):
    status: str
    message: str
    errors: dict | None = None


class HealthOut(BaseModel):
    status: str
    db: str
    version: str
