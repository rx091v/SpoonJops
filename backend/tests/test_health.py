from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_endpoint_returns_service_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_service_info_endpoint_returns_versioned_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/system/info")

    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"
