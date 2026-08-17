from __future__ import annotations

from fastapi.testclient import TestClient

from flowstock_api.config import Settings
from flowstock_api.main import create_app


class StubProbe:
    def __init__(self, ready: bool) -> None:
        self.ready = ready
        self.closed = False

    def is_ready(self) -> bool:
        return self.ready

    def close(self) -> None:
        self.closed = True


def make_app(*, ready: bool = True):
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://flowstock:test@localhost/flowstock_test",
        )
    )
    app.state.database_probe = StubProbe(ready)
    return app


def test_liveness_has_correlation_and_security_headers() -> None:
    with TestClient(make_app()) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"api": "ok"}}
    assert response.headers["x-correlation-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_safe_incoming_correlation_id_is_preserved() -> None:
    with TestClient(make_app()) as client:
        response = client.get(
            "/api/v1/health/live",
            headers={"X-Correlation-ID": "acceptance-run-001"},
        )

    assert response.headers["x-correlation-id"] == "acceptance-run-001"


def test_invalid_incoming_correlation_id_is_replaced() -> None:
    with TestClient(make_app()) as client:
        response = client.get(
            "/api/v1/health/live",
            headers={"X-Correlation-ID": "unsafe value with spaces"},
        )

    assert response.headers["x-correlation-id"] != "unsafe value with spaces"


def test_readiness_reports_database_failure_without_sensitive_details() -> None:
    with TestClient(make_app(ready=False)) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "failed"},
    }
    assert "postgresql" not in response.text


def test_metrics_are_exposed() -> None:
    with TestClient(make_app()) as client:
        client.get("/api/v1/health/live")
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "flowstock_http_requests_total" in response.text
