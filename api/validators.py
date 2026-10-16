import re

PHONE_RE = re.compile(r"^375\d{9}$")

PHONE_ERROR = "Введите белорусский номер в формате +375 (29) 123-45-67"


def normalize_phone(raw: str) -> str:
    """Убирает всё, кроме цифр. '80...' → '375...'."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("80"):
        digits = "375" + digits[2:]
    return digits


def validate_phone(raw: str) -> str:
    """Возвращает нормализованный номер или бросает ValueError."""
    normalized = normalize_phone(raw)
    if not PHONE_RE.match(normalized):
        raise ValueError(PHONE_ERROR)
    return normalized


def sanitize_text(value: str | None, max_len: int) -> str | None:
    """Strip + обрезка по длине. None остаётся None."""
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_len]
