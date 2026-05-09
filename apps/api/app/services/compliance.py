from app.services.listings import get_listing_detail
from realestate_schemas import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResponse,
    ComplianceMetric,
    Confidence,
    FindingStatus,
    Listing,
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
    return [
        _metric(
            "Lot information",
            "Address",
            listing.address,
            FindingStatus.PASSES,
            Confidence.LOW,
            "Kaggle static fallback row",
            "Address is from MVP fallback data and should be cross-checked.",
        ),
        _metric(
            "Lot information",
            "Part of town",
            listing.neighborhood or "Unknown",
            FindingStatus.PASSES if listing.neighborhood else FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Kaggle static fallback row",
            None,
        ),
        _metric(
            "Lot information",
            "Lot size",
            _format_sqft(listing.lot_sqft),
            _target_status(listing.lot_sqft, spec.target_lot_sqft),
            Confidence.LOW,
            "Kaggle static fallback row",
            _target_note("Target lot size", spec.target_lot_sqft),
        ),
        _metric(
            "Lot information",
            "Requested units",
            str(spec.units),
            FindingStatus.PASSES,
            Confidence.HIGH,
            "User intake",
            None,
        ),
        _metric(
            "Lot information",
            "Recorded units",
            str(listing.units),
            FindingStatus.PASSES if listing.units >= spec.units else FindingStatus.WARNING,
            Confidence.LOW,
            "Kaggle static fallback row",
            "Unit count is static fallback data, not an entitlement.",
        ),
        _metric(
            "Zoning",
            "Zoning district",
            parcel.zoning or "Unknown",
            FindingStatus.UNKNOWN if parcel.zoning is None else FindingStatus.PASSES,
            Confidence.LOW,
            "Austin GIS zoning join",
            "Official zoning has not been joined for this prototype parcel.",
        ),
        _metric(
            "Setbacks",
            "Front setback",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Land Development Code",
            "Requires official zoning district, lot geometry, and code rule lookup.",
        ),
        _metric(
            "Setbacks",
            "Side setback",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Land Development Code",
            "Requires official zoning district and lot geometry.",
        ),
        _metric(
            "Setbacks",
            "Rear setback",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Land Development Code",
            "Requires official zoning district and lot geometry.",
        ),
        _metric(
            "Building coverage",
            "Building square footage",
            _format_sqft(listing.building_sqft),
            _target_status(listing.building_sqft, spec.target_building_sqft, lower_is_warning=False),
            Confidence.LOW,
            "Kaggle static fallback row",
            _target_note("Target building size", spec.target_building_sqft),
        ),
        _metric(
            "Building coverage",
            "FAR / building coverage",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Land Development Code",
            "Requires zoning district, official lot area, and building envelope rules.",
        ),
        _metric(
            "Building coverage",
            "Impervious cover",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin Land Development Code",
            "Requires site plan, lot geometry, and surface coverage data.",
        ),
        _metric(
            "Environmental",
            "Tree ordinance risk",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin tree review",
            "Requires tree survey or official tree data.",
        ),
        _metric(
            "Environmental",
            "Floodplain / WUI overlays",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin GIS overlay joins",
            "Overlay layers are not joined in this stage.",
        ),
        _metric(
            "Public safety",
            "Crime statistics",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin public safety data",
            "Crime data is not integrated yet and should be sourced, dated, and normalized separately.",
        ),
        _metric(
            "Permitting",
            "Permit history",
            "Unknown",
            FindingStatus.UNKNOWN,
            Confidence.LOW,
            "Austin permit data",
            "Permit records are available but not joined to this prototype parcel yet.",
        ),
    ]


def _metric(
    category: str,
    label: str,
    value: str,
    status: FindingStatus,
    confidence: Confidence,
    source: str,
    notes: str | None,
) -> ComplianceMetric:
    return ComplianceMetric(
        category=category,
        label=label,
        value=value,
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
