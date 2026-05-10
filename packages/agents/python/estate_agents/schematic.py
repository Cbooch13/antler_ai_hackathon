from dataclasses import dataclass
import json
import math
import os
import secrets
from typing import Any, Callable
from xml.sax.saxutils import escape

from realestate_schemas import (
    ComplianceFinding,
    DesignOption,
    FindingStatus,
    FloorPlan,
    FloorPlanConnection,
    FloorPlanOpening,
    FloorPlanQualityCheck,
    FloorPlanQualityReport,
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
- Produce exactly one option with strategy human_comfort.
- Use the requested target building square footage for the option.
- Include reasonable room dimensions in feet and room areas that can reconcile to the target.
- Prefer public rooms with south/east daylight in Austin; reduce west glazing.
- Group kitchens, baths, laundry, and ADU wet rooms near wet-wall cores.
- Keep bedrooms more private than entry/living zones.
- Use multiple floors only when the program or lot constraints suggest it.
- When revision feedback is provided, correct failed checks before improving warnings.
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
                name="Primary Feasibility Plan",
                strategy="human_comfort",
                target_building_sqft=target_sqft,
                units=spec.units,
                floor_plans=[
                    self._plan(
                        spec=spec,
                        strategy="human_comfort",
                        plan_id=f"floor-plan-human-comfort-{variant_id}",
                        name="Primary Feasibility Floor Plan",
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
                    "Returns one primary plan while schematic quality thresholds are being tightened.",
                    "Prioritizes comfort, daylight, room separation, storage, and a clear entry sequence.",
                    "Groups wet rooms for buildability while keeping bedrooms buffered from the main entry.",
                    "Uses the full requested building program; room areas are reconciled to the target square footage.",
                ],
                compliance_findings=agent_input.warning_findings,
            )
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

        walls = _walls_from_rooms(rooms)
        connections = _connections_from_rooms(rooms)
        openings = self._openings(strategy)
        quality_report = _quality_report(
            rooms=rooms,
            walls=walls,
            openings=openings,
            connections=connections,
            total_sqft=total_sqft,
            footprint_width_ft=footprint_width_ft,
            footprint_depth_ft=footprint_depth_ft,
            sqft_delta=sqft_delta,
            spec=spec,
            strategy=strategy,
        )
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
            connections=connections,
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
            connections=connections,
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
            quality_report=quality_report,
            notes=notes
            + [
                f"Requested program: {spec.bedrooms or 'unspecified'} bedrooms, {spec.bathrooms or 'unspecified'} bathrooms, {spec.units} unit(s).",
                "Generated room areas reconcile to the total plan square footage; room geometry is conceptual.",
            ],
        )

    def _comfort_layouts(self, spec: UserBuildSpec) -> list[RoomLayout]:
        public_h = 32
        adu_h = 22 if spec.units > 1 else 0
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
        client_factory: Callable[[], Any] | None = None,
        max_attempts: int | None = None,
    ) -> None:
        self.fallback_agent = fallback_agent or SchematicDesignAgent()
        self.model = model or os.getenv("OPENAI_SCHEMATIC_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.4"
        self.client_factory = client_factory
        self.max_attempts = max_attempts or _llm_schematic_max_attempts()

    def generate(self, agent_input: SchematicAgentInput) -> list[DesignOption]:
        if not _llm_schematic_enabled() or not os.getenv("OPENAI_API_KEY"):
            return self.fallback_agent.generate(agent_input)

        try:
            return self._generate_with_openai(agent_input)
        except Exception:
            return self.fallback_agent.generate(agent_input)

    def _generate_with_openai(self, agent_input: SchematicAgentInput) -> list[DesignOption]:
        client = self._openai_client()
        best_options: list[DesignOption] | None = None
        best_score = -1.0
        revision_feedback: list[dict[str, Any]] = []

        for attempt in range(1, self.max_attempts + 1):
            response = client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": SCHEMATIC_AGENT_SYSTEM_PROMPT},
                    {"role": "user", "content": _llm_prompt(agent_input, revision_feedback)},
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
            options = _options_from_llm_payload(_extract_response_json(response), agent_input)
            score = _average_quality_score(options)
            passed = _options_pass_quality(options)
            _annotate_revision_loop(options, attempt, self.max_attempts, passed)
            if score > best_score:
                best_options = options
                best_score = score
            if passed:
                return options
            revision_feedback = _quality_feedback(options)

        if best_options is None:
            raise ValueError("OpenAI schematic generation did not return any options")
        _annotate_best_available(best_options, self.max_attempts)
        return best_options

    def _openai_client(self) -> Any:
        if self.client_factory is not None:
            return self.client_factory()

        try:
            from openai import OpenAI
        except ImportError:
            raise

        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _llm_schematic_enabled() -> bool:
    return os.getenv("LLM_SCHEMATIC_ENABLED", "").lower() in {"1", "true", "yes", "on"}


def _llm_schematic_max_attempts() -> int:
    try:
        return max(1, min(5, int(os.getenv("LLM_SCHEMATIC_MAX_ATTEMPTS", "3"))))
    except ValueError:
        return 3


def _llm_prompt(
    agent_input: SchematicAgentInput,
    revision_feedback: list[dict[str, Any]] | None = None,
) -> str:
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
        "revision_feedback": revision_feedback or [],
        "revision_instruction": (
            "If revision_feedback is present, revise the plan JSON to resolve every failing check first, "
            "then reduce warnings while preserving the user's requested program and total square footage."
        ),
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
            "strategy": {"type": "string", "enum": ["human_comfort"]},
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
            "options": {"type": "array", "minItems": 1, "maxItems": 1, "items": option}
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
                spec=agent_input.spec,
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

    if [option.strategy for option in options] != ["human_comfort"]:
        raise ValueError("LLM did not return the required primary schematic strategy")
    return options


def _average_quality_score(options: list[DesignOption]) -> float:
    reports = [plan.quality_report for option in options for plan in option.floor_plans]
    if not reports:
        return 0
    return sum(report.score for report in reports) / len(reports)


def _options_pass_quality(options: list[DesignOption]) -> bool:
    reports = [plan.quality_report for option in options for plan in option.floor_plans]
    critical_codes = {
        "area_reconciliation",
        "footprint_area",
        "room_bounds",
        "room_overlap",
        "program_fit",
        "room_dimensions",
        "path_connectivity",
    }
    return bool(reports) and all(
        report.score >= 85
        and all(
            check.status == FindingStatus.PASSES
            for check in report.checks
            if check.code in critical_codes
        )
        for report in reports
    )


def _quality_feedback(options: list[DesignOption]) -> list[dict[str, Any]]:
    feedback: list[dict[str, Any]] = []
    for option in options:
        for plan in option.floor_plans:
            actionable_checks = [
                {
                    "code": check.code,
                    "label": check.label,
                    "status": check.status.value,
                    "summary": check.summary,
                }
                for check in plan.quality_report.checks
                if check.status in {FindingStatus.FAILS, FindingStatus.WARNING}
            ]
            if actionable_checks:
                feedback.append(
                    {
                        "option": option.strategy,
                        "plan": plan.name,
                        "quality_score": plan.quality_report.score,
                        "quality_status": plan.quality_report.status.value,
                        "checks_to_fix": actionable_checks,
                    }
                )
    return feedback


def _annotate_revision_loop(
    options: list[DesignOption],
    attempt: int,
    max_attempts: int,
    passed: bool,
) -> None:
    status = "accepted" if passed else "needs another revision"
    for option in options:
        option.assumptions.append(
            f"OpenAI revision loop attempt {attempt} of {max_attempts}: deterministic quality checker {status}."
        )


def _annotate_best_available(options: list[DesignOption], max_attempts: int) -> None:
    for option in options:
        option.assumptions.append(
            f"Returned best available OpenAI plan after {max_attempts} revision attempts; unresolved quality warnings remain advisory."
        )


def _floor_from_llm(
    floor_payload: dict[str, Any],
    strategy: str,
    plan_id: str,
    total_option_sqft: float,
    floor_count: int,
    option_name: str,
    solar_strategy: str,
    spec: UserBuildSpec,
) -> FloorPlan:
    floor_sqft = round(total_option_sqft / max(1, floor_count), 2)
    rooms = _rooms_from_llm_rooms(floor_payload["rooms"], floor_sqft)
    footprint_width_ft = max(sum(room.width_ft for room in rooms[:3]), math.sqrt(floor_sqft * 1.5))
    footprint_depth_ft = floor_sqft / footprint_width_ft
    rooms = _refine_llm_room_geometry(
        rooms=rooms,
        total_sqft=floor_sqft,
        footprint_width_ft=footprint_width_ft,
        footprint_depth_ft=footprint_depth_ft,
    )
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
    walls = _walls_from_rooms(rooms)
    connections = _connections_from_rooms(rooms)
    openings = _openings_for_strategy(strategy)
    quality_report = _quality_report(
        rooms=rooms,
        walls=walls,
        openings=openings,
        connections=connections,
        total_sqft=floor_sqft,
        footprint_width_ft=footprint_width_ft,
        footprint_depth_ft=footprint_depth_ft,
        sqft_delta=sqft_delta,
        spec=spec,
        strategy=strategy,
    )
    svg = _svg_export(
        title=f"{option_name} - {floor_payload['level']}",
        total_sqft=floor_sqft,
        width_ft=footprint_width_ft,
        depth_ft=footprint_depth_ft,
        rooms=rooms,
        walls=walls,
        openings=openings,
        connections=connections,
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
        connections=connections,
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
        quality_report=quality_report,
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


def _refine_llm_room_geometry(
    rooms: list[FloorPlanRoom],
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
) -> list[FloorPlanRoom]:
    unit_rooms = [room for room in rooms if _is_unit_room(room)]
    wet_rooms = [
        room
        for room in rooms
        if room not in unit_rooms and room.category in {"bath", "service"}
    ]
    circulation_rooms = [
        room
        for room in rooms
        if room not in unit_rooms and room not in wet_rooms and room.category == "circulation"
    ]
    public_rooms = [
        room
        for room in rooms
        if room not in unit_rooms and room not in wet_rooms and room not in circulation_rooms and room.category in {"entry", "living", "kitchen"}
    ]
    private_rooms = [
        room
        for room in rooms
        if room not in unit_rooms and room not in wet_rooms and room not in circulation_rooms and room not in public_rooms
    ]

    unit_h = 24 if unit_rooms else 0
    public_h = 32 if public_rooms else 0
    hall_h = 12 if circulation_rooms else 0
    private_h = max(0, 100 - unit_h - public_h - hall_h)
    main_w = 78 if wet_rooms else 100
    refined: list[FloorPlanRoom] = []

    if public_rooms:
        refined.extend(
            _position_row(
                public_rooms,
                x=0,
                y=0,
                width=main_w,
                height=public_h,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
    if circulation_rooms:
        refined.extend(
            _position_row(
                circulation_rooms,
                x=0,
                y=public_h,
                width=main_w,
                height=hall_h,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
    if private_rooms:
        refined.extend(
            _position_grid(
                private_rooms,
                x=0,
                y=public_h + hall_h,
                width=main_w,
                height=private_h,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
    if wet_rooms:
        refined.extend(
            _position_column(
                wet_rooms,
                x=main_w,
                y=0,
                width=100 - main_w,
                height=100 - unit_h,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
    if unit_rooms:
        refined.extend(
            _position_row(
                unit_rooms,
                x=0,
                y=100 - unit_h,
                width=100,
                height=unit_h,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )

    room_by_id = {room.room_id: room for room in refined}
    return [room_by_id.get(room.room_id, room) for room in rooms]


def _is_unit_room(room: FloorPlanRoom) -> bool:
    label = f"{room.room_id} {room.name}".lower()
    return room.category == "unit" or "adu" in label or "second unit" in label


def _position_row(
    rooms: list[FloorPlanRoom],
    x: float,
    y: float,
    width: float,
    height: float,
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
) -> list[FloorPlanRoom]:
    total_area = sum(room.estimated_sqft for room in rooms) or len(rooms)
    cursor = x
    positioned: list[FloorPlanRoom] = []
    for index, room in enumerate(rooms):
        if index == len(rooms) - 1:
            room_width = x + width - cursor
        else:
            room_width = width * room.estimated_sqft / total_area
        positioned.append(
            _room_with_geometry(
                room=room,
                x=cursor,
                y=y,
                width=room_width,
                height=height,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
        cursor += room_width
    return positioned


def _position_column(
    rooms: list[FloorPlanRoom],
    x: float,
    y: float,
    width: float,
    height: float,
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
) -> list[FloorPlanRoom]:
    total_area = sum(room.estimated_sqft for room in rooms) or len(rooms)
    cursor = y
    positioned: list[FloorPlanRoom] = []
    for index, room in enumerate(rooms):
        if index == len(rooms) - 1:
            room_height = y + height - cursor
        else:
            room_height = height * room.estimated_sqft / total_area
        positioned.append(
            _room_with_geometry(
                room=room,
                x=x,
                y=cursor,
                width=width,
                height=room_height,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
        cursor += room_height
    return positioned


def _position_grid(
    rooms: list[FloorPlanRoom],
    x: float,
    y: float,
    width: float,
    height: float,
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
) -> list[FloorPlanRoom]:
    if not rooms:
        return []
    rows = 2 if len(rooms) > 2 and height >= 24 else 1
    row_height = height / rows
    positioned: list[FloorPlanRoom] = []
    for row_index in range(rows):
        row_rooms = rooms[row_index::rows]
        positioned.extend(
            _position_row(
                row_rooms,
                x=x,
                y=y + row_index * row_height,
                width=width,
                height=row_height,
                total_sqft=total_sqft,
                footprint_width_ft=footprint_width_ft,
                footprint_depth_ft=footprint_depth_ft,
            )
        )
    return positioned


def _room_with_geometry(
    room: FloorPlanRoom,
    x: float,
    y: float,
    width: float,
    height: float,
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
) -> FloorPlanRoom:
    bounded_width = max(1, min(100 - x, width))
    bounded_height = max(1, min(100 - y, height))
    estimated_sqft = total_sqft * (bounded_width * bounded_height / 10_000)
    return room.model_copy(
        update={
            "estimated_sqft": round(estimated_sqft, 2),
            "width_ft": round(footprint_width_ft * bounded_width / 100 * 2) / 2,
            "depth_ft": round(footprint_depth_ft * bounded_height / 100 * 2) / 2,
            "x": round(x, 2),
            "y": round(y, 2),
            "width": round(bounded_width, 2),
            "height": round(bounded_height, 2),
        }
    )


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


def _connections_from_rooms(rooms: list[FloorPlanRoom]) -> list[FloorPlanConnection]:
    direct = _direct_room_connections(rooms)
    by_room: dict[str, list[FloorPlanConnection]] = {room.room_id: [] for room in rooms}
    for connection in direct:
        by_room[connection.from_room_id].append(connection)
        by_room[connection.to_room_id].append(connection)

    hub = _connection_hub_room(rooms)
    if hub is None:
        return direct

    connections = list(direct)
    connected_ids = _reachable_room_ids(hub.room_id, connections)
    for room in rooms:
        if room.room_id == hub.room_id or room.room_id in connected_ids:
            continue
        nearest = _nearest_connected_room(room, [candidate for candidate in rooms if candidate.room_id in connected_ids])
        if nearest is None:
            continue
        fallback = _fallback_connection(room, nearest, len(connections) + 1)
        connections.append(fallback)
        connected_ids = _reachable_room_ids(hub.room_id, connections)
    return connections


def _direct_room_connections(rooms: list[FloorPlanRoom]) -> list[FloorPlanConnection]:
    connections: list[FloorPlanConnection] = []
    for index, first in enumerate(rooms):
        for second in rooms[index + 1 :]:
            connection = _shared_boundary_connection(first, second, len(connections) + 1)
            if connection is not None:
                connections.append(connection)
    return connections


def _shared_boundary_connection(
    first: FloorPlanRoom,
    second: FloorPlanRoom,
    index: int,
) -> FloorPlanConnection | None:
    tolerance = 0.2
    first_right = first.x + first.width
    second_right = second.x + second.width
    first_bottom = first.y + first.height
    second_bottom = second.y + second.height

    if abs(first_right - second.x) <= tolerance or abs(second_right - first.x) <= tolerance:
        boundary_x = first_right if abs(first_right - second.x) <= tolerance else second_right
        overlap_start = max(first.y, second.y)
        overlap_end = min(first_bottom, second_bottom)
        overlap = overlap_end - overlap_start
        if overlap >= 3:
            return _connection(
                index=index,
                first=first,
                second=second,
                x=boundary_x,
                y=overlap_start + overlap / 2,
                width=min(8, max(3, overlap * 0.5)),
                orientation="vertical",
            )

    if abs(first_bottom - second.y) <= tolerance or abs(second_bottom - first.y) <= tolerance:
        boundary_y = first_bottom if abs(first_bottom - second.y) <= tolerance else second_bottom
        overlap_start = max(first.x, second.x)
        overlap_end = min(first_right, second_right)
        overlap = overlap_end - overlap_start
        if overlap >= 3:
            return _connection(
                index=index,
                first=first,
                second=second,
                x=overlap_start + overlap / 2,
                y=boundary_y,
                width=min(8, max(3, overlap * 0.5)),
                orientation="horizontal",
            )
    return None


def _connection(
    index: int,
    first: FloorPlanRoom,
    second: FloorPlanRoom,
    x: float,
    y: float,
    width: float,
    orientation: str,
) -> FloorPlanConnection:
    return FloorPlanConnection(
        connection_id=f"connection-{index}",
        from_room_id=first.room_id,
        to_room_id=second.room_id,
        connection_type=_connection_type(first, second),
        x=round(max(0, min(100, x)), 2),
        y=round(max(0, min(100, y)), 2),
        width=round(max(2.5, min(100, width)), 2),
        orientation=orientation,
    )


def _connection_type(first: FloorPlanRoom, second: FloorPlanRoom) -> str:
    categories = {first.category, second.category}
    if "unit" in categories:
        return "unit_entry"
    if categories <= {"entry", "living", "kitchen", "circulation"}:
        return "wide_opening"
    return "door"


def _connection_hub_room(rooms: list[FloorPlanRoom]) -> FloorPlanRoom | None:
    for category in ("entry", "circulation", "living", "kitchen"):
        for room in rooms:
            if room.category == category:
                return room
    return rooms[0] if rooms else None


def _reachable_room_ids(start_room_id: str, connections: list[FloorPlanConnection]) -> set[str]:
    adjacency: dict[str, set[str]] = {}
    for connection in connections:
        adjacency.setdefault(connection.from_room_id, set()).add(connection.to_room_id)
        adjacency.setdefault(connection.to_room_id, set()).add(connection.from_room_id)
    seen = {start_room_id}
    frontier = [start_room_id]
    while frontier:
        current = frontier.pop()
        for next_room in adjacency.get(current, set()):
            if next_room not in seen:
                seen.add(next_room)
                frontier.append(next_room)
    return seen


def _nearest_connected_room(
    room: FloorPlanRoom,
    candidates: list[FloorPlanRoom],
) -> FloorPlanRoom | None:
    if not candidates:
        return None
    room_center = _room_center(room)
    return min(candidates, key=lambda candidate: _distance(room_center, _room_center(candidate)))


def _fallback_connection(
    room: FloorPlanRoom,
    connected_room: FloorPlanRoom,
    index: int,
) -> FloorPlanConnection:
    room_center = _room_center(room)
    connected_center = _room_center(connected_room)
    if abs(room_center[0] - connected_center[0]) > abs(room_center[1] - connected_center[1]):
        x = room.x if room_center[0] > connected_center[0] else room.x + room.width
        return _connection(index, room, connected_room, x, room_center[1], 3.2, "vertical")
    y = room.y if room_center[1] > connected_center[1] else room.y + room.height
    return _connection(index, room, connected_room, room_center[0], y, 3.2, "horizontal")


def _room_center(room: FloorPlanRoom) -> tuple[float, float]:
    return (room.x + room.width / 2, room.y + room.height / 2)


def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return math.sqrt((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2)


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


def _quality_report(
    rooms: list[FloorPlanRoom],
    walls: list[FloorPlanWall],
    openings: list[FloorPlanOpening],
    connections: list[FloorPlanConnection],
    total_sqft: float,
    footprint_width_ft: float,
    footprint_depth_ft: float,
    sqft_delta: float,
    spec: UserBuildSpec,
    strategy: str,
) -> FloorPlanQualityReport:
    checks = [
        _area_reconciliation_check(total_sqft, sqft_delta),
        _footprint_check(total_sqft, footprint_width_ft, footprint_depth_ft),
        _room_bounds_check(rooms),
        _room_overlap_check(rooms),
        _room_program_check(rooms, spec),
        _room_dimension_check(rooms),
        _circulation_check(rooms),
        _path_connectivity_check(rooms, connections),
        _opening_check(openings),
        _unit_separation_check(rooms, walls, spec),
        _solar_check(openings, strategy),
    ]
    score = 100
    for check in checks:
        if check.status == FindingStatus.FAILS:
            score -= 28
        elif check.status == FindingStatus.WARNING:
            score -= 10
        elif check.status == FindingStatus.UNKNOWN:
            score -= 5

    if any(check.status == FindingStatus.FAILS for check in checks):
        status = FindingStatus.FAILS
    elif any(check.status in {FindingStatus.WARNING, FindingStatus.UNKNOWN} for check in checks):
        status = FindingStatus.WARNING
    else:
        status = FindingStatus.PASSES

    return FloorPlanQualityReport(
        score=max(0, min(100, score)),
        status=status,
        checks=checks,
        review_notes=[
            "Quality checks are deterministic MVP heuristics for product review, not professional architectural validation.",
            "Stage 6H uses this report with the OpenAI revision loop and structured geometry refiner.",
        ],
    )


def _quality_check(
    code: str,
    label: str,
    status: FindingStatus,
    summary: str,
) -> FloorPlanQualityCheck:
    return FloorPlanQualityCheck(code=code, label=label, status=status, summary=summary)


def _area_reconciliation_check(total_sqft: float, sqft_delta: float) -> FloorPlanQualityCheck:
    abs_delta = abs(sqft_delta)
    if abs_delta <= 0.5:
        status = FindingStatus.PASSES
        summary = "Room areas reconcile to the target floor-plan square footage."
    elif abs_delta <= max(10, total_sqft * 0.01):
        status = FindingStatus.WARNING
        summary = f"Room areas are within 1% of target, with {sqft_delta:.2f} sqft delta."
    else:
        status = FindingStatus.FAILS
        summary = f"Room areas miss the target by {sqft_delta:.2f} sqft."
    return _quality_check("area_reconciliation", "Area reconciliation", status, summary)


def _footprint_check(total_sqft: float, width_ft: float, depth_ft: float) -> FloorPlanQualityCheck:
    footprint_area = width_ft * depth_ft
    delta_ratio = abs(footprint_area - total_sqft) / total_sqft
    aspect_ratio = max(width_ft, depth_ft) / min(width_ft, depth_ft)
    if delta_ratio > 0.03:
        return _quality_check(
            "footprint_area",
            "Footprint area",
            FindingStatus.FAILS,
            "Footprint dimensions do not reconcile to the stated floor-plan square footage.",
        )
    if aspect_ratio > 3.2:
        return _quality_check(
            "footprint_area",
            "Footprint area",
            FindingStatus.WARNING,
            "Footprint area reconciles, but the overall plan is unusually elongated.",
        )
    return _quality_check(
        "footprint_area",
        "Footprint area",
        FindingStatus.PASSES,
        "Footprint dimensions reconcile to the stated floor-plan square footage.",
    )


def _room_bounds_check(rooms: list[FloorPlanRoom]) -> FloorPlanQualityCheck:
    out_of_bounds = [
        room.name
        for room in rooms
        if room.x < 0 or room.y < 0 or room.x + room.width > 100.25 or room.y + room.height > 100.25
    ]
    if out_of_bounds:
        return _quality_check(
            "room_bounds",
            "Room bounds",
            FindingStatus.FAILS,
            f"Rooms extend outside the normalized footprint: {', '.join(out_of_bounds[:4])}.",
        )
    return _quality_check(
        "room_bounds",
        "Room bounds",
        FindingStatus.PASSES,
        "All rooms fit inside the normalized floor-plan footprint.",
    )


def _room_overlap_check(rooms: list[FloorPlanRoom]) -> FloorPlanQualityCheck:
    overlap_pairs: list[str] = []
    overlap_area = 0.0
    for index, first in enumerate(rooms):
        for second in rooms[index + 1 :]:
            x_overlap = max(0, min(first.x + first.width, second.x + second.width) - max(first.x, second.x))
            y_overlap = max(0, min(first.y + first.height, second.y + second.height) - max(first.y, second.y))
            pair_area = x_overlap * y_overlap
            if pair_area > 0.5:
                overlap_pairs.append(f"{first.name} / {second.name}")
                overlap_area += pair_area

    if overlap_area > 5:
        return _quality_check(
            "room_overlap",
            "Room overlap",
            FindingStatus.FAILS,
            f"Significant room overlap detected: {', '.join(overlap_pairs[:3])}.",
        )
    if overlap_pairs:
        return _quality_check(
            "room_overlap",
            "Room overlap",
            FindingStatus.WARNING,
            f"Minor room overlap or rounding conflict detected: {', '.join(overlap_pairs[:3])}.",
        )
    return _quality_check(
        "room_overlap",
        "Room overlap",
        FindingStatus.PASSES,
        "No meaningful room overlaps detected.",
    )


def _room_program_check(rooms: list[FloorPlanRoom], spec: UserBuildSpec) -> FloorPlanQualityCheck:
    bedroom_count = sum(1 for room in rooms if room.category == "bedroom")
    bath_count = sum(1 for room in rooms if room.category == "bath")
    has_kitchen = any(room.category == "kitchen" for room in rooms)
    has_living = any(room.category == "living" for room in rooms)
    target_bedrooms = spec.bedrooms or 1
    target_bathrooms = math.floor(spec.bathrooms or 1)
    missing: list[str] = []
    if bedroom_count < target_bedrooms:
        missing.append(f"{target_bedrooms - bedroom_count} bedroom(s)")
    if bath_count < target_bathrooms:
        missing.append(f"{target_bathrooms - bath_count} bath(s)")
    if not has_kitchen:
        missing.append("kitchen")
    if not has_living:
        missing.append("living area")

    if missing:
        return _quality_check(
            "program_fit",
            "Program fit",
            FindingStatus.FAILS,
            f"Plan is missing requested program elements: {', '.join(missing)}.",
        )
    return _quality_check(
        "program_fit",
        "Program fit",
        FindingStatus.PASSES,
        "Plan includes the requested bedroom/bath count plus kitchen and living areas.",
    )


def _room_dimension_check(rooms: list[FloorPlanRoom]) -> FloorPlanQualityCheck:
    minimums = {
        "bedroom": (70, 7),
        "bath": (24, 3),
        "kitchen": (70, 6),
        "living": (120, 8),
        "unit": (180, 8),
        "circulation": (35, 3),
    }
    failures: list[str] = []
    warnings: list[str] = []
    for room in rooms:
        min_sqft, min_dimension = minimums.get(room.category, (24, 3))
        if room.category == "living" and "dining" in room.name.lower():
            min_sqft = 80
        shortest_side = min(room.width_ft, room.depth_ft)
        longest_side = max(room.width_ft, room.depth_ft)
        if room.estimated_sqft < min_sqft or shortest_side < min_dimension:
            failures.append(room.name)
        elif room.category != "circulation" and longest_side / max(shortest_side, 1) > 4.8:
            warnings.append(room.name)

    if failures:
        return _quality_check(
            "room_dimensions",
            "Room dimensions",
            FindingStatus.FAILS,
            f"Rooms below MVP minimum size assumptions: {', '.join(failures[:4])}.",
        )
    if warnings:
        return _quality_check(
            "room_dimensions",
            "Room dimensions",
            FindingStatus.WARNING,
            f"Rooms have elongated proportions that need architect review: {', '.join(warnings[:4])}.",
        )
    return _quality_check(
        "room_dimensions",
        "Room dimensions",
        FindingStatus.PASSES,
        "Room dimensions meet MVP minimum size and proportion assumptions.",
    )


def _circulation_check(rooms: list[FloorPlanRoom]) -> FloorPlanQualityCheck:
    has_circulation = any(room.category == "circulation" for room in rooms)
    public_rooms = [room for room in rooms if room.category in {"entry", "living", "kitchen"}]
    private_rooms = [room for room in rooms if room.category in {"bedroom", "bath", "unit"}]
    if not public_rooms or not private_rooms:
        return _quality_check(
            "circulation",
            "Circulation",
            FindingStatus.WARNING,
            "Public/private room zoning could not be evaluated from this room mix.",
        )
    if not has_circulation and len(rooms) > 6:
        return _quality_check(
            "circulation",
            "Circulation",
            FindingStatus.WARNING,
            "No dedicated circulation room is modeled; door reachability needs geometric refinement.",
        )
    return _quality_check(
        "circulation",
        "Circulation",
        FindingStatus.PASSES,
        "Plan includes a legible public/private room mix and modeled circulation.",
    )


def _path_connectivity_check(
    rooms: list[FloorPlanRoom],
    connections: list[FloorPlanConnection],
) -> FloorPlanQualityCheck:
    if not rooms:
        return _quality_check(
            "path_connectivity",
            "Path connectivity",
            FindingStatus.FAILS,
            "No rooms are available to evaluate circulation paths.",
        )
    hub = _connection_hub_room(rooms)
    if hub is None or not connections:
        return _quality_check(
            "path_connectivity",
            "Path connectivity",
            FindingStatus.FAILS,
            "No room connection graph is modeled.",
        )
    reachable = _reachable_room_ids(hub.room_id, connections)
    missing = [room.name for room in rooms if room.room_id not in reachable]
    if missing:
        return _quality_check(
            "path_connectivity",
            "Path connectivity",
            FindingStatus.FAILS,
            f"Rooms are not reachable from the entry/circulation graph: {', '.join(missing[:4])}.",
        )
    narrow_doors = [
        connection.connection_id
        for connection in connections
        if connection.connection_type in {"door", "unit_entry"} and connection.width < 3
    ]
    if narrow_doors:
        return _quality_check(
            "path_connectivity",
            "Path connectivity",
            FindingStatus.WARNING,
            "Some modeled doors are narrow and need architect review.",
        )
    return _quality_check(
        "path_connectivity",
        "Path connectivity",
        FindingStatus.PASSES,
        "All rooms are reachable through the modeled connection graph.",
    )


def _opening_check(openings: list[FloorPlanOpening]) -> FloorPlanQualityCheck:
    door_count = sum(1 for opening in openings if opening.opening_type == "door")
    window_count = sum(1 for opening in openings if opening.opening_type == "window")
    if door_count == 0:
        return _quality_check(
            "openings",
            "Openings",
            FindingStatus.FAILS,
            "No exterior door opening is modeled.",
        )
    if window_count < 2:
        return _quality_check(
            "openings",
            "Openings",
            FindingStatus.WARNING,
            "Few window openings are modeled; daylight and egress need refinement.",
        )
    return _quality_check(
        "openings",
        "Openings",
        FindingStatus.PASSES,
        "Exterior door and multiple window openings are modeled.",
    )


def _unit_separation_check(
    rooms: list[FloorPlanRoom],
    walls: list[FloorPlanWall],
    spec: UserBuildSpec,
) -> FloorPlanQualityCheck:
    if spec.units <= 1:
        return _quality_check(
            "unit_separation",
            "Unit separation",
            FindingStatus.PASSES,
            "Single-unit plan does not require second-unit separation.",
        )
    has_second_unit = any(room.category == "unit" for room in rooms)
    has_unit_wall = any(wall.wall_id == "unit-separation" for wall in walls)
    has_adu_bath = any("adu" in room.room_id and room.category == "bath" for room in rooms)
    if has_second_unit and has_unit_wall and has_adu_bath:
        return _quality_check(
            "unit_separation",
            "Unit separation",
            FindingStatus.PASSES,
            "Second-unit living, bath, and conceptual separation wall are modeled.",
        )
    return _quality_check(
        "unit_separation",
        "Unit separation",
        FindingStatus.WARNING,
        "Second-unit separation is incomplete and needs geometric/code refinement.",
    )


def _solar_check(openings: list[FloorPlanOpening], strategy: str) -> FloorPlanQualityCheck:
    south_or_east_openings = [
        opening
        for opening in openings
        if "south" in opening.opening_id or "east" in opening.opening_id or opening.y >= 99 or opening.x >= 99
    ]
    west_openings = [opening for opening in openings if "west" in opening.opening_id or opening.x <= 1]
    if south_or_east_openings and not west_openings:
        return _quality_check(
            "solar_orientation",
            "Solar orientation",
            FindingStatus.PASSES,
            "Openings favor the assumed south/east daylight strategy.",
        )
    if south_or_east_openings:
        return _quality_check(
            "solar_orientation",
            "Solar orientation",
            FindingStatus.WARNING,
            "Plan includes south/east daylight assumptions but needs parcel-frontage verification.",
        )
    return _quality_check(
        "solar_orientation",
        "Solar orientation",
        FindingStatus.WARNING,
        f"{strategy.replace('_', ' ').title()} plan has generic openings; solar strategy needs true parcel orientation.",
    )


def _walls_from_rooms(rooms: list[FloorPlanRoom]) -> list[FloorPlanWall]:
    walls = [
        _wall("north", 0, 0, 100, 0, "exterior"),
        _wall("east", 100, 0, 100, 100, "exterior"),
        _wall("south", 100, 100, 0, 100, "exterior"),
        _wall("west", 0, 100, 0, 0, "exterior"),
    ]
    unit_y_values = [room.y for room in rooms if _is_unit_room(room)]
    if unit_y_values:
        unit_y = min(unit_y_values)
        walls.append(_wall("unit-separation", 0, unit_y, 100, unit_y))

    seen: set[tuple[float, float, float, float]] = set()
    for room in rooms:
        candidates = [
            (room.x, room.y, room.x + room.width, room.y),
            (room.x + room.width, room.y, room.x + room.width, room.y + room.height),
            (room.x + room.width, room.y + room.height, room.x, room.y + room.height),
            (room.x, room.y + room.height, room.x, room.y),
        ]
        for x1, y1, x2, y2 in candidates:
            if _is_exterior_segment(x1, y1, x2, y2):
                continue
            key = (round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2))
            reverse_key = (key[2], key[3], key[0], key[1])
            if key in seen or reverse_key in seen:
                continue
            seen.add(key)
            walls.append(_wall(f"room-wall-{len(walls)}", key[0], key[1], key[2], key[3]))
    return walls


def _is_exterior_segment(x1: float, y1: float, x2: float, y2: float) -> bool:
    return (
        (abs(y1) < 0.01 and abs(y2) < 0.01)
        or (abs(y1 - 100) < 0.01 and abs(y2 - 100) < 0.01)
        or (abs(x1) < 0.01 and abs(x2) < 0.01)
        or (abs(x1 - 100) < 0.01 and abs(x2 - 100) < 0.01)
    )


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
    connections: list[FloorPlanConnection],
    scale_assumption: str,
) -> str:
    scale = 7.2
    margin_x = 56
    margin_y = 92
    svg_width = 100 * scale + margin_x * 2
    svg_height = 100 * scale + margin_y + 72
    room_label_markup = "\n".join(_svg_room_label(room, scale) for room in rooms)
    fixture_markup = "\n".join(_svg_room_symbols(room, scale) for room in rooms)
    wall_markup = "\n".join(_svg_wall(wall, scale) for wall in walls)
    opening_markup = "\n".join(_svg_opening(opening, scale) for opening in openings)
    connection_markup = "\n".join(_svg_connection(connection, scale) for connection in connections)
    escaped_title = escape(title)
    escaped_scale = escape(scale_assumption)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width:.0f}" height="{svg_height:.0f}" viewBox="0 0 {svg_width:.0f} {svg_height:.0f}" role="img" aria-label="{escaped_title}">
  <style>
    .title {{ font: 18px Arial, sans-serif; fill: #111827; font-weight: 700; }}
    .small {{ font: 10px Arial, sans-serif; fill: #4b5563; }}
    .room-label {{ font: 10px Arial, sans-serif; fill: #111827; font-weight: 700; letter-spacing: 0.6px; }}
    .room-dims {{ font: 8px Arial, sans-serif; fill: #6b7280; }}
    .wall {{ stroke: #111827; stroke-linecap: square; fill: none; }}
    .exterior {{ stroke-width: 5; }}
    .interior {{ stroke-width: 2.2; }}
    .opening {{ fill: #ffffff; stroke: #111827; stroke-width: 1.2; }}
    .door {{ stroke: #111827; stroke-width: 1.2; fill: none; }}
    .fixture {{ stroke: #6b7280; stroke-width: 1; fill: none; }}
    .furniture {{ stroke: #9ca3af; stroke-width: 1; fill: none; }}
    .counter {{ stroke: #4b5563; stroke-width: 1.2; fill: #f9fafb; }}
  </style>
  <rect x="0" y="0" width="{svg_width:.0f}" height="{svg_height:.0f}" fill="#ffffff"/>
  <text x="24" y="30" class="title">{escaped_title}</text>
  <text x="24" y="50" class="small">{round(total_sqft):,} sqft | {round(width_ft, 1)} ft x {round(depth_ft, 1)} ft footprint</text>
  <text x="24" y="66" class="small">{escaped_scale}</text>
  <g transform="translate({margin_x} {margin_y})">
    <rect x="0" y="0" width="{100 * scale:.1f}" height="{100 * scale:.1f}" fill="#ffffff"/>
    {fixture_markup}
    {connection_markup}
    {opening_markup}
    {wall_markup}
    {room_label_markup}
  </g>
</svg>"""


def _svg_room_label(room: FloorPlanRoom, scale: float) -> str:
    x = room.x * scale
    y = room.y * scale
    width = room.width * scale
    height = room.height * scale
    label_y = y + height / 2 - 3
    return (
        f'<g><text class="room-label" x="{x + width / 2:.1f}" y="{label_y:.1f}" text-anchor="middle">{escape(_short_room_label(room.name))}</text>'
        f'<text class="room-dims" x="{x + width / 2:.1f}" y="{label_y + 12:.1f}" text-anchor="middle">{round(room.width_ft, 1)} ft x {round(room.depth_ft, 1)} ft</text></g>'
    )


def _svg_wall(wall: FloorPlanWall, scale: float) -> str:
    return (
        f'<line class="wall {escape(wall.wall_type)}" x1="{wall.x1 * scale:.1f}" '
        f'y1="{wall.y1 * scale:.1f}" x2="{wall.x2 * scale:.1f}" y2="{wall.y2 * scale:.1f}"/>'
    )


def _svg_opening(opening: FloorPlanOpening, scale: float) -> str:
    if opening.opening_type == "door":
        return _svg_exterior_door(opening, scale)
    width = opening.width * scale if opening.orientation == "horizontal" else 8
    height = 8 if opening.orientation == "horizontal" else opening.width * scale
    return (
        f'<rect class="opening" x="{opening.x * scale:.1f}" y="{opening.y * scale:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}"/>'
    )


def _svg_exterior_door(opening: FloorPlanOpening, scale: float) -> str:
    x = opening.x * scale
    y = opening.y * scale
    width = opening.width * scale
    if opening.orientation == "vertical":
        return (
            f'<g><line class="door" x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + width:.1f}"/>'
            f'<path class="door" d="M {x:.1f} {y:.1f} A {width:.1f} {width:.1f} 0 0 1 {x + width:.1f} {y + width:.1f}"/></g>'
        )
    return (
        f'<g><line class="door" x1="{x:.1f}" y1="{y:.1f}" x2="{x + width:.1f}" y2="{y:.1f}"/>'
        f'<path class="door" d="M {x:.1f} {y:.1f} A {width:.1f} {width:.1f} 0 0 1 {x + width:.1f} {y + width:.1f}"/></g>'
    )


def _svg_connection(connection: FloorPlanConnection, scale: float) -> str:
    if connection.connection_type == "wide_opening":
        return _svg_wide_opening(connection, scale)
    return _svg_connection_door(connection, scale)


def _svg_wide_opening(connection: FloorPlanConnection, scale: float) -> str:
    x = connection.x * scale
    y = connection.y * scale
    width = connection.width * scale
    if connection.orientation == "vertical":
        return (
            f'<rect class="opening" x="{x - 4:.1f}" y="{y - width / 2:.1f}" width="8" height="{width:.1f}"/>'
        )
    return (
        f'<rect class="opening" x="{x - width / 2:.1f}" y="{y - 4:.1f}" width="{width:.1f}" height="8"/>'
    )


def _svg_connection_door(connection: FloorPlanConnection, scale: float) -> str:
    x = connection.x * scale
    y = connection.y * scale
    door = max(18, min(34, connection.width * scale))
    if connection.orientation == "vertical":
        return (
            f'<g><line class="door" x1="{x:.1f}" y1="{y - door / 2:.1f}" x2="{x:.1f}" y2="{y + door / 2:.1f}"/>'
            f'<path class="door" d="M {x:.1f} {y - door / 2:.1f} A {door:.1f} {door:.1f} 0 0 1 {x + door:.1f} {y + door / 2:.1f}"/></g>'
        )
    return (
        f'<g><line class="door" x1="{x - door / 2:.1f}" y1="{y:.1f}" x2="{x + door / 2:.1f}" y2="{y:.1f}"/>'
        f'<path class="door" d="M {x - door / 2:.1f} {y:.1f} A {door:.1f} {door:.1f} 0 0 0 {x + door / 2:.1f} {y - door:.1f}"/></g>'
    )


def _svg_room_symbols(room: FloorPlanRoom, scale: float) -> str:
    if room.category == "bedroom":
        return _svg_bed(room, scale)
    if room.category == "bath":
        return _svg_bath_fixtures(room, scale)
    if room.category == "kitchen":
        return _svg_kitchen_fixtures(room, scale)
    if room.category == "living":
        return _svg_living_furniture(room, scale)
    if room.category == "service":
        return _svg_service_symbols(room, scale)
    if room.category == "unit":
        return _svg_unit_furniture(room, scale)
    return ""


def _svg_bed(room: FloorPlanRoom, scale: float) -> str:
    x = room.x * scale + 10
    y = room.y * scale + 10
    width = min(room.width * scale - 20, 84)
    height = min(room.height * scale - 18, 58)
    if width < 24 or height < 24:
        return ""
    pillow_w = width * 0.32
    return (
        f'<g class="furniture"><rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}"/>'
        f'<rect x="{x + 5:.1f}" y="{y + 5:.1f}" width="{pillow_w:.1f}" height="{height * 0.28:.1f}"/>'
        f'<rect x="{x + width - pillow_w - 5:.1f}" y="{y + 5:.1f}" width="{pillow_w:.1f}" height="{height * 0.28:.1f}"/></g>'
    )


def _svg_bath_fixtures(room: FloorPlanRoom, scale: float) -> str:
    x = room.x * scale + 8
    y = room.y * scale + 8
    width = max(24, room.width * scale - 16)
    tub_w = min(width, 56)
    return (
        f'<g class="fixture"><rect x="{x:.1f}" y="{y:.1f}" width="{tub_w:.1f}" height="20" rx="4"/>'
        f'<circle cx="{x + 13:.1f}" cy="{y + 42:.1f}" r="8"/>'
        f'<rect x="{x + 30:.1f}" y="{y + 34:.1f}" width="18" height="16"/></g>'
    )


def _svg_kitchen_fixtures(room: FloorPlanRoom, scale: float) -> str:
    x = room.x * scale + 8
    y = room.y * scale + 8
    width = max(30, room.width * scale - 16)
    height = max(28, room.height * scale - 16)
    island_w = min(width * 0.55, 62)
    return (
        f'<g><rect class="counter" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="16"/>'
        f'<rect class="counter" x="{x + width - 18:.1f}" y="{y:.1f}" width="18" height="{height:.1f}"/>'
        f'<rect class="counter" x="{x + width * 0.25:.1f}" y="{y + height * 0.5:.1f}" width="{island_w:.1f}" height="18"/>'
        f'<circle class="fixture" cx="{x + width - 9:.1f}" cy="{y + 10:.1f}" r="4"/>'
        f'<circle class="fixture" cx="{x + width - 9:.1f}" cy="{y + 24:.1f}" r="4"/></g>'
    )


def _svg_living_furniture(room: FloorPlanRoom, scale: float) -> str:
    x = room.x * scale + room.width * scale * 0.24
    y = room.y * scale + room.height * scale * 0.35
    sofa_w = min(room.width * scale * 0.42, 90)
    return (
        f'<g class="furniture"><rect x="{x:.1f}" y="{y:.1f}" width="{sofa_w:.1f}" height="24"/>'
        f'<rect x="{x + sofa_w * 0.2:.1f}" y="{y + 42:.1f}" width="{sofa_w * 0.55:.1f}" height="18"/>'
        f'<rect x="{x - 36:.1f}" y="{y + 34:.1f}" width="26" height="26" transform="rotate(-25 {x - 23:.1f} {y + 47:.1f})"/></g>'
    )


def _svg_service_symbols(room: FloorPlanRoom, scale: float) -> str:
    label = f"{room.name} {room.room_id}".lower()
    if "laundry" not in label and "mechanical" not in label:
        return ""
    x = room.x * scale + 8
    y = room.y * scale + room.height * scale - 42
    return (
        f'<g class="fixture"><rect x="{x:.1f}" y="{y:.1f}" width="24" height="28"/>'
        f'<rect x="{x + 30:.1f}" y="{y:.1f}" width="24" height="28"/>'
        f'<circle cx="{x + 12:.1f}" cy="{y + 14:.1f}" r="7"/>'
        f'<circle cx="{x + 42:.1f}" cy="{y + 14:.1f}" r="7"/></g>'
    )


def _svg_unit_furniture(room: FloorPlanRoom, scale: float) -> str:
    x = room.x * scale + 10
    y = room.y * scale + 10
    return (
        f'<g class="furniture"><rect x="{x:.1f}" y="{y:.1f}" width="58" height="30"/>'
        f'<rect x="{x + 76:.1f}" y="{y:.1f}" width="54" height="18"/>'
        f'<rect x="{x + 76:.1f}" y="{y + 28:.1f}" width="42" height="16"/></g>'
    )


def _short_room_label(name: str) -> str:
    replacements = {
        "Upper unit ": "",
        "Lower unit ": "",
        " / sleep": "",
        " / mechanical": "",
        "Laundry / pantry": "Laundry",
        "Living / dining": "Living",
    }
    label = name
    for before, after in replacements.items():
        label = label.replace(before, after)
    return label.upper()
