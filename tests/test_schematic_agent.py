from estate_agents import SchematicAgentInput, SchematicDesignAgent
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
    assert all(option.floor_plans[0].scale_assumption.startswith("Concept scale") for option in options)
    assert all(option.floor_plans[0].visual_exports[0].format == "svg" for option in options)

    second_run = SchematicDesignAgent().generate(
        SchematicAgentInput(spec=spec, warning_findings=[])
    )
    assert options[0].option_id != second_run[0].option_id
