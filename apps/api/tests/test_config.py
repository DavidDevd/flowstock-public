from __future__ import annotations

import pytest
from pydantic import ValidationError

from flowstock_api.config import Settings
from flowstock_api.modules.identity.contracts import SessionPolicy


def test_settings_require_postgresql() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite:///flowstock.db")


def test_pilot_disables_api_documentation() -> None:
    settings = Settings(
        environment="pilot",
        database_url="postgresql+psycopg://flowstock:test@postgres/flowstock",
    )
    assert settings.docs_enabled is False


def test_session_policy_matches_architecture_baseline() -> None:
    policy = SessionPolicy()
    assert policy.idle_timeout.total_seconds() == 15 * 60
    assert policy.absolute_lifetime.total_seconds() == 12 * 60 * 60
    assert policy.critical_operation_freshness.total_seconds() == 5 * 60
