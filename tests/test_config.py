"""Tests for the application settings and field validators."""

import pytest


def test_default_settings_are_valid() -> None:
    from app.config import settings

    assert settings.app_name
    assert settings.app_version
    assert 0.0 <= settings.tax_rate <= 1.0
    assert settings.rate_limit > 0
    assert settings.window_seconds > 0


def test_tax_rate_bounds_accept_zero() -> None:
    from app.config import Settings

    s = Settings(TAX_RATE=0.0)
    assert s.tax_rate == 0.0


def test_tax_rate_bounds_accept_one() -> None:
    from app.config import Settings

    s = Settings(TAX_RATE=1.0)
    assert s.tax_rate == 1.0


def test_tax_rate_rejects_negative() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(TAX_RATE=-0.01)


def test_tax_rate_rejects_above_one() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(TAX_RATE=1.01)


def test_log_level_uppercased() -> None:
    from app.config import Settings

    s = Settings(LOG_LEVEL="debug")
    assert s.log_level == "DEBUG"


def test_log_level_rejects_invalid() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="TRACE")


def test_rate_limit_and_window_defaults() -> None:
    from app.config import settings

    assert isinstance(settings.rate_limit, int)
    assert isinstance(settings.window_seconds, int)
