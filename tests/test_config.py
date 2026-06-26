"""Tests for the application settings and field validators."""

import os

import pytest


def test_default_settings_are_valid() -> None:
    from app.config import settings

    assert settings.app_name
    assert settings.app_version
    assert 0.0 <= settings.tax_rate <= 1.0
    assert settings.rate_limit > 0
    assert settings.window_seconds > 0


def test_tax_rate_bounds_accept_zero(monkeypatch) -> None:
    monkeypatch.setenv("TAX_RATE", "0.0")
    from importlib import reload

    import app.config as cfg

    reload(cfg)
    assert cfg.Settings().tax_rate == 0.0


def test_tax_rate_bounds_accept_one(monkeypatch) -> None:
    monkeypatch.setenv("TAX_RATE", "1.0")
    from app.config import Settings

    s = Settings()
    assert s.tax_rate == 1.0


def test_tax_rate_rejects_negative() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(tax_rate=-0.01)


def test_tax_rate_rejects_above_one() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(tax_rate=1.01)


def test_log_level_uppercased(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")
    from app.config import Settings

    s = Settings()
    assert s.log_level == "DEBUG"


def test_log_level_rejects_invalid() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(log_level="TRACE")


def test_rate_limit_and_window_defaults() -> None:
    from app.config import settings

    assert isinstance(settings.rate_limit, int)
    assert isinstance(settings.window_seconds, int)
