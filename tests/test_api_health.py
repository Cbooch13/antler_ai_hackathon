from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_reports_stage_one() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stage": "1-intake"}
