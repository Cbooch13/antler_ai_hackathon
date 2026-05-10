from app.services.compliance import evaluate_compliance
from realestate_schemas import (
    DesignGenerationRequest,
    DesignGenerationResponse,
    DesignOption,
    FindingStatus,
    FloorPlan,
    FloorPlanRoom,
    UserBuildSpec,
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
            floor_plan=_floor_plan(
                request.spec,
                plan_id="floor-plan-conservative",
                name="Conservative Ground Floor",
                level="Level 1",
                total_sqft=_scaled_sqft(request.spec.target_building_sqft, 0.82),
                units=1,
                compact=True,
                notes=[
                    "Compact one-unit plan keeps more site area available for setbacks and tree/drainage review.",
                    "Room areas are conceptual planning estimates, not measured dimensions.",
                ],
            ),
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
            floor_plan=_floor_plan(
                request.spec,
                plan_id="floor-plan-balanced",
                name="Balanced Ground Floor",
                level="Level 1",
                total_sqft=_scaled_sqft(request.spec.target_building_sqft, 1.0),
                units=request.spec.units,
                compact=False,
                notes=[
                    "Program follows the requested bedrooms, bathrooms, and unit count where provided.",
                    "Adjacencies are conceptual and require architect review before reliance.",
                ],
            ),
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
            floor_plan=_floor_plan(
                request.spec,
                plan_id="floor-plan-max-yield",
                name="Max Yield Ground Floor",
                level="Level 1",
                total_sqft=_scaled_sqft(request.spec.target_building_sqft, 1.15),
                units=request.spec.units,
                compact=False,
                notes=[
                    "Larger program increases review sensitivity for envelope, drainage, egress, structure, and utilities.",
                    "Do not advance to visualization until zoning and site constraints are professionally checked.",
                ],
            ),
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
            "Stage 6B schematics and floor plans are conceptual planning options only.",
            "Architect, civil engineer, surveyor, attorney, and city review are required before design reliance.",
        ],
    )


def _option(
    option_id: str,
    name: str,
    strategy: str,
    target_building_sqft: float,
    units: int,
    floor_plan: FloorPlan,
    assumptions: list[str],
    findings: list,
) -> DesignOption:
    return DesignOption(
        option_id=option_id,
        name=name,
        strategy=strategy,
        target_building_sqft=target_building_sqft,
        units=units,
        floor_plans=[floor_plan],
        assumptions=assumptions,
        compliance_findings=findings,
    )


def _scaled_sqft(target_building_sqft: float | None, factor: float) -> float:
    baseline = target_building_sqft or 1_800
    return max(400, round(baseline * factor))


def _floor_plan(
    spec: UserBuildSpec,
    plan_id: str,
    name: str,
    level: str,
    total_sqft: float,
    units: int,
    compact: bool,
    notes: list[str],
) -> FloorPlan:
    bedrooms = max(1, spec.bedrooms or (2 if compact else 3))
    bathrooms = max(1, round(spec.bathrooms or 2))
    rooms = _base_rooms(total_sqft, bedrooms, bathrooms, units, compact)
    return FloorPlan(
        plan_id=plan_id,
        name=name,
        level=level,
        total_sqft=total_sqft,
        rooms=rooms,
        notes=notes,
    )


def _base_rooms(
    total_sqft: float,
    bedrooms: int,
    bathrooms: int,
    units: int,
    compact: bool,
) -> list[FloorPlanRoom]:
    rooms = [
        _room("living", "Living / dining", "living", total_sqft * 0.22, 0, 0, 42, 38),
        _room("kitchen", "Kitchen", "kitchen", total_sqft * 0.11, 42, 0, 24, 28),
        _room("service", "Laundry / service", "service", total_sqft * 0.06, 66, 0, 18, 22),
    ]

    bedroom_area = total_sqft * (0.09 if compact else 0.1)
    bedroom_layout = [
        (0, 38, 25, 30),
        (25, 38, 25, 30),
        (50, 38, 25, 30),
        (75, 38, 25, 30),
        (0, 68, 25, 32),
        (25, 68, 25, 32),
    ]
    for index in range(min(bedrooms, len(bedroom_layout))):
        x, y, width, height = bedroom_layout[index]
        rooms.append(
            _room(
                f"bedroom-{index + 1}",
                f"Bedroom {index + 1}",
                "bedroom",
                bedroom_area,
                x,
                y,
                width,
                height,
            )
        )

    bath_area = total_sqft * 0.045
    bath_layout = [(84, 0, 16, 22), (66, 22, 18, 22), (84, 22, 16, 22), (50, 68, 18, 32)]
    for index in range(min(bathrooms, len(bath_layout))):
        x, y, width, height = bath_layout[index]
        rooms.append(
            _room(
                f"bath-{index + 1}",
                f"Bath {index + 1}",
                "bath",
                bath_area,
                x,
                y,
                width,
                height,
            )
        )

    if units > 1:
        rooms.append(
            _room("adu-studio", "Second-unit studio", "unit", total_sqft * 0.14, 68, 68, 32, 32)
        )
        rooms.append(
            _room(
                "adu-entry",
                "Second-unit entry",
                "circulation",
                total_sqft * 0.025,
                84,
                44,
                16,
                24,
            )
        )
    else:
        rooms.append(_room("flex", "Flex / office", "flex", total_sqft * 0.08, 68, 68, 32, 32))

    return rooms


def _room(
    room_id: str,
    name: str,
    category: str,
    estimated_sqft: float,
    x: float,
    y: float,
    width: float,
    height: float,
) -> FloorPlanRoom:
    return FloorPlanRoom(
        room_id=room_id,
        name=name,
        category=category,
        estimated_sqft=max(35, round(estimated_sqft)),
        x=x,
        y=y,
        width=width,
        height=height,
    )
