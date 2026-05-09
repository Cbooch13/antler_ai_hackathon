from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import create_app
from realestate_schemas import (
    Confidence,
    DataIngestionResponse,
    IngestionSourceKind,
    PermitRecord,
    SourceMetadata,
)


def test_recent_permits_route_returns_normalized_records(monkeypatch) -> None:
    source = SourceMetadata(
        source_name="Austin Open Data issued construction permits",
        source_url="https://data.austintexas.gov/resource/3syk-w9eu.json",
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.HIGH,
    )

    def fake_fetch_recent_permits(limit: int) -> DataIngestionResponse:
        assert limit == 1
        return DataIngestionResponse(
            source_kind=IngestionSourceKind.SOCRATA,
            source_name="Austin issued construction permits",
            records=[
                PermitRecord(
                    permit_id="BP-2024-001",
                    address="100 Congress Ave",
                    sources=[source],
                )
            ],
            source=source,
        )

    monkeypatch.setattr("app.routers.data.fetch_recent_permits", fake_fetch_recent_permits)
    client = TestClient(create_app())

    response = client.get("/data/austin/permits/recent?limit=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sourceKind"] == "socrata"
    assert payload["records"][0]["permitId"] == "BP-2024-001"
    assert payload["records"][0]["sources"][0]["sourceUrl"].endswith("3syk-w9eu.json")
