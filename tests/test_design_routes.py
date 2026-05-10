from fastapi.testclient import TestClient

from app.main import create_app


def test_design_route_returns_one_primary_schematic_option() -> None:
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
    assert [option["strategy"] for option in payload["options"]] == ["human_comfort"]
    assert payload["options"][0]["targetBuildingSqft"] == 2200
    assert all(option["floorPlans"] for option in payload["options"])
    assert all(option["floorPlans"][0]["totalSqft"] > 0 for option in payload["options"])
    assert all(option["floorPlans"][0]["rooms"] for option in payload["options"])
    assert all(option["floorPlans"][0]["walls"] for option in payload["options"])
    assert all(option["floorPlans"][0]["openings"] for option in payload["options"])
    assert all(option["floorPlans"][0]["connections"] for option in payload["options"])
    assert all(option["floorPlans"][0]["scaleAssumption"] for option in payload["options"])
    assert all(option["floorPlans"][0]["visualExports"][0]["format"] == "svg" for option in payload["options"])
    assert all(option["floorPlans"][0]["qualityReport"]["checks"] for option in payload["options"])
    assert all(option["floorPlans"][0]["qualityReport"]["score"] > 0 for option in payload["options"])
    assert any(
        "Selected from 7 exemplar-guided local candidate generations" in assumption
        for assumption in payload["options"][0]["assumptions"]
    )
    assert any(
        check["code"] == "exemplar_fit"
        for check in payload["options"][0]["floorPlans"][0]["qualityReport"]["checks"]
    )
    assert all(
        option["floorPlans"][0]["qualityReport"]["status"] in {"passes", "warning"}
        for option in payload["options"]
    )
    assert all(
        any(check["code"] == "path_connectivity" for check in option["floorPlans"][0]["qualityReport"]["checks"])
        for option in payload["options"]
    )
    assert all(
        not any(
            check["status"] == "fails"
            for check in option["floorPlans"][0]["qualityReport"]["checks"]
        )
        for option in payload["options"]
    )
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
