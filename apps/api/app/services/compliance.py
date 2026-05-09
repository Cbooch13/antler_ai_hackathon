from app.services.listings import get_listing_detail
from realestate_schemas import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResponse,
    ComplianceMetric,
    Confidence,
    FindingStatus,
    Listing,
    MetricBasis,
    Parcel,
    UserBuildSpec,
)
from rules import evaluate_lot_feasibility


def evaluate_compliance(
    request: ComplianceEvaluationRequest,
) -> ComplianceEvaluationResponse | None:
    detail = get_listing_detail(request.listing_id)
    if detail is None or detail.parcel is None:
        return None

    findings = evaluate_lot_feasibility(
        build_spec=request.spec,
        listing=detail.listing,
        parcel=detail.parcel,
    )
    blocking_or_unknown = [
        finding
        for finding in findings
        if finding.status.value in {"fails", "unknown", "warning"}
    ]
    summary = (
        f"{len(findings)} advisory findings generated; "
        f"{len(blocking_or_unknown)} require review or additional data."
    )
    return ComplianceEvaluationResponse(
        listing=detail.listing,
        parcel=detail.parcel,
        metrics=build_compliance_metrics(request.spec, detail.listing, detail.parcel),
        findings=findings,
        summary=summary,
        professional_verification_required=True,
    )


def build_compliance_metrics(
    spec: UserBuildSpec,
    listing: Listing,
    parcel: Parcel,
) -> list[ComplianceMetric]:
    zoning = parcel.zoning or _estimate_zoning(listing)
    lot_sqft = parcel.lot_sqft or listing.lot_sqft
    coverage = _coverage_ratio(listing.building_sqft, lot_sqft)

    return [
        _metric(
            "Lot information",
            "Address",
            listing.address,
            MetricBasis.KNOWN,
            FindingStatus.PASSES,
            Confidence.LOW,
            "Kaggle static fallback row",
            "Address is from MVP fallback data and should be cross-checked.",
        ),
        _metric(
            "Lot information",
            "Part of town",
            listing.neighborhood or "Unknown",
            MetricBasis.KNOWN if listing.neighborhood else MetricBasis.UNKNOWN,
            FindingStatus.PASSES if listing.neighborhood else FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Kaggle static fallback row",
            None,
        ),
        _metric(
            "Lot information",
            "Lot size",
            _format_sqft(lot_sqft),
            MetricBasis.KNOWN if lot_sqft else MetricBasis.UNKNOWN,
            _target_status(lot_sqft, spec.target_lot_sqft),
            Confidence.LOW,
            "Kaggle static fallback row cross-check target: Travis County Appraisal District parcel records",
            _target_note("Target lot size", spec.target_lot_sqft),
        ),
        _metric(
            "Lot information",
            "Requested units",
            str(spec.units),
            MetricBasis.KNOWN,
            FindingStatus.PASSES,
            Confidence.HIGH,
            "User intake",
            None,
        ),
        _metric(
            "Lot information",
            "Recorded units",
            str(listing.units),
            MetricBasis.KNOWN,
            FindingStatus.PASSES if listing.units >= spec.units else FindingStatus.WARNING,
            Confidence.LOW,
            "Kaggle static fallback row",
            "Unit count is static fallback data, not an entitlement.",
        ),
        _metric(
            "Zoning",
            "Zoning district",
            zoning,
            MetricBasis.KNOWN if parcel.zoning else MetricBasis.ESTIMATED,
            FindingStatus.PASSES if parcel.zoning else FindingStatus.WARNING,
            Confidence.LOW,
            "Austin GIS zoning join",
            (
                "Official zoning has not been joined; SF-3 is a conservative residential "
                "infill placeholder until the Austin zoning FeatureServer is queried."
            )
            if parcel.zoning is None
            else None,
        ),
        _metric(
            "Setbacks",
            "Front setback",
            _estimated_setback(zoning, "front"),
            MetricBasis.ESTIMATED,
            FindingStatus.WARNING,
            Confidence.LOW,
            "Austin Land Development Code",
            "Advisory SF-3-style estimate; verify against official zoning, lot geometry, compatibility, and current code.",
        ),
        _metric(
            "Setbacks",
            "Side setback",
            _estimated_setback(zoning, "side"),
            MetricBasis.ESTIMATED,
            FindingStatus.WARNING,
            Confidence.LOW,
            "Austin Land Development Code",
            "Advisory SF-3-style estimate; side setbacks can change with lot width, height, use, and overlays.",
        ),
        _metric(
            "Setbacks",
            "Rear setback",
            _estimated_setback(zoning, "rear"),
            MetricBasis.ESTIMATED,
            FindingStatus.WARNING,
            Confidence.LOW,
            "Austin Land Development Code",
            "Advisory SF-3-style estimate; verify with survey, zoning, and code review.",
        ),
        _metric(
            "Building coverage",
            "Building square footage",
            _format_sqft(listing.building_sqft),
            MetricBasis.KNOWN if listing.building_sqft else MetricBasis.UNKNOWN,
            _target_status(listing.building_sqft, spec.target_building_sqft, lower_is_warning=False),
            Confidence.LOW,
            "Kaggle static fallback row",
            _target_note("Target building size", spec.target_building_sqft),
        ),
        _metric(
            "Building coverage",
            "FAR / building coverage",
            _format_percent(coverage),
            MetricBasis.ESTIMATED if coverage is not None else MetricBasis.UNKNOWN,
            FindingStatus.WARNING if coverage is not None else FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Derived from Kaggle building sqft and lot sqft; code limits require official zoning and envelope rules",
            "Existing structure ratio only; not max allowed FAR/building coverage.",
        ),
        _metric(
            "Building coverage",
            "Impervious cover",
            _estimated_impervious_cover(coverage),
            MetricBasis.ESTIMATED if coverage is not None else MetricBasis.UNKNOWN,
            FindingStatus.WARNING if coverage is not None else FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Land Development Code",
            "Rough estimate from building footprint plus driveway/patio allowance; site plan and survey required.",
        ),
        _metric(
            "Environmental",
            "Tree ordinance risk",
            "Estimate: medium",
            MetricBasis.PUBLIC_DATA_PENDING,
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Open Data tree inventory / arborist survey",
            "Public tree inventory can screen nearby city trees, but private protected trees need a survey.",
        ),
        _metric(
            "Environmental",
            "Floodplain / WUI overlays",
            "Public overlay join pending",
            MetricBasis.PUBLIC_DATA_PENDING,
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin WUI Code Overlay FeatureServer and FEMA floodplain FeatureServer",
            "Use parcel coordinates for spatial joins before design decisions.",
        ),
        _metric(
            "Public safety",
            "Crime statistics",
            "Public incident join pending",
            MetricBasis.PUBLIC_DATA_PENDING,
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Open Data crime reports",
            "Join recent incident records by radius and date window; show counts by category, not a safety conclusion.",
        ),
        _metric(
            "Permitting",
            "Permit history",
            "Public permit join pending",
            MetricBasis.PUBLIC_DATA_PENDING,
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin permit data",
            "Austin permit records are already available in integrations and should be address/parcel matched next.",
        ),
    ]


def _metric(
    category: str,
    label: str,
    value: str,
    basis: MetricBasis,
    status: FindingStatus,
    confidence: Confidence,
    source: str,
    notes: str | None,
) -> ComplianceMetric:
    return ComplianceMetric(
        category=category,
        label=label,
        value=value,
        basis=basis,
        status=status,
        confidence=confidence,
        source=source,
        notes=notes,
    )


def _format_sqft(value: float | None) -> str:
    if value is None:
        return "Unknown"
    return f"{value:,.0f} sqft"


def _target_status(
    value: float | None,
    target: float | None,
    lower_is_warning: bool = True,
) -> FindingStatus:
    if value is None or target is None:
        return FindingStatus.UNKNOWN
    if lower_is_warning and value < target:
        return FindingStatus.WARNING
    return FindingStatus.PASSES


def _target_note(label: str, target: float | None) -> str | None:
    if target is None:
        return None
    return f"{label}: {target:,.0f} sqft."


def _estimate_zoning(listing: Listing) -> str:
    if listing.units >= 2:
        return "SF-3 (estimated)"
    return "SF-3 (estimated)"


def _estimated_setback(zoning: str, setback: str) -> str:
    if "SF-3" not in zoning:
        return "Requires zoning-specific lookup"

    estimates = {
        "front": "25 ft estimate",
        "side": "5 ft estimate",
        "rear": "10 ft estimate",
    }
    return estimates[setback]


def _coverage_ratio(building_sqft: float | None, lot_sqft: float | None) -> float | None:
    if not building_sqft or not lot_sqft:
        return None
    return building_sqft / lot_sqft


def _format_percent(value: float | None) -> str:
    if value is None:
        return "Unknown"
    return f"{value * 100:.1f}% existing building-to-lot ratio"


def _estimated_impervious_cover(building_coverage: float | None) -> str:
    if building_coverage is None:
        return "Unknown"
    estimated = min(building_coverage + 0.12, 1.0)
    return f"{estimated * 100:.1f}% rough impervious-cover estimate"
