from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from realestate_schemas import (
    Confidence,
    Listing,
    ListingSourceMode,
    MapContext,
    Parcel,
    ParcelDetailResponse,
    PermitRecord,
    PropertyType,
    RiskTolerance,
    SourceMetadata,
    UserBuildSpec,
)


def test_user_build_spec_accepts_valid_austin_infill_request() -> None:
    spec = UserBuildSpec(
        project_name="East Austin ADU",
        property_type=PropertyType.ADU,
        total_budget_usd=850_000,
        target_lot_sqft=6_500,
        target_building_sqft=2_200,
        bedrooms=4,
        bathrooms=3,
        units=2,
        style_preferences=["warm modern", "natural light"],
        risk_tolerance=RiskTolerance.MEDIUM,
    )

    assert spec.city == "Austin"
    assert spec.state == "TX"
    assert spec.units == 2


def test_user_build_spec_rejects_invalid_budget() -> None:
    with pytest.raises(ValidationError):
        UserBuildSpec(
            project_name="Impossible project",
            property_type=PropertyType.SINGLE_FAMILY,
            total_budget_usd=0,
        )


def test_user_build_spec_accepts_camel_case_api_payload() -> None:
    spec = UserBuildSpec(
        projectName="Camel case intake",
        propertyType="adu",
        totalBudgetUsd=950_000,
        targetLotSqft=6_000,
        units=2,
        riskTolerance="low",
    )

    assert spec.project_name == "Camel case intake"
    assert spec.model_dump(by_alias=True)["totalBudgetUsd"] == 950_000


def test_parcel_requires_valid_coordinates_when_present() -> None:
    source = SourceMetadata(
        source_name="Austin GIS",
        source_url="https://example.com/austin-gis",
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.HIGH,
    )

    parcel = Parcel(
        parcel_id="123",
        address="100 Congress Ave, Austin, TX",
        lot_sqft=7_200,
        zoning="SF-3",
        latitude=30.2672,
        longitude=-97.7431,
        sources=[source],
    )

    assert parcel.sources[0].confidence == Confidence.HIGH


def test_core_json_schema_exports_stage_zero_contracts() -> None:
    schema_path = Path("packages/schemas/json/core.schema.json")
    schema = json.loads(schema_path.read_text())

    assert schema["$defs"]["UserBuildSpec"]["properties"]["city"]["const"] == "Austin"
    assert "ComplianceFinding" in schema["$defs"]
    assert "PermitRecord" in schema["$defs"]
    assert "Listing" in schema["$defs"]


def test_permit_record_preserves_raw_payload_and_source_metadata() -> None:
    source = SourceMetadata(
        source_name="Austin Open Data issued construction permits",
        source_url="https://data.austintexas.gov/resource/3syk-w9eu.json",
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.HIGH,
        license_name="City of Austin Open Data terms",
        notes=["verify official status"],
    )

    permit = PermitRecord(
        permitId="BP-2024-001",
        valuationUsd=650_000,
        raw={"permit_number": "BP-2024-001"},
        sources=[source],
    )

    assert permit.permit_id == "BP-2024-001"
    assert permit.model_dump(by_alias=True)["valuationUsd"] == 650_000
    assert permit.sources[0].notes == ["verify official status"]


def test_listing_static_source_contract_requires_inventory_flag() -> None:
    source = SourceMetadata(
        source_name="Kaggle Austin housing prices dataset",
        source_url="https://www.kaggle.com/datasets/ericpierce/austinhousingprices",
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.LOW,
        license_name="GPL-2.0",
    )

    listing = Listing(
        listingId="kaggle-austin-001",
        address="Central Austin prototype comp",
        priceUsd=825_000,
        lotSqft=6_600,
        buildingSqft=2_150,
        units=2,
        sourceMode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
        currentInventory=False,
        dataYear=2021,
        prototypeNote="Prototype static dataset row. This is not an active listing.",
        sources=[source],
    )

    assert listing.current_inventory is False
    assert listing.model_dump(by_alias=True)["sourceMode"] == "prototype_static_dataset"


def test_parcel_detail_contract_supports_missing_official_joins() -> None:
    source = SourceMetadata(
        source_name="Kaggle Austin housing prices dataset",
        source_url="https://www.kaggle.com/datasets/ericpierce/austinhousingprices",
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.LOW,
    )
    listing = Listing(
        listingId="kaggle-austin-001",
        address="Central Austin prototype comp",
        priceUsd=825_000,
        sourceMode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
        currentInventory=False,
        units=2,
        sources=[source],
    )

    detail = ParcelDetailResponse(
        listing=listing,
        parcel=None,
        mapContext=MapContext(latitude=30.298, longitude=-97.741),
        warnings=["No zoning feature has been joined yet."],
        sources=[source],
    )

    assert detail.map_context.map_provider == "mapbox"
    assert detail.model_dump(by_alias=True)["mapContext"]["latitude"] == 30.298
