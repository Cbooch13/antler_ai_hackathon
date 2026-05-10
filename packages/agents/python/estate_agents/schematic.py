from dataclasses import dataclass

from realestate_schemas import (
    ComplianceFinding,
    DesignOption,
    FloorPlan,
    FloorPlanOpening,
    FloorPlanRoom,
    FloorPlanWall,
    UserBuildSpec,
)


@dataclass(frozen=True)
class SchematicAgentInput:
    spec: UserBuildSpec
    warning_findings: list[ComplianceFinding]


class SchematicDesignAgent:
    """Deterministic schematic agent for concept-level architectural plans."""

    def generate(self, agent_input: SchematicAgentInput) -> list[DesignOption]:
        spec = agent_input.spec
        comfort_sqft = _scaled_sqft(spec.target_building_sqft, 1.0)
        efficient_sqft = _scaled_sqft(spec.target_building_sqft, 0.9)

        return [
            DesignOption(
                option_id="schematic-human-comfort",
                name="Human Comfort Plan",
                strategy="human_comfort",
                target_building_sqft=comfort_sqft,
                units=spec.units,
                floor_plans=[
                    _comfort_plan(
                        spec=spec,
                        total_sqft=comfort_sqft,
                    )
                ],
                assumptions=[
                    "Prioritizes daylight, room separation, storage, and a clear public-to-private transition.",
                    "Keeps bedrooms away from the main entry and wet rooms grouped for buildability.",
                    "Best review path when livability and resale comfort are more important than maximum density.",
                ],
                compliance_findings=agent_input.warning_findings,
            ),
            DesignOption(
                option_id="schematic-space-utilization",
                name="Space Utilization Plan",
                strategy="space_utilization",
                target_building_sqft=efficient_sqft,
                units=spec.units,
                floor_plans=[
                    _space_utilization_plan(
                        spec=spec,
                        total_sqft=efficient_sqft,
                    )
                ],
                assumptions=[
                    "Prioritizes compact circulation, stacked wet areas, and flexible rooms.",
                    "Uses a tighter footprint to preserve site area for setbacks, trees, drainage, and parking.",
                    "Best review path when construction efficiency and entitlement flexibility matter most.",
                ],
                compliance_findings=agent_input.warning_findings,
            ),
        ]


def _comfort_plan(spec: UserBuildSpec, total_sqft: float) -> FloorPlan:
    bedrooms = max(1, min(spec.bedrooms or 3, 4))
    bathrooms = max(1, min(round(spec.bathrooms or 2), 3))
    rooms = [
        _room("porch", "Covered entry", "entry", total_sqft * 0.035, 0, 0, 16, 18),
        _room("living", "Living", "living", total_sqft * 0.18, 16, 0, 32, 32),
        _room("dining", "Dining", "living", total_sqft * 0.08, 48, 0, 18, 32),
        _room("kitchen", "Kitchen", "kitchen", total_sqft * 0.11, 66, 0, 20, 32),
        _room("utility", "Laundry / pantry", "service", total_sqft * 0.045, 86, 0, 14, 20),
        _room("hall", "Bedroom hall", "circulation", total_sqft * 0.07, 40, 32, 12, 68),
        _room("primary-bed", "Primary bedroom", "bedroom", total_sqft * 0.14, 52, 52, 28, 32),
        _room("primary-bath", "Primary bath", "bath", total_sqft * 0.06, 80, 52, 20, 18),
        _room("storage", "Storage", "service", total_sqft * 0.035, 80, 70, 20, 14),
    ]
    rooms.extend(
        _bedroom_group(
            bedrooms=bedrooms - 1,
            bathrooms=max(0, bathrooms - 1),
            total_sqft=total_sqft,
            start_y=32,
        )
    )
    if spec.units > 1:
        rooms.extend(
            [
                _room("adu-living", "ADU living / sleep", "unit", total_sqft * 0.12, 0, 70, 28, 30),
                _room("adu-kitchen", "ADU kitchenette", "kitchen", total_sqft * 0.035, 28, 70, 12, 15),
                _room("adu-bath", "ADU bath", "bath", total_sqft * 0.035, 28, 85, 12, 15),
            ]
        )

    return FloorPlan(
        plan_id="floor-plan-human-comfort",
        name="Human Comfort Ground Floor",
        level="Level 1",
        total_sqft=total_sqft,
        rooms=rooms,
        walls=_comfort_walls(),
        openings=_comfort_openings(),
        notes=[
            "Conceptual diagram uses standard adjacency logic: public rooms at entry, bedrooms buffered, wet rooms grouped.",
            "Exterior proportions, structural grid, egress, accessibility, MEP, and code compliance require professional design.",
        ],
    )


def _space_utilization_plan(spec: UserBuildSpec, total_sqft: float) -> FloorPlan:
    bedrooms = max(1, min(spec.bedrooms or 3, 4))
    bathrooms = max(1, min(round(spec.bathrooms or 2), 3))
    rooms = [
        _room("entry", "Entry / mudroom", "entry", total_sqft * 0.035, 0, 0, 14, 18),
        _room("great-room", "Great room", "living", total_sqft * 0.2, 14, 0, 38, 32),
        _room("kitchen", "Kitchen wall", "kitchen", total_sqft * 0.1, 52, 0, 24, 32),
        _room("wet-core", "Bath / laundry core", "bath", total_sqft * 0.09, 76, 0, 24, 32),
        _room("gallery", "Gallery hall", "circulation", total_sqft * 0.05, 0, 32, 100, 12),
        _room("primary-bed", "Primary bedroom", "bedroom", total_sqft * 0.12, 66, 44, 34, 28),
        _room("primary-bath", "Primary bath", "bath", total_sqft * 0.045, 66, 72, 17, 28),
        _room("flex", "Flex / office", "flex", total_sqft * 0.06, 83, 72, 17, 28),
    ]
    rooms.extend(_efficient_bedrooms(bedrooms - 1, bathrooms - 1, total_sqft))
    if spec.units > 1:
        rooms.extend(
            [
                _room("adu-studio", "ADU studio", "unit", total_sqft * 0.11, 0, 72, 28, 28),
                _room("adu-bath", "ADU wet room", "bath", total_sqft * 0.03, 28, 72, 12, 14),
                _room("adu-kitchen", "ADU galley", "kitchen", total_sqft * 0.03, 28, 86, 12, 14),
            ]
        )

    return FloorPlan(
        plan_id="floor-plan-space-utilization",
        name="Space Utilization Ground Floor",
        level="Level 1",
        total_sqft=total_sqft,
        rooms=rooms,
        walls=_efficient_walls(),
        openings=_efficient_openings(),
        notes=[
            "Conceptual diagram minimizes hallway area and stacks wet rooms to reduce cost and footprint.",
            "Tighter planning increases the need to verify room dimensions, egress, accessibility, structure, and utilities.",
        ],
    )


def _bedroom_group(
    bedrooms: int,
    bathrooms: int,
    total_sqft: float,
    start_y: float,
) -> list[FloorPlanRoom]:
    rooms: list[FloorPlanRoom] = []
    bedroom_slots = [(0, start_y, 20, 24), (20, start_y, 20, 24), (0, start_y + 24, 20, 22)]
    for index in range(min(bedrooms, len(bedroom_slots))):
        x, y, width, height = bedroom_slots[index]
        rooms.append(
            _room(
                f"bedroom-{index + 2}",
                f"Bedroom {index + 2}",
                "bedroom",
                total_sqft * 0.09,
                x,
                y,
                width,
                height,
            )
        )
    bath_slots = [(20, start_y + 24, 20, 16), (20, start_y + 40, 20, 14)]
    for index in range(min(bathrooms, len(bath_slots))):
        x, y, width, height = bath_slots[index]
        rooms.append(
            _room(
                f"bath-{index + 2}",
                f"Bath {index + 2}",
                "bath",
                total_sqft * 0.04,
                x,
                y,
                width,
                height,
            )
        )
    return rooms


def _efficient_bedrooms(
    bedrooms: int,
    bathrooms: int,
    total_sqft: float,
) -> list[FloorPlanRoom]:
    rooms: list[FloorPlanRoom] = []
    bedroom_slots = [(0, 44, 22, 28), (22, 44, 22, 28), (44, 44, 22, 28)]
    for index in range(min(bedrooms, len(bedroom_slots))):
        x, y, width, height = bedroom_slots[index]
        rooms.append(
            _room(
                f"bedroom-{index + 2}",
                f"Bedroom {index + 2}",
                "bedroom",
                total_sqft * 0.085,
                x,
                y,
                width,
                height,
            )
        )
    if bathrooms > 0:
        rooms.append(_room("shared-bath", "Shared bath", "bath", total_sqft * 0.04, 44, 72, 22, 28))
    return rooms


def _comfort_walls() -> list[FloorPlanWall]:
    return [
        _wall("north", 0, 0, 100, 0, "exterior"),
        _wall("east", 100, 0, 100, 100, "exterior"),
        _wall("south", 100, 100, 0, 100, "exterior"),
        _wall("west", 0, 100, 0, 0, "exterior"),
        _wall("public-private", 0, 32, 100, 32),
        _wall("bedroom-hall-west", 40, 32, 40, 100),
        _wall("bedroom-hall-east", 52, 32, 52, 100),
        _wall("kitchen-service", 86, 0, 86, 32),
        _wall("primary-suite", 80, 52, 80, 100),
    ]


def _comfort_openings() -> list[FloorPlanOpening]:
    return [
        _opening("front-door", 6, 0, 8, "horizontal", "door"),
        _opening("rear-door", 92, 100, 8, "horizontal", "door"),
        _opening("living-window", 24, 0, 16, "horizontal", "window"),
        _opening("bedroom-window", 8, 100, 14, "horizontal", "window"),
        _opening("primary-window", 60, 100, 16, "horizontal", "window"),
    ]


def _efficient_walls() -> list[FloorPlanWall]:
    return [
        _wall("north", 0, 0, 100, 0, "exterior"),
        _wall("east", 100, 0, 100, 100, "exterior"),
        _wall("south", 100, 100, 0, 100, "exterior"),
        _wall("west", 0, 100, 0, 0, "exterior"),
        _wall("public-private", 0, 32, 100, 32),
        _wall("gallery", 0, 44, 100, 44),
        _wall("wet-core", 76, 0, 76, 32),
        _wall("primary-suite", 66, 44, 66, 100),
        _wall("adu-separation", 40, 72, 40, 100),
    ]


def _efficient_openings() -> list[FloorPlanOpening]:
    return [
        _opening("front-door", 4, 0, 8, "horizontal", "door"),
        _opening("side-door", 0, 82, 10, "vertical", "door"),
        _opening("great-room-window", 22, 0, 18, "horizontal", "window"),
        _opening("kitchen-window", 58, 0, 12, "horizontal", "window"),
        _opening("primary-window", 78, 100, 16, "horizontal", "window"),
    ]


def _wall(
    wall_id: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    wall_type: str = "interior",
) -> FloorPlanWall:
    return FloorPlanWall(wall_id=wall_id, x1=x1, y1=y1, x2=x2, y2=y2, wall_type=wall_type)


def _opening(
    opening_id: str,
    x: float,
    y: float,
    width: float,
    orientation: str,
    opening_type: str,
) -> FloorPlanOpening:
    return FloorPlanOpening(
        opening_id=opening_id,
        x=x,
        y=y,
        width=width,
        orientation=orientation,
        opening_type=opening_type,
    )


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


def _scaled_sqft(target_building_sqft: float | None, factor: float) -> float:
    baseline = target_building_sqft or 1_800
    return max(400, round(baseline * factor))
