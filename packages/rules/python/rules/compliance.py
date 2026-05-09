from realestate_schemas import (
    ComplianceFinding,
    Confidence,
    FindingStatus,
    Listing,
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


def evaluate_lot_feasibility(
    build_spec: UserBuildSpec,
    listing: Listing,
    parcel: Parcel,
) -> list[ComplianceFinding]:
    findings = evaluate_foundation_compliance(build_spec, parcel)

    findings.append(
        ComplianceFinding(
            code="NOT-OFFICIAL-APPROVAL",
            title="Advisory feasibility only",
            status=FindingStatus.WARNING,
            summary=(
                "This check is a planning screen, not City of Austin approval or a substitute "
                "for architect, engineer, survey, legal, arborist, or city review."
            ),
            confidence=Confidence.HIGH,
            professional_verification_required=True,
            citations=parcel.sources,
        )
    )

    if not listing.current_inventory:
        findings.append(
            ComplianceFinding(
                code="STATIC-DATASET-SOURCE",
                title="Static fallback data",
                status=FindingStatus.WARNING,
                summary=(
                    "This property comes from a static MVP fallback dataset and must not be "
                    "treated as active inventory."
                ),
                confidence=Confidence.HIGH,
                professional_verification_required=True,
                citations=listing.sources,
            )
        )

    if build_spec.target_lot_sqft and listing.lot_sqft:
        if listing.lot_sqft >= build_spec.target_lot_sqft:
            findings.append(
                ComplianceFinding(
                    code="LOT-SIZE-TARGET",
                    title="Lot size target",
                    status=FindingStatus.PASSES,
                    summary=(
                        f"Static lot size estimate of {listing.lot_sqft:,.0f} sqft meets the "
                        f"target of {build_spec.target_lot_sqft:,.0f} sqft."
                    ),
                    confidence=Confidence.LOW,
                    professional_verification_required=True,
                    citations=listing.sources,
                )
            )
        else:
            findings.append(
                ComplianceFinding(
                    code="LOT-SIZE-TARGET",
                    title="Lot size target",
                    status=FindingStatus.WARNING,
                    summary=(
                        f"Static lot size estimate of {listing.lot_sqft:,.0f} sqft is below the "
                        f"target of {build_spec.target_lot_sqft:,.0f} sqft."
                    ),
                    confidence=Confidence.LOW,
                    professional_verification_required=True,
                    citations=listing.sources,
                )
            )

    if listing.units >= build_spec.units:
        findings.append(
            ComplianceFinding(
                code="UNIT-COUNT-TARGET",
                title="Unit count target",
                status=FindingStatus.PASSES,
                summary=(
                    f"The record's unit count of {listing.units} meets the requested "
                    f"{build_spec.units} unit target."
                ),
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=listing.sources,
            )
        )
    else:
        findings.append(
            ComplianceFinding(
                code="UNIT-COUNT-TARGET",
                title="Unit count target",
                status=FindingStatus.WARNING,
                summary=(
                    f"The record's unit count of {listing.units} is below the requested "
                    f"{build_spec.units} unit target."
                ),
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=listing.sources,
            )
        )

    if parcel.zoning is None:
        findings.append(
            ComplianceFinding(
                code="ZONING-JOIN-REQUIRED",
                title="Official zoning join required",
                status=FindingStatus.UNKNOWN,
                summary=(
                    "No official zoning district has been joined yet, so allowed use, setbacks, "
                    "height, impervious cover, and compatibility cannot be confirmed."
                ),
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=parcel.sources,
            )
        )

    findings.extend(
        [
            ComplianceFinding(
                code="TREE-REVIEW-REQUIRED",
                title="Tree review unknown",
                status=FindingStatus.UNKNOWN,
                summary=(
                    "Tree constraints cannot be evaluated until a tree survey or official city "
                    "tree data is joined."
                ),
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=parcel.sources,
            ),
            ComplianceFinding(
                code="FLOOD-WUI-REVIEW-REQUIRED",
                title="Floodplain and WUI overlays unknown",
                status=FindingStatus.UNKNOWN,
                summary=(
                    "Floodplain and Wildland-Urban Interface overlay impacts are not joined yet "
                    "and must be verified before design decisions."
                ),
                confidence=Confidence.LOW,
                professional_verification_required=True,
                citations=parcel.sources,
            ),
        ]
    )

    return findings
