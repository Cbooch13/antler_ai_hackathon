from dataclasses import dataclass
import json
import math
import os
import secrets
from typing import Any
from xml.sax.saxutils import escape

from realestate_schemas import (
    ComplianceFinding,
    DesignOption,
    FloorPlan,
    FloorPlanOpening,
    FloorPlanRoom,
    FloorPlanWall,
    GeneratedVisualExport,
    UserBuildSpec,
)


SCHEMATIC_AGENT_SYSTEM_PROMPT = """
You are an early-stage residential schematic design agent for Austin infill projects.
Return architectural concepts as structured JSON only. Your job is to propose plans that
respect the requested program, preserve human livability, and explain design tradeoffs.

Rules:
- Produce exactly two options: human_comfort and space_utilization.
- Use the requested target building square footage for both options.
- Include reasonable room dimensions in feet and room areas that can reconcile to the target.
- Prefer public rooms with south/east daylight in Austin; reduce west glazing.
- Group kitchens, baths, laundry, and ADU wet rooms near wet-wall cores.
- Keep bedrooms more private than entry/living zones.
- Use multiple floors only when the program or lot constraints suggest it.
- Do not claim permit readiness or code approval.
"""


@dataclass(frozen=True)
class SchematicAgentInput:
    spec: UserBuildSpec
    warning_findings: list[ComplianceFinding]
    address: str | None = None
    neighborhood: str | None = None
    lot_sqft: float | None = None
    zoning: str | None = None


@dataclass(frozen=True)
class RoomLayout:
    room_id: str
    name: str
    category: str
    x: float
    y: float
    width: float
    height: float


class SchematicDesignAgent:
    """Generative schematic agent for concept-level architectural plans."""

    def __init__(self, rng: secrets.SystemRandom | None = None) -> None:
        self.rng = rng or secrets.SystemRandom()

    def generate(self, agent_input: SchematicAgentInput) -> list[DesignOption]:
        spec = agent_input.spec
        target_sqft = _target_sqft(spec)
        variant_id = secrets.token_hex(4)

        return [
            DesignOption(
                option_id=f"schematic-human-comfort-{variant_id}",
                name="Human Comfort Plan",
                strategy="human_comfort",
                target_building_sqft=target_sqft,
                units=spec.units,
                floor_plans=[
                    self._plan(
                        spec=spec,
                        strategy="human_comfort",
                        plan_id=f"floor-plan-human-comfort-{variant_id}",
                        name="Human Comfort Ground Floor",
                        total_sqft=target_sqft,
                        aspect_ratio=self.rng.uniform(1.42, 1.68),
                        layouts=self._comfort_layouts(spec),
                        notes=[
                            "Generated concept prioritizes daylight, generous public rooms, storage, and a legible public-to-private transition.",
                            "Room dimensions are rounded planning assumptions; architect review is required for measured drawings.",
                        ],
                    )
                ],
                assumptions=[
                    "Prioritizes comfort, daylight, room separation, storage, and a clear entry sequence.",
                    "Groups wet rooms for buildability while keeping bedrooms buffered from the main entry.",
                    "Uses the full requested building program; room areas are reconciled to the target square footage.",
                ],
                compliance_findings=agent_input.warning_findings,
            ),
            DesignOption(
                option_id=f"schematic-space-utilization-{variant_id}",
                name="Space Utilization Plan",
                strategy="space_utilization",
                target_building_sqft=target_sqft,
                units=spec.units,
                floor_plans=[
                    self._plan(
                        spec=spec,
                        strategy="space_utilization",
                        plan_id=f"floor-plan-space-utilization-{variant_id}",
                        name="Space Utilization Ground Floor",
                        total_sqft=target_sqft,
                        aspect_ratio=self.rng.uniform(1.55, 1.9),
                        layouts=self._space_utilization_layouts(spec),
                        notes=[
                            "Generated concept compresses circulation and stacks wet rooms to improve usable-area efficiency.",
                            "Tighter planning increases the need to verify egress, clearances, structure, and utilities.",
                        ],
                    )
                ],
                assumptions=[
                    "Optimizes usable program area through compact circulation and flexible rooms.",
                    "Keeps second-unit access legible while minimizing duplicated service area.",
                    "Uses the full requested building program; room areas are reconciled to the target square footage.",
                ],
                compliance_findings=agent_input.warning_findings,
            ),
        ]

    def _plan(
        self,
        spec: UserBuildSpec,
        strategy: str,
        plan_id: str,
        name: str,
        total_sqft: float,
        aspect_ratio: float,
        layouts: list[RoomLayout],
        notes: list[str],
    ) -> FloorPlan:
        footprint_width_ft = math.sqrt(total_sqft * aspect_ratio)
        footprint_depth_ft = total_sqft / footprint_width_ft
        rooms = _rooms_from_layouts(layouts, total_sqft, footprint_width_ft, footprint_depth_ft)
        sqft_delta = round(total_sqft - sum(room.estimated_sqft for room in rooms), 2)
        if rooms and abs(sqft_delta) >= 0.01:
            last = rooms[-1]
            rooms[-1] = last.model_copy(
                update={"estimated_sqft": max(35, round(last.estimated_sqft + sqft_delta, 2))}
            )
            sqft_delta = round(total_sqft - sum(room.estimated_sqft for room in rooms), 2)

        walls = _walls()
        openings = self._openings(strategy)
        scale_assumption = (
            f"Concept scale: 1 SVG plan unit = {footprint_width_ft / 100:.2f} ft horizontally "
            f"and {footprint_depth_ft / 100:.2f} ft vertically; dimensions rounded to 0.5 ft."
        )
        svg = _svg_export(
            title=name,
            total_sqft=total_sqft,
            width_ft=footprint_width_ft,
            depth_ft=footprint_depth_ft,
            rooms=rooms,
            walls=walls,
            openings=openings,
            scale_assumption=scale_assumption,
        )
        return FloorPlan(
            plan_id=plan_id,
            name=name,
            level="Level 1",
            total_sqft=total_sqft,
            footprint_width_ft=round(footprint_width_ft, 1),
            footprint_depth_ft=round(footprint_depth_ft, 1),
            scale_assumption=scale_assumption,
            sqft_delta=sqft_delta,
            rooms=rooms,
            walls=walls,
            openings=openings,
            visual_exports=[
                GeneratedVisualExport(
                    export_id=f"{plan_id}-svg",
                    label="Architectural concept SVG",
                    format="svg",
                    content=svg,
                    notes=[
                        "Generated SVG export is conceptual and suitable for product review only.",
                        "Not a permit drawing, measured CAD file, or professional architectural deliverable.",
                    ],
                )
            ],
            notes=notes
            + [
                f"Requested program: {spec.bedrooms or 'unspecified'} bedrooms, {spec.bathrooms or 'unspecified'} bathrooms, {spec.units} unit(s).",
                "Generated room areas reconcile to the total plan square footage; room geometry is conceptual.",
            ],
        )

    def _comfort_layouts(self, spec: UserBuildSpec) -> list[RoomLayout]:
        public_h = self.rng.uniform(32, 37)
        adu_h = self.rng.uniform(22, 28) if spec.units > 1 else 0
        private_h = 100 - public_h - adu_h
        bedrooms = max(1, min(spec.bedrooms or 3, 4))
        bathrooms = max(1, min(round(spec.bathrooms or 2), 3))
        rooms = [
            _layout("entry", "Covered entry", "entry", 0, 0, 13, public_h),
            _layout("living", "Living", "living", 13, 0, 31, public_h),
            _layout("dining", "Dining", "living", 44, 0, 17, public_h),
            _layout("kitchen", "Kitchen", "kitchen", 61, 0, 24, public_h),
            _layout("service", "Laundry / pantry", "service", 85, 0, 15, public_h),
            _layout("primary-bed", "Primary bedroom", "bedroom", 62, public_h, 24, private_h * 0.62),
            _layout("primary-bath", "Primary bath", "bath", 86, public_h, 14, private_h * 0.34),
            _layout("storage", "Storage", "service", 86, public_h + private_h * 0.34, 14, private_h * 0.28),
            _layout("hall", "Bedroom hall", "circulation", 36, public_h, 10, private_h),
            _layout("linen-mech", "Linen / mechanical", "service", 46, public_h, 16, private_h),
            _layout("primary-closet", "Primary closet / flex", "flex", 62, public_h + private_h * 0.62, 38, private_h * 0.38),
        ]
        main_secondary_baths = max(0, bathrooms - 1 - (1 if spec.units > 1 else 0))
        rooms.extend(_private_bed_bath_layouts(bedrooms - 1, main_secondary_baths, public_h, private_h))
        if spec.units > 1:
            rooms.extend(
                [
                    _layout("adu-living", "ADU living / sleep", "unit", 0, 100 - adu_h, 58, adu_h),
                    _layout("adu-kitchen", "ADU kitchenette", "kitchen", 58, 100 - adu_h, 22, adu_h),
                    _layout("adu-bath", "ADU bath", "bath", 80, 100 - adu_h, 20, adu_h),
                ]
            )
        else:
            rooms.append(_layout("flex", "Flex / office", "flex", 46, public_h + private_h * 0.62, 54, private_h * 0.38))
        return rooms

    def _space_utilization_layouts(self, spec: UserBuildSpec) -> list[RoomLayout]:
        public_h = self.rng.uniform(28, 33)
        gallery_h = self.rng.uniform(8, 11)
        adu_h = self.rng.uniform(24, 30) if spec.units > 1 else 0
        private_y = public_h + gallery_h
        private_h = 100 - private_y - adu_h
        bedrooms = max(1, min(spec.bedrooms or 3, 4))
        bathrooms = max(1, min(round(spec.bathrooms or 2), 3))
        rooms = [
            _layout("entry", "Entry / mudroom", "entry", 0, 0, 12, public_h),
            _layout("great-room", "Great room", "living", 12, 0, 41, public_h),
            _layout("kitchen", "Kitchen wall", "kitchen", 53, 0, 26, public_h),
            _layout("wet-core", "Bath / laundry core", "bath", 79, 0, 21, public_h),
            _layout("gallery", "Gallery hall", "circulation", 0, public_h, 100, gallery_h),
            _layout("primary-bed", "Primary bedroom", "bedroom", 66, private_y, 34, private_h * 0.7),
            _layout("primary-bath", "Primary bath", "bath", 66, private_y + private_h * 0.7, 17, private_h * 0.3),
            _layout("flex", "Flex / office", "flex", 83, private_y + private_h * 0.7, 17, private_h * 0.3),
            _layout("storage-core", "Storage / mechanical", "service", 0, private_y + private_h * 0.68, 44, private_h * 0.32),
        ]
        main_secondary_baths = max(0, bathrooms - 1 - (1 if spec.units > 1 else 0))
        rooms.extend(_efficient_bed_bath_layouts(bedrooms - 1, main_secondary_baths, private_y, private_h))
        if spec.units > 1:
            rooms.extend(
                [
                    _layout("adu-studio", "ADU studio", "unit", 0, 100 - adu_h, 58, adu_h),
                    _layout("adu-galley", "ADU galley", "kitchen", 58, 100 - adu_h, 21, adu_h),
                    _layout("adu-wet-room", "ADU wet room", "bath", 79, 100 - adu_h, 21, adu_h),
                ]
            )
        return rooms

    def _openings(self, strategy: str) -> list[FloorPlanOpening]:
        if strategy == "human_comfort":
            return [
                _opening("front-door", 5, 0, 8, "horizontal", "door"),
                _opening("rear-door", 92, 100, 8, "horizontal", "door"),
                _opening("living-window", 21, 0, 16, "horizontal", "window"),
                _opening("kitchen-window", 68, 0, 12, "horizontal", "window"),
                _opening("bedroom-window", 8, 100, 14, "horizontal", "window"),
                _opening("primary-window", 70, 100, 16, "horizontal", "window"),
            ]
        return [
            _opening("front-door", 4, 0, 8, "horizontal", "door"),
            _opening("side-door", 0, 84, 10, "vertical", "door"),
            _opening("great-room-window", 22, 0, 18, "horizontal", "window"),
            _opening("kitchen-window", 59, 0, 12, "horizontal", "window"),
            _opening("primary-window", 77, 100, 16, "horizontal", "window"),
        ]


class OpenAISchematicDesignAgent:
    """OpenAI-backed schematic agent with local validation and fallback."""

    def __init__(
        self,
        fallback_agent: SchematicDesignAgent | None = None,
        model: str | None = None,
    ) -> None:
        self.fallback_agent = fallback_agent or SchematicDesignAgent()
        self.model = model or os.getenv("OPENAI_SCHEMATIC_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.4"

    def generate(self, agent_input: SchematicAgentInput) -> list[DesignOption]:
        if not _llm_schematic_enabled() or not os.getenv("OPENAI_API_KEY"):
            return self.fallback_agent.generate(agent_input)

        try:
            return self._generate_with_openai(agent_input)
        except Exception:
            return self.fallback_agent.generate(agent_input)

    def _generate_with_openai(self, agent_input: SchematicAgentInput) -> list[DesignOption]:
        try:
            from openai import OpenAI
        except ImportError:
            return self.fallback_agent.generate(agent_input)

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SCHEMATIC_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": _llm_prompt(agent_input)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "schematic_design_response",
                    "schema": _llm_response_schema(),
                    "strict": True,
                }
            },
        )
        return _options_from_llm_payload(_extract_response_json(response), agent_input)


def _llm_schematic_enabled() -> bool:
    return os.getenv("LLM_SCHEMATIC_ENABLED", "").lower() in {"1", "true", "yes", "on"}


def _llm_prompt(agent_input: SchematicAgentInput) -> str:
    spec = agent_input.spec
    warnings = [
        {
            "code": finding.code,
            "title": finding.title,
            "status": finding.status.value,
            "summary": finding.summary,
        }
        for finding in agent_input.warning_findings
    ]
    payload = {
        "project": {
            "property_type": spec.property_type.value,
            "target_building_sqft": spec.target_building_sqft,
            "target_lot_sqft": spec.target_lot_sqft,
            "bedrooms": spec.bedrooms,
            "bathrooms": spec.bathrooms,
            "units": spec.units,
            "style_preferences": spec.style_preferences,
            "risk_tolerance": spec.risk_tolerance.value,
        },
        "property_context": {
            "address": agent_input.address,
            "neighborhood": agent_input.neighborhood,
            "lot_sqft": agent_input.lot_sqft,
            "zoning": agent_input.zoning,
            "orientation_assumption": "North is up until official parcel/street frontage geometry is joined.",
            "solar_context": "Austin, Texas: prioritize controlled south/east daylight and reduce unshaded west exposure.",
        },
        "compliance_findings": warnings,
    }
    return json.dumps(payload, indent=2)


def _llm_response_schema() -> dict[str, Any]:
    room = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "category", "width_ft", "depth_ft", "daylight_orientation", "adjacency_notes"],
        "properties": {
            "name": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["entry", "living", "kitchen", "service", "bedroom", "bath", "unit", "circulation", "flex"],
            },
            "width_ft": {"type": "number", "minimum": 3},
            "depth_ft": {"type": "number", "minimum": 3},
            "daylight_orientation": {"type": "string"},
            "adjacency_notes": {"type": "string"},
        },
    }
    floor = {
        "type": "object",
        "additionalProperties": False,
        "required": ["level", "rooms", "floor_notes"],
        "properties": {
            "level": {"type": "string"},
            "rooms": {"type": "array", "minItems": 3, "items": room},
            "floor_notes": {"type": "array", "items": {"type": "string"}},
        },
    }
    option = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "strategy", "concept", "solar_strategy", "floors", "assumptions"],
        "properties": {
            "name": {"type": "string"},
            "strategy": {"type": "string", "enum": ["human_comfort", "space_utilization"]},
            "concept": {"type": "string"},
            "solar_strategy": {"type": "string"},
            "floors": {"type": "array", "minItems": 1, "maxItems": 3, "items": floor},
            "assumptions": {"type": "array", "items": {"type": "string"}},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["options"],
        "properties": {
            "options": {"type": "array", "minItems": 2, "maxItems": 2, "items": option}
        },
    }


def _extract_response_json(response: Any) -> dict[str, Any]:
    text = getattr(response, "output_text", None)
    if text:
        return json.loads(text)

    output = getattr(response, "output", [])
    for item in output:
        for content in getattr(item, "content", []):
            content_text = getattr(content, "text", None)
            if content_text:
                return json.loads(content_text)
    raise ValueError("OpenAI response did not include JSON text")


def _options_from_llm_payload(
    payload: dict[str, Any],
    agent_input: SchematicAgentInput,
) -> list[DesignOption]:
    target_sqft = _target_sqft(agent_input.spec)
    variant_id = secrets.token_hex(4)
    options: list[DesignOption] = []
    for index, option_payload in enumerate(payload.get("options", [])):
        strategy = option_payload["strategy"]
        floors = option_payload["floors"]
        floor_plans = [
            _floor_from_llm(
                floor_payload=floor_payload,
                strategy=strategy,
                plan_id=f"floor-plan-{strategy}-{variant_id}-{floor_index + 1}",
                total_option_sqft=target_sqft,
                floor_count=len(floors),
                option_name=option_payload["name"],
                solar_strategy=option_payload["solar_strategy"],
            )
            for floor_index, floor_payload in enumerate(floors)
        ]
        options.append(
            DesignOption(
                option_id=f"schematic-{strategy}-{variant_id}-{index + 1}",
                name=option_payload["name"],
                strategy=strategy,
                target_building_sqft=target_sqft,
                units=agent_input.spec.units,
                floor_plans=floor_plans,
                assumptions=[
                    option_payload["concept"],
                    option_payload["solar_strategy"],
                    *option_payload["assumptions"],
                    "Generated by OpenAI structured output and validated through the local schematic contract.",
                ],
                compliance_findings=agent_input.warning_findings,
            )
        )

    if {option.strategy for option in options} != {"human_comfort", "space_utilization"}:
        raise ValueError("LLM did not return required schematic strategies")
    return options


def _floor_from_llm(
    floor_payload: dict[str, Any],
    strategy: str,
    plan_id: str,
    total_option_sqft: float,
    floor_count: int,
    option_name: str,
    solar_strategy: str,
) -> FloorPlan:
    floor_sqft = round(total_option_sqft / max(1, floor_count), 2)
    rooms = _rooms_from_llm_rooms(floor_payload["rooms"], floor_sqft)
    footprint_width_ft = max(sum(room.width_ft for room in rooms[:3]), math.sqrt(floor_sqft * 1.5))
    footprint_depth_ft = floor_sqft / footprint_width_ft
    rooms = _assign_llm_room_positions(rooms)
    sqft_delta = round(floor_sqft - sum(room.estimated_sqft for room in rooms), 2)
    if rooms and abs(sqft_delta) >= 0.01:
        rooms[-1] = rooms[-1].model_copy(
            update={"estimated_sqft": max(35, round(rooms[-1].estimated_sqft + sqft_delta, 2))}
        )
        sqft_delta = round(floor_sqft - sum(room.estimated_sqft for room in rooms), 2)
    scale_assumption = (
        f"OpenAI concept scale: 1 SVG plan unit = {footprint_width_ft / 100:.2f} ft horizontally "
        f"and {footprint_depth_ft / 100:.2f} ft vertically; room dimensions are model-proposed and rounded."
    )
    walls = _walls()
    openings = _openings_for_strategy(strategy)
    svg = _svg_export(
        title=f"{option_name} - {floor_payload['level']}",
        total_sqft=floor_sqft,
        width_ft=footprint_width_ft,
        depth_ft=footprint_depth_ft,
        rooms=rooms,
        walls=walls,
        openings=openings,
        scale_assumption=scale_assumption,
    )
    return FloorPlan(
        plan_id=plan_id,
        name=floor_payload["level"],
        level=floor_payload["level"],
        total_sqft=floor_sqft,
        footprint_width_ft=round(footprint_width_ft, 1),
        footprint_depth_ft=round(footprint_depth_ft, 1),
        scale_assumption=scale_assumption,
        sqft_delta=sqft_delta,
        rooms=rooms,
        walls=walls,
        openings=openings,
        visual_exports=[
            GeneratedVisualExport(
                export_id=f"{plan_id}-svg",
                label="OpenAI architectural concept SVG",
                format="svg",
                content=svg,
                notes=[
                    "Generated from OpenAI structured output and local SVG rendering.",
                    "Conceptual only; professional design review required.",
                ],
            )
        ],
        notes=[solar_strategy, *floor_payload["floor_notes"]],
    )


def _rooms_from_llm_rooms(
    rooms_payload: list[dict[str, Any]],
    floor_sqft: float,
) -> list[FloorPlanRoom]:
    rooms = [
        FloorPlanRoom(
            room_id=f"llm-room-{index + 1}",
            name=room["name"],
            category=room["category"],
            estimated_sqft=round(room["width_ft"] * room["depth_ft"], 2),
            width_ft=round(room["width_ft"] * 2) / 2,
            depth_ft=round(room["depth_ft"] * 2) / 2,
            x=0,
            y=0,
            width=10,
            height=10,
        )
        for index, room in enumerate(rooms_payload)
    ]
    total_area = sum(room.estimated_sqft for room in rooms)
    if total_area <= 0:
        raise ValueError("LLM rooms did not include positive area")
    scale_factor = floor_sqft / total_area
    return [
        room.model_copy(
            update={
                "estimated_sqft": round(room.estimated_sqft * scale_factor, 2),
                "width_ft": round(room.width_ft * math.sqrt(scale_factor) * 2) / 2,
                "depth_ft": round(room.depth_ft * math.sqrt(scale_factor) * 2) / 2,
            }
        )
        for room in rooms
    ]


def _assign_llm_room_positions(rooms: list[FloorPlanRoom]) -> list[FloorPlanRoom]:
    columns = 3
    rows = math.ceil(len(rooms) / columns)
    cell_width = 100 / columns
    cell_height = 100 / max(1, rows)
    positioned = []
    for index, room in enumerate(rooms):
        column = index % columns
        row = index // columns
        positioned.append(
            room.model_copy(
                update={
                    "x": round(column * cell_width, 2),
                    "y": round(row * cell_height, 2),
                    "width": round(cell_width, 2),
                    "height": round(cell_height, 2),
                }
            )
        )
    return positioned


def _openings_for_strategy(strategy: str) -> list[FloorPlanOpening]:
    if strategy == "human_comfort":
        return [
            _opening("front-door", 5, 0, 8, "horizontal", "door"),
            _opening("south-living-window", 20, 100, 18, "horizontal", "window"),
            _opening("east-bedroom-window", 100, 52, 14, "vertical", "window"),
            _opening("kitchen-window", 68, 0, 12, "horizontal", "window"),
        ]
    return [
        _opening("front-door", 4, 0, 8, "horizontal", "door"),
        _opening("side-door", 0, 84, 10, "vertical", "door"),
        _opening("great-room-window", 22, 0, 18, "horizontal", "window"),
        _opening("south-window-band", 50, 100, 18, "horizontal", "window"),
    ]


def _target_sqft(spec: UserBuildSpec) -> float:
    return max(400, round(spec.target_building_sqft or 1_800))


def _layout(
    room_id: str,
    name: str,
    category: str,
    x: float,
    y: float,
    width: float,
    height: float,
) -> RoomLayout:
    return RoomLayout(room_id=room_id, name=name, category=category, x=x, y=y, width=width, height=height)


def _private_bed_bath_layouts(
    bedrooms: int,
    bathrooms: int,
    y: float,
    height: float,
) -> list[RoomLayout]:
    layouts: list[RoomLayout] = []
    bedroom_slots = [(0, y, 18, height * 0.5), (18, y, 18, height * 0.5), (0, y + height * 0.5, 18, height * 0.5)]
    for index in range(min(bedrooms, len(bedroom_slots))):
        x, slot_y, width, slot_h = bedroom_slots[index]
        layouts.append(_layout(f"bedroom-{index + 2}", f"Bedroom {index + 2}", "bedroom", x, slot_y, width, slot_h))
    bath_slots = [(18, y + height * 0.5, 18, height * 0.28), (18, y + height * 0.78, 18, height * 0.22)]
    for index in range(min(bathrooms, len(bath_slots))):
        x, slot_y, width, slot_h = bath_slots[index]
        layouts.append(_layout(f"bath-{index + 2}", f"Bath {index + 2}", "bath", x, slot_y, width, slot_h))
    for index in range(min(bathrooms, len(bath_slots)), len(bath_slots)):
        x, slot_y, width, slot_h = bath_slots[index]
        layouts.append(
            _layout(
                f"secondary-storage-{index + 1}",
                "Secondary storage",
                "service",
                x,
                slot_y,
                width,
                slot_h,
            )
        )
    return layouts


def _efficient_bed_bath_layouts(
    bedrooms: int,
    bathrooms: int,
    y: float,
    height: float,
) -> list[RoomLayout]:
    layouts: list[RoomLayout] = []
    bed_width = 66 / max(1, min(bedrooms, 3))
    for index in range(min(bedrooms, 3)):
        layouts.append(
            _layout(
                f"bedroom-{index + 2}",
                f"Bedroom {index + 2}",
                "bedroom",
                index * bed_width,
                y,
                bed_width,
                height * 0.68,
            )
        )
    if bathrooms > 0:
        layouts.append(_layout("shared-bath", "Shared bath", "bath", 44, y + height * 0.68, 22, height * 0.32))
    else:
        layouts.append(
            _layout("shared-storage", "Shared storage", "service", 44, y + height * 0.68, 22, height * 0.32)
        )
    return layouts


def _rooms_from_layouts(
    layouts: list[RoomLayout],
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
) -> list[FloorPlanRoom]:
    rooms: list[FloorPlanRoom] = []
    for layout in layouts:
        width_ft = footprint_width_ft * layout.width / 100
        depth_ft = footprint_depth_ft * layout.height / 100
        estimated_sqft = total_sqft * (layout.width * layout.height / 10_000)
        rooms.append(
            FloorPlanRoom(
                room_id=layout.room_id,
                name=layout.name,
                category=layout.category,
                estimated_sqft=round(estimated_sqft, 2),
                width_ft=round(width_ft * 2) / 2,
                depth_ft=round(depth_ft * 2) / 2,
                x=round(layout.x, 2),
                y=round(layout.y, 2),
                width=round(layout.width, 2),
                height=round(layout.height, 2),
            )
        )
    return rooms


def _walls() -> list[FloorPlanWall]:
    return [
        _wall("north", 0, 0, 100, 0, "exterior"),
        _wall("east", 100, 0, 100, 100, "exterior"),
        _wall("south", 100, 100, 0, 100, "exterior"),
        _wall("west", 0, 100, 0, 0, "exterior"),
        _wall("public-private", 0, 34, 100, 34),
        _wall("service-core", 79, 0, 79, 100),
        _wall("unit-separation", 0, 74, 100, 74),
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


def _svg_export(
    title: str,
    total_sqft: float,
    width_ft: float,
    depth_ft: float,
    rooms: list[FloorPlanRoom],
    walls: list[FloorPlanWall],
    openings: list[FloorPlanOpening],
    scale_assumption: str,
) -> str:
    scale = 8
    svg_width = 100 * scale
    svg_height = 118 * scale
    room_markup = "\n".join(_svg_room(room, scale) for room in rooms)
    wall_markup = "\n".join(_svg_wall(wall, scale) for wall in walls)
    opening_markup = "\n".join(_svg_opening(opening, scale) for opening in openings)
    escaped_title = escape(title)
    escaped_scale = escape(scale_assumption)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" role="img" aria-label="{escaped_title}">
  <style>
    .label {{ font: 12px Arial, sans-serif; fill: #1f2933; font-weight: 700; }}
    .small {{ font: 10px Arial, sans-serif; fill: #5c6a70; }}
    .room {{ stroke: #47545a; stroke-width: 1; }}
    .living {{ fill: #d8eadf; }}
    .entry {{ fill: #d8eadf; }}
    .kitchen {{ fill: #e9dfc7; }}
    .service {{ fill: #e9dfc7; }}
    .bedroom {{ fill: #dbe4ef; }}
    .flex {{ fill: #dbe4ef; }}
    .bath {{ fill: #e8d7dc; }}
    .unit {{ fill: #d8e7e8; }}
    .circulation {{ fill: #d8e7e8; }}
    .wall {{ stroke: #25363d; stroke-linecap: square; }}
    .exterior {{ stroke-width: 5; }}
    .interior {{ stroke-width: 2; }}
    .opening {{ fill: #ffffff; stroke: #255f5a; stroke-width: 1; }}
  </style>
  <rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="#f5f4ee"/>
  <text x="16" y="24" class="label">{escaped_title}</text>
  <text x="16" y="42" class="small">{round(total_sqft):,} sqft | {round(width_ft, 1)} ft x {round(depth_ft, 1)} ft footprint</text>
  <text x="16" y="58" class="small">{escaped_scale}</text>
  <g transform="translate(0 100)">
    {room_markup}
    {wall_markup}
    {opening_markup}
  </g>
</svg>"""


def _svg_room(room: FloorPlanRoom, scale: int) -> str:
    x = room.x * scale
    y = room.y * scale
    width = room.width * scale
    height = room.height * scale
    label_y = y + min(height / 2, 26)
    return (
        f'<g><rect class="room {escape(room.category)}" x="{x:.1f}" y="{y:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}" rx="2"/>'
        f'<text class="label" x="{x + width / 2:.1f}" y="{label_y:.1f}" text-anchor="middle">{escape(room.name)}</text>'
        f'<text class="small" x="{x + width / 2:.1f}" y="{label_y + 14:.1f}" text-anchor="middle">{round(room.width_ft, 1)} ft x {round(room.depth_ft, 1)} ft</text>'
        f'<text class="small" x="{x + width / 2:.1f}" y="{label_y + 27:.1f}" text-anchor="middle">{round(room.estimated_sqft):,} sf</text></g>'
    )


def _svg_wall(wall: FloorPlanWall, scale: int) -> str:
    return (
        f'<line class="wall {escape(wall.wall_type)}" x1="{wall.x1 * scale:.1f}" '
        f'y1="{wall.y1 * scale:.1f}" x2="{wall.x2 * scale:.1f}" y2="{wall.y2 * scale:.1f}"/>'
    )


def _svg_opening(opening: FloorPlanOpening, scale: int) -> str:
    width = opening.width * scale if opening.orientation == "horizontal" else 10
    height = 10 if opening.orientation == "horizontal" else opening.width * scale
    return (
        f'<rect class="opening" x="{opening.x * scale:.1f}" y="{opening.y * scale:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}"/>'
    )
