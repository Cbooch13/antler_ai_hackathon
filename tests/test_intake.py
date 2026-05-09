from fastapi.testclient import TestClient

from app.main import create_app
from app.services.intake import normalize_build_spec
from realestate_schemas import IntakeNormalizeRequest


def test_normalize_text_builds_valid_adu_spec() -> None:
    result = normalize_build_spec(
        IntakeNormalizeRequest(
            freeText=(
                "I want an ADU with 4 beds, 3 baths, 2 units, 2200 sqft house, "
                "6500 lot sqft, warm modern style, and 850k budget."
            )
        )
    )

    assert result.spec is not None
    assert result.spec.property_type.value == "adu"
    assert result.spec.total_budget_usd == 850_000
    assert result.spec.units == 2
    assert result.missing_fields == []


def test_normalize_text_reports_missing_budget() -> None:
    result = normalize_build_spec(
        IntakeNormalizeRequest(freeText="I want a conservative ADU with natural light.")
    )

    assert result.spec is None
    assert "totalBudgetUsd" in result.missing_fields


def test_intake_api_accepts_camel_case_structured_spec() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/intake/normalize",
        json={
            "freeText": "",
            "structured": {
                "projectName": "North Loop duplex",
                "propertyType": "duplex_triplex",
                "totalBudgetUsd": 1_100_000,
                "targetLotSqft": 7_000,
                "targetBuildingSqft": 3_000,
                "bedrooms": 5,
                "bathrooms": 4,
                "units": 2,
                "riskTolerance": "medium",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["spec"]["projectName"] == "North Loop duplex"
    assert payload["spec"]["totalBudgetUsd"] == 1_100_000
    assert payload["missingFields"] == []
