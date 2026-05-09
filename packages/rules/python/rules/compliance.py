from realestate_schemas import (
    ComplianceFinding,
    Confidence,
    FindingStatus,
    Parcel,
    UserBuildSpec,
)


def evaluate_foundation_compliance(
    build_spec: UserBuildSpec,
    parcel: Parcel,
) -> list[ComplianceFinding]:
    """Stage 0 placeholder rules that enforce conservative status semantics."""
    findings: list[ComplianceFinding] = []

    if build_spec.property_type.value == "commercial":
        findings.append(
            ComplianceFinding(
                code="MVP-COMMERCIAL-SCOPE",
                title="Commercial workflow is phase two",
                status=FindingStatus.WARNING,
                summary=(
                    "Commercial feasibility can be captured during intake, but MVP rules are "
                    "limited to residential infill until commercial checks are modeled."
                ),
                confidence=Confidence.MEDIUM,
                professional_verification_required=True,
                citations=parcel.sources,
            )
        )

    if parcel.zoning is None:
        findings.append(
            ComplianceFinding(
                code="MISSING-ZONING",
                title="Zoning data unavailable",
                status=FindingStatus.UNKNOWN,
                summary="No zoning value is attached to this parcel yet.",
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=parcel.sources,
            )
        )

    if not findings:
        findings.append(
            ComplianceFinding(
                code="FOUNDATION-READY",
                title="Ready for detailed rule evaluation",
                status=FindingStatus.UNKNOWN,
                summary="Stage 0 confirms schema compatibility, not permit feasibility.",
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=parcel.sources,
            )
        )

    return findings
