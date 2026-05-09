from app.services.listings import get_listing_detail
from realestate_schemas import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResponse,
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
        findings=findings,
        summary=summary,
        professional_verification_required=True,
    )
