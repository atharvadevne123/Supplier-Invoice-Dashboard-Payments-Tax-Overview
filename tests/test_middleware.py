"""Tests for CorrelationIDMiddleware."""


def test_correlation_id_added_to_response(client) -> None:
    response = client.get("/api/v1/health")
    assert "X-Correlation-ID" in response.headers


def test_existing_correlation_id_echoed(client) -> None:
    custom_id = "test-correlation-xyz"
    response = client.get("/api/v1/health", headers={"X-Correlation-ID": custom_id})
    assert response.headers.get("X-Correlation-ID") == custom_id


def test_generated_correlation_id_is_hex(client) -> None:
    response = client.get("/api/v1/health")
    cid = response.headers.get("X-Correlation-ID", "")
    assert len(cid) == 32
    int(cid, 16)


def test_correlation_id_unique_per_request(client) -> None:
    r1 = client.get("/api/v1/health")
    r2 = client.get("/api/v1/health")
    assert r1.headers["X-Correlation-ID"] != r2.headers["X-Correlation-ID"]


def test_correlation_id_present_on_404(client) -> None:
    response = client.get("/api/v1/invoices/NONEXISTENT-INV")
    assert "X-Correlation-ID" in response.headers
