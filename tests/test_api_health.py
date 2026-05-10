from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_reports_stage_six_c() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stage": "6c-schematic-agent"}
