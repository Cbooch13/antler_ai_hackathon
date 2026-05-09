from enum import Enum

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    INTAKE = "intake"
    LISTING = "listing"
    GIS = "gis"
    COMPLIANCE = "compliance"
    FINANCE = "finance"
    DESIGN = "design"
    VISUALIZATION = "visualization"
    REVIEW_PACKET = "review_packet"


class OrchestrationPlan(BaseModel):
    project_id: str = Field(min_length=1)
    current_agent: AgentName
    completed_agents: list[AgentName] = Field(default_factory=list)
    blocked_reason: str | None = None
