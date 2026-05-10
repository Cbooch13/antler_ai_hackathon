from app.services.compliance import evaluate_compliance
from realestate_schemas import (
    DesignGenerationRequest,
    DesignGenerationResponse,
    DesignOption,
    FindingStatus,
)


def generate_design_options(
    request: DesignGenerationRequest,
) -> DesignGenerationResponse | None:
    compliance = evaluate_compliance(request)
    if compliance is None:
        return None

    warning_findings = [
        finding
        for finding in compliance.findings
        if finding.status in {FindingStatus.WARNING, FindingStatus.UNKNOWN, FindingStatus.FAILS}
    ]
    options = [
        _option(
            option_id="schematic-conservative",
            name="Conservative Envelope",
            strategy="conservative",
            target_building_sqft=_scaled_sqft(request.spec.target_building_sqft, 0.82),
            units=1,
            assumptions=[
                "Prioritizes lower entitlement risk and a smaller building envelope.",
                "Keeps extra room for setbacks, protected trees, drainage, and site access until survey data is joined.",
                "Suitable first review path for architect and surveyor feedback.",
            ],
            findings=warning_findings,
        ),
        _option(
            option_id="schematic-balanced",
            name="Balanced Program",
            strategy="balanced",
            target_building_sqft=_scaled_sqft(request.spec.target_building_sqft, 1.0),
            units=request.spec.units,
            assumptions=[
                "Tracks the user's requested program while preserving feasibility warnings.",
                "Uses current lot/building data as a planning target, not a permit-ready envelope.",
                "Best candidate for conversational tuning in the next design iteration.",
            ],
            findings=warning_findings,
        ),
        _option(
            option_id="schematic-max-yield",
            name="Max Yield Test",
            strategy="max_yield",
            target_building_sqft=_scaled_sqft(request.spec.target_building_sqft, 1.15),
            units=request.spec.units,
            assumptions=[
                "Stress-tests the desired program against the available lot context.",
                "Requires the highest scrutiny for zoning, impervious cover, compatibility, drainage, and tree impacts.",
                "Should not move to visualization until professional review flags are resolved.",
            ],
            findings=warning_findings,
        ),
    ]

    return DesignGenerationResponse(
        listing=compliance.listing,
        parcel=compliance.parcel,
        options=options,
        warnings=[
            "Stage 6 schematics are conceptual planning options only.",
            "Architect, civil engineer, surveyor, attorney, and city review are required before design reliance.",
        ],
    )


def _option(
    option_id: str,
    name: str,
    strategy: str,
    target_building_sqft: float,
    units: int,
    assumptions: list[str],
    findings: list,
) -> DesignOption:
    return DesignOption(
        option_id=option_id,
        name=name,
        strategy=strategy,
        target_building_sqft=target_building_sqft,
        units=units,
        assumptions=assumptions,
        compliance_findings=findings,
    )


def _scaled_sqft(target_building_sqft: float | None, factor: float) -> float:
    baseline = target_building_sqft or 1_800
    return max(400, round(baseline * factor))
