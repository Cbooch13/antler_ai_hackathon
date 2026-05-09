from realestate_schemas import Parcel, PropertyType, UserBuildSpec
from rules import evaluate_foundation_compliance


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
