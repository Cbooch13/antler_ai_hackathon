from fastapi.testclient import TestClient

from app.main import create_app


def test_compliance_route_returns_advisory_findings() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/compliance/evaluate",
        json={
            "spec": {
                "projectName": "ADU search",
                "city": "Austin",
                "state": "TX",
                "propertyType": "adu",
                "totalBudgetUsd": 850000,
                "targetLotSqft": 6500,
                "targetBuildingSqft": 2200,
                "bedrooms": 4,
                "bathrooms": 3,
                "units": 2,
                "stylePreferences": [],
                "riskTolerance": "medium",
            },
            "listingId": "kaggle-austin-001",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["professionalVerificationRequired"] is True
    assert payload["listing"]["listingId"] == "kaggle-austin-001"
    assert payload["parcel"]["parcelId"] == "prototype-kaggle-austin-001"
    assert any(finding["code"] == "STATIC-DATASET-SOURCE" for finding in payload["findings"])
    assert any(finding["status"] == "unknown" for finding in payload["findings"])


def test_compliance_route_404s_unknown_listing() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/compliance/evaluate",
        json={
            "spec": {
                "projectName": "ADU search",
                "city": "Austin",
                "state": "TX",
                "propertyType": "adu",
                "totalBudgetUsd": 850000,
                "units": 2,
                "stylePreferences": [],
                "riskTolerance": "medium",
            },
            "listingId": "not-real",
        },
    )

    assert response.status_code == 404
