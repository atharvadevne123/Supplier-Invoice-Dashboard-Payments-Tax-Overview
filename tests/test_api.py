"""API integration tests for the Supplier Invoice Dashboard endpoints."""



def test_health_check(client) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["database"] == "connected"


def test_version_endpoint(client) -> None:
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    assert "version" in resp.json()


def test_list_invoices_empty(client) -> None:
    resp = client.get("/api/v1/invoices")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_create_invoice_success(client, sample_invoice_data) -> None:
    resp = client.post("/api/v1/invoices", json=sample_invoice_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["invoice_number"] == "INV-001"
    assert data["tax_amount"] is not None
    assert data["outstanding_amount"] is not None


def test_create_invoice_duplicate_conflict(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.post("/api/v1/invoices", json=sample_invoice_data)
    assert resp.status_code == 409


def test_get_invoice_not_found(client) -> None:
    resp = client.get("/api/v1/invoices/NONEXISTENT")
    assert resp.status_code == 404


def test_get_invoice_found(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.get("/api/v1/invoices/INV-001")
    assert resp.status_code == 200
    assert resp.json()["invoice_number"] == "INV-001"


def test_list_invoices_pagination(client) -> None:
    for i in range(5):
        data = {
            "invoice_number": f"INV-{i:03d}",
            "business_unit": "BU",
            "supplier": "Supplier",
            "invoice_date": "2025-01-01",
            "invoice_amount": "100.00",
            "amount_paid": "0.00",
            "currency": "USD",
            "payment_status": "UNPAID",
        }
        client.post("/api/v1/invoices", json=data)

    resp = client.get("/api/v1/invoices?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pages"] == 3


def test_list_invoices_filter_by_supplier(client) -> None:
    for supplier in ["Acme", "Beta Corp"]:
        data = {
            "invoice_number": f"INV-{supplier[:3]}",
            "business_unit": "BU",
            "supplier": supplier,
            "invoice_date": "2025-01-01",
            "invoice_amount": "100.00",
            "amount_paid": "0.00",
            "currency": "USD",
            "payment_status": "UNPAID",
        }
        client.post("/api/v1/invoices", json=data)

    resp = client.get("/api/v1/invoices?supplier=Acme")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["supplier"] == "Acme"


def test_summary_empty(client) -> None:
    resp = client.get("/api/v1/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_invoices"] == 0


def test_supplier_ranking_empty(client) -> None:
    resp = client.get("/api/v1/analytics/supplier-ranking")
    assert resp.status_code == 200
    assert resp.json() == []


def test_monthly_trend_empty(client) -> None:
    resp = client.get("/api/v1/analytics/monthly-trend")
    assert resp.status_code == 200
    assert resp.json() == []


def test_currency_breakdown_empty(client) -> None:
    resp = client.get("/api/v1/analytics/currency-breakdown")
    assert resp.status_code == 200
    assert resp.json() == []


def test_overdue_invoices_empty(client) -> None:
    resp = client.get("/api/v1/analytics/overdue")
    assert resp.status_code == 200
    assert resp.json() == []


def test_status_distribution_empty(client) -> None:
    resp = client.get("/api/v1/analytics/status-distribution")
    assert resp.status_code == 200
    assert resp.json() == {}


def test_create_invoice_invalid_amount(client) -> None:
    data = {
        "invoice_number": "INV-BAD",
        "business_unit": "BU",
        "supplier": "X",
        "invoice_date": "2025-01-01",
        "invoice_amount": "-100.00",
        "amount_paid": "0.00",
        "currency": "USD",
        "payment_status": "UNPAID",
    }
    resp = client.post("/api/v1/invoices", json=data)
    assert resp.status_code == 422


def test_metrics_endpoint(client) -> None:
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_invoices" in data
    assert "unpaid_ratio" in data


def test_view_selector_endpoint_empty(client) -> None:
    resp = client.get("/api/v1/report/view-selector")
    assert resp.status_code == 200
    data = resp.json()
    assert "table_view" in data
    assert "graph_view" in data


def test_view_selector_with_data(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.get("/api/v1/report/view-selector")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["table_view"]) == 1
    assert data["graph_view"]["total_invoices"] == 1


def test_list_invoices_filter_by_payment_status(client) -> None:
    for i, status in enumerate(["PAID", "UNPAID", "PARTIAL"]):
        data = {
            "invoice_number": f"STATUS-{i}",
            "business_unit": "BU",
            "supplier": "Supplier",
            "invoice_date": "2025-01-01",
            "invoice_amount": "100.00",
            "amount_paid": "0.00",
            "currency": "USD",
            "payment_status": status,
        }
        client.post("/api/v1/invoices", json=data)

    resp = client.get("/api/v1/invoices?payment_status=PAID")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_update_invoice_payment(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.patch("/api/v1/invoices/INV-001?amount_paid=500.00&payment_status=PARTIAL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_status"] == "PARTIAL"


def test_update_invoice_not_found(client) -> None:
    resp = client.patch("/api/v1/invoices/GHOST?amount_paid=100.00")
    assert resp.status_code == 404


def test_update_invoice_overpayment_rejected(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.patch("/api/v1/invoices/INV-001?amount_paid=99999.00")
    assert resp.status_code == 422


def test_delete_invoice_success(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.delete("/api/v1/invoices/INV-001")
    assert resp.status_code == 204
    get_resp = client.get("/api/v1/invoices/INV-001")
    assert get_resp.status_code == 404


def test_delete_invoice_not_found(client) -> None:
    resp = client.delete("/api/v1/invoices/NONEXISTENT")
    assert resp.status_code == 404


def test_currency_normalized_endpoint(client, sample_invoice_data) -> None:
    client.post("/api/v1/invoices", json=sample_invoice_data)
    resp = client.get("/api/v1/analytics/currency-normalized")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "invoice_amount_usd" in data[0]


def test_list_invoices_filter_by_date_from(client) -> None:
    for inv_date in ["2025-01-01", "2025-03-01", "2025-06-01"]:
        idx = inv_date.replace("-", "")
        data = {
            "invoice_number": f"DATE-{idx}",
            "business_unit": "BU",
            "supplier": "Supplier",
            "invoice_date": inv_date,
            "invoice_amount": "100.00",
            "amount_paid": "0.00",
            "currency": "USD",
            "payment_status": "UNPAID",
        }
        client.post("/api/v1/invoices", json=data)

    resp = client.get("/api/v1/invoices?date_from=2025-03-01")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_invoices_filter_by_date_to(client) -> None:
    for inv_date in ["2025-01-01", "2025-03-01", "2025-06-01"]:
        idx = inv_date.replace("-", "")
        data = {
            "invoice_number": f"DTO-{idx}",
            "business_unit": "BU",
            "supplier": "Vendor",
            "invoice_date": inv_date,
            "invoice_amount": "100.00",
            "amount_paid": "0.00",
            "currency": "USD",
            "payment_status": "UNPAID",
        }
        client.post("/api/v1/invoices", json=data)

    resp = client.get("/api/v1/invoices?date_to=2025-03-01")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_summary_includes_cancelled_count(client) -> None:
    data = {
        "invoice_number": "CAN-001",
        "business_unit": "BU",
        "supplier": "X",
        "invoice_date": "2025-01-01",
        "invoice_amount": "100.00",
        "amount_paid": "0.00",
        "currency": "USD",
        "payment_status": "CANCELLED",
    }
    client.post("/api/v1/invoices", json=data)
    resp = client.get("/api/v1/summary")
    assert resp.status_code == 200


def test_summary_with_supplier_filter(client) -> None:
    for i, supplier in enumerate(["Acme", "Beta"]):
        data = {
            "invoice_number": f"SUMF-{i}",
            "business_unit": "BU",
            "supplier": supplier,
            "invoice_date": "2025-01-01",
            "invoice_amount": "1000.00",
            "amount_paid": "0.00",
            "currency": "USD",
            "payment_status": "UNPAID",
        }
        client.post("/api/v1/invoices", json=data)

    resp = client.get("/api/v1/summary?supplier=Acme")
    assert resp.status_code == 200
    assert resp.json()["total_invoices"] == 1
