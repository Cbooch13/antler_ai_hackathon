from app.services.compliance import evaluate_compliance
from estate_agents import SchematicAgentInput, SchematicDesignAgent
from realestate_schemas import (
    DesignGenerationRequest,
    DesignGenerationResponse,
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
    options = SchematicDesignAgent().generate(
        SchematicAgentInput(spec=request.spec, warning_findings=warning_findings)
    )

    return DesignGenerationResponse(
        listing=compliance.listing,
        parcel=compliance.parcel,
        options=options,
        warnings=[
            "Stage 6C schematic agent outputs are conceptual planning studies only.",
            "Architect, civil engineer, surveyor, attorney, and city review are required before design reliance.",
        ],
    )
