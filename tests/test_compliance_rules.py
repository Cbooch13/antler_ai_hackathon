from datetime import datetime, timezone

from realestate_schemas import (
    Confidence,
    Listing,
    ListingSourceMode,
    Parcel,
    PropertyType,
    SourceMetadata,
    UserBuildSpec,
)
from rules import evaluate_foundation_compliance, evaluate_lot_feasibility


def test_commercial_spec_is_flagged_as_phase_two() -> None:
    findings = evaluate_foundation_compliance(
        UserBuildSpec(
            project_name="Mixed-use concept",
            property_type=PropertyType.COMMERCIAL,
            total_budget_usd=2_500_000,
        ),
        Parcel(parcel_id="p1", address="Austin, TX", zoning="CS"),
    )

    assert findings[0].code == "MVP-COMMERCIAL-SCOPE"
    assert findings[0].professional_verification_required is True


def test_missing_zoning_is_unknown_not_pass() -> None:
    findings = evaluate_foundation_compliance(
        UserBuildSpec(
            project_name="ADU concept",
            property_type=PropertyType.ADU,
            total_budget_usd=900_000,
        ),
        Parcel(parcel_id="p2", address="Austin, TX"),
    )

    assert any(finding.status.value == "unknown" for finding in findings)
    assert all(finding.status.value != "passes" for finding in findings)


def test_lot_feasibility_never_treats_static_listing_as_approval() -> None:
    source = SourceMetadata(
        source_name="Kaggle Austin housing prices dataset",
        source_url="https://www.kaggle.com/datasets/ericpierce/austinhousingprices",
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.LOW,
    )
    spec = UserBuildSpec(
        project_name="ADU concept",
        property_type=PropertyType.ADU,
        total_budget_usd=850_000,
        target_lot_sqft=6_500,
        units=2,
    )
    listing = Listing(
        listing_id="kaggle-austin-001",
        address="4307 Avenue G, Austin, TX 78751",
        price_usd=825_000,
        lot_sqft=6_600,
        units=2,
        source_mode=ListingSourceMode.PROTOTYPE_STATIC_DATASET,
        current_inventory=False,
        sources=[source],
    )

    findings = evaluate_lot_feasibility(
        build_spec=spec,
        listing=listing,
        parcel=Parcel(
            parcel_id="prototype-kaggle-austin-001",
            address=listing.address,
            lot_sqft=listing.lot_sqft,
            sources=[source],
        ),
    )

    codes = {finding.code for finding in findings}
    assert "STATIC-DATASET-SOURCE" in codes
    assert "NOT-OFFICIAL-APPROVAL" in codes
    assert "LOT-SIZE-TARGET" in codes
    assert any(finding.status.value == "unknown" for finding in findings)
    assert all(finding.professional_verification_required for finding in findings)
