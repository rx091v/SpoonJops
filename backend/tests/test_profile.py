from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_job_search_profile_endpoint_returns_demo_targeting() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/system/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Rahul Mathur"
    assert body["target_job_remote_only"] is False
    assert "Staff Software Engineer" in body["target_job_titles"]
