import pytest

from api.validators import PHONE_ERROR, normalize_phone, sanitize_text, validate_phone


class TestNormalizePhone:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("+375291234567", "375291234567"),
            ("375291234567", "375291234567"),
            ("+375 (29) 123-45-67", "375291234567"),
            ("80291234567", "375291234567"),
            ("  +375 29 123 45 67  ", "375291234567"),
            ("+375-29-123-45-67", "375291234567"),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_phone(raw) == expected


class TestValidatePhone:
    @pytest.mark.parametrize(
        "raw",
        [
            "+375291234567",
            "375291234567",
            "+375 (29) 123-45-67",
            "80291234567",
        ],
    )
    def test_valid(self, raw):
        assert validate_phone(raw) == "375291234567"

    @pytest.mark.parametrize(
        "raw",
        [
            "+7 999 123-45-67",
            "123",
            "",
            "abc",
            "+37529123456",  # 11 цифр
            "+3752912345678",  # 13 цифр
            "3751234567890",  # не 375
        ],
    )
    def test_invalid(self, raw):
        with pytest.raises(ValueError) as exc:
            validate_phone(raw)
        assert PHONE_ERROR in str(exc.value)


class TestSanitizeText:
    def test_none(self):
        assert sanitize_text(None, 100) is None

    def test_empty(self):
        assert sanitize_text("   ", 100) is None

    def test_strip(self):
        assert sanitize_text("  hello  ", 100) == "hello"

    def test_truncate(self):
        assert sanitize_text("a" * 200, 10) == "a" * 10
