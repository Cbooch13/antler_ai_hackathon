from app.services.compliance import evaluate_compliance
from estate_agents import OpenAISchematicDesignAgent, SchematicAgentInput
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
    options = OpenAISchematicDesignAgent().generate(
        SchematicAgentInput(
            spec=request.spec,
            warning_findings=warning_findings,
            address=compliance.listing.address,
            neighborhood=compliance.listing.neighborhood,
            lot_sqft=compliance.parcel.lot_sqft or compliance.listing.lot_sqft,
            zoning=compliance.parcel.zoning,
        )
    )

    return DesignGenerationResponse(
        listing=compliance.listing,
        parcel=compliance.parcel,
        options=options,
        warnings=[
            "Stage 6L schematic agent outputs are conceptual planning studies only.",
            "When LLM_SCHEMATIC_ENABLED is false or OpenAI is unavailable, the service falls back to the local generator.",
            "Architect, civil engineer, surveyor, attorney, and city review are required before design reliance.",
        ],
    )
