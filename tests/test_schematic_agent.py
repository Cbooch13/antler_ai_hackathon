import json
from types import SimpleNamespace

from estate_agents import OpenAISchematicDesignAgent, SchematicAgentInput, SchematicDesignAgent
from realestate_schemas import PropertyType, UserBuildSpec


def test_schematic_agent_generates_comfort_and_utilization_versions() -> None:
    spec = UserBuildSpec(
        project_name="Architectural concept",
        property_type=PropertyType.ADU,
        total_budget_usd=850_000,
        target_building_sqft=2_200,
        bedrooms=4,
        bathrooms=3,
        units=2,
    )

    options = SchematicDesignAgent().generate(
        SchematicAgentInput(spec=spec, warning_findings=[])
    )

    assert [option.strategy for option in options] == ["human_comfort", "space_utilization"]
    assert all(option.floor_plans for option in options)
    assert all(option.floor_plans[0].walls for option in options)
    assert all(option.floor_plans[0].openings for option in options)
    assert all(option.target_building_sqft == 2_200 for option in options)
    assert all(abs(option.floor_plans[0].sqft_delta) < 0.01 for option in options)
    assert all(option.floor_plans[0].quality_report.score > 0 for option in options)
    assert all(option.floor_plans[0].quality_report.checks for option in options)
    assert all(
        not any(check.status == "fails" for check in option.floor_plans[0].quality_report.checks)
        for option in options
    )
    assert all(option.floor_plans[0].scale_assumption.startswith("Concept scale") for option in options)
    assert all(option.floor_plans[0].visual_exports[0].format == "svg" for option in options)

    second_run = SchematicDesignAgent().generate(
        SchematicAgentInput(spec=spec, warning_findings=[])
    )
    assert options[0].option_id != second_run[0].option_id


def test_openai_schematic_agent_falls_back_when_disabled(monkeypatch) -> None:
    monkeypatch.delenv("LLM_SCHEMATIC_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    spec = UserBuildSpec(
        project_name="Fallback concept",
        property_type=PropertyType.ADU,
        total_budget_usd=850_000,
        target_building_sqft=1_800,
        units=1,
    )

    options = OpenAISchematicDesignAgent().generate(
        SchematicAgentInput(
            spec=spec,
            warning_findings=[],
            address="4307 Avenue G, Austin, TX 78751",
            neighborhood="Hyde Park / Central Austin",
            lot_sqft=6_600,
            zoning="SF-3",
        )
    )

    assert [option.strategy for option in options] == ["human_comfort", "space_utilization"]
    assert all(option.floor_plans for option in options)
    assert all(option.floor_plans[0].quality_report.checks for option in options)


def test_openai_schematic_agent_revises_against_quality_feedback(monkeypatch) -> None:
    monkeypatch.setenv("LLM_SCHEMATIC_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    prompts: list[str] = []
    responses = [
        _llm_payload(include_required_program=False),
        _llm_payload(include_required_program=True),
    ]

    class FakeResponses:
        def create(self, **kwargs):
            prompts.append(kwargs["input"][1]["content"])
            return SimpleNamespace(output_text=json.dumps(responses.pop(0)))

    class FakeClient:
        responses = FakeResponses()

    spec = UserBuildSpec(
        project_name="Revision concept",
        property_type=PropertyType.SINGLE_FAMILY,
        total_budget_usd=850_000,
        target_building_sqft=1_200,
        bedrooms=2,
        bathrooms=1,
        units=1,
    )

    options = OpenAISchematicDesignAgent(
        client_factory=lambda: FakeClient(),
        max_attempts=3,
    ).generate(SchematicAgentInput(spec=spec, warning_findings=[]))

    assert len(prompts) == 2
    assert '"revision_feedback": []' in prompts[0]
    assert "program_fit" in prompts[1]
    assert [option.strategy for option in options] == ["human_comfort", "space_utilization"]
    assert all(
        not any(check.status == "fails" for check in option.floor_plans[0].quality_report.checks)
        for option in options
    )
    assert all(
        any("revision loop attempt 2 of 3" in assumption for assumption in option.assumptions)
        for option in options
    )


def _llm_payload(include_required_program: bool) -> dict:
    if include_required_program:
        rooms = [
            _llm_room("Entry", "entry", 7, 7),
            _llm_room("Living", "living", 16, 14),
            _llm_room("Kitchen", "kitchen", 12, 10),
            _llm_room("Gallery hall", "circulation", 12, 5),
            _llm_room("Primary bedroom", "bedroom", 13, 12),
            _llm_room("Bedroom 2", "bedroom", 11, 11),
            _llm_room("Bath", "bath", 8, 6),
        ]
    else:
        rooms = [
            _llm_room("Primary bedroom", "bedroom", 13, 12),
            _llm_room("Bedroom 2", "bedroom", 11, 11),
            _llm_room("Bath", "bath", 8, 6),
        ]

    return {
        "options": [
            {
                "name": "Human Comfort Plan",
                "strategy": "human_comfort",
                "concept": "Comfort-focused test plan.",
                "solar_strategy": "Prioritize south and east daylight.",
                "floors": [{"level": "Level 1", "rooms": rooms, "floor_notes": ["Test floor."]}],
                "assumptions": ["Test assumption."],
            },
            {
                "name": "Space Utilization Plan",
                "strategy": "space_utilization",
                "concept": "Efficient test plan.",
                "solar_strategy": "Compact plan with controlled glazing.",
                "floors": [{"level": "Level 1", "rooms": rooms, "floor_notes": ["Test floor."]}],
                "assumptions": ["Test assumption."],
            },
        ]
    }


def _llm_room(name: str, category: str, width_ft: float, depth_ft: float) -> dict:
    return {
        "name": name,
        "category": category,
        "width_ft": width_ft,
        "depth_ft": depth_ft,
        "daylight_orientation": "south/east where possible",
        "adjacency_notes": "test adjacency",
    }
