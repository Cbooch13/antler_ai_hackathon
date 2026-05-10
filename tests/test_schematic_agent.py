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
    assert options[0].target_building_sqft > options[1].target_building_sqft
