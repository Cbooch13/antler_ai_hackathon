from fastapi.testclient import TestClient

from app.main import create_app


def test_design_route_returns_comfort_and_space_utilization_options() -> None:
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
        "human_comfort",
        "space_utilization",
    ]
    assert payload["options"][0]["targetBuildingSqft"] == 2200
    assert payload["options"][1]["targetBuildingSqft"] == 2200
    assert all(option["floorPlans"] for option in payload["options"])
    assert all(option["floorPlans"][0]["totalSqft"] > 0 for option in payload["options"])
    assert all(option["floorPlans"][0]["rooms"] for option in payload["options"])
    assert all(option["floorPlans"][0]["walls"] for option in payload["options"])
    assert all(option["floorPlans"][0]["openings"] for option in payload["options"])
    assert all(option["floorPlans"][0]["scaleAssumption"] for option in payload["options"])
    assert all(option["floorPlans"][0]["visualExports"][0]["format"] == "svg" for option in payload["options"])
    assert all(abs(option["floorPlans"][0]["sqftDelta"]) < 0.01 for option in payload["options"])

    comfort = payload["options"][0]
    comfort_rooms = comfort["floorPlans"][0]["rooms"]
    comfort_room_names = {room["name"] for room in comfort_rooms}
    assert comfort["units"] == 2
    assert sum(1 for name in comfort_room_names if name.startswith("Bedroom")) == 4
    assert "Primary bedroom" in comfort_room_names
    assert "ADU living / sleep" in comfort_room_names
    assert "ADU bath" in comfort_room_names
    assert sum(1 for room in comfort_rooms if room["category"] == "bath") >= 3
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
