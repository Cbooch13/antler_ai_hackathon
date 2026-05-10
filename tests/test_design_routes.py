from fastapi.testclient import TestClient

from app.main import create_app


def test_design_route_returns_three_schematic_options() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/design/schematics",
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
    assert payload["listing"]["listingId"] == "kaggle-austin-001"
    assert [option["strategy"] for option in payload["options"]] == [
        "conservative",
        "balanced",
        "max_yield",
    ]
    assert payload["options"][0]["targetBuildingSqft"] == 1804
    assert payload["options"][1]["targetBuildingSqft"] == 2200
    assert payload["options"][2]["targetBuildingSqft"] == 2530
    assert all(option["floorPlans"] for option in payload["options"])
    assert all(option["floorPlans"][0]["totalSqft"] > 0 for option in payload["options"])
    assert all(option["floorPlans"][0]["rooms"] for option in payload["options"])

    balanced = payload["options"][1]
    balanced_rooms = balanced["floorPlans"][0]["rooms"]
    balanced_room_names = {room["name"] for room in balanced_rooms}
    assert balanced["units"] == 2
    assert sum(1 for name in balanced_room_names if name.startswith("Bedroom")) == 4
    assert "Second-unit studio" in balanced_room_names
    assert sum(1 for room in balanced_rooms if room["category"] == "bath") == 3
    assert all(option["complianceFindings"] for option in payload["options"])
    assert payload["warnings"]


def test_design_route_404s_unknown_listing() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/design/schematics",
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
