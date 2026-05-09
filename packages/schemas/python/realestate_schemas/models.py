from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PositiveFloat, PositiveInt


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ContractModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskTolerance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    ADU = "adu"
    DUPLEX_TRIPLEX = "duplex_triplex"
    COMMERCIAL = "commercial"


class FindingStatus(str, Enum):
    PASSES = "passes"
    FAILS = "fails"
    WARNING = "warning"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    MISSING = "missing"
    UPLOADED = "uploaded"
    NEEDS_REVIEW = "needs_review"
    APPROVED_BY_PROFESSIONAL = "approved_by_professional"
    SUBMITTED_TO_CITY = "submitted_to_city"
    CITY_COMMENTS_RECEIVED = "city_comments_received"


class SourceMetadata(ContractModel):
    source_name: str = Field(min_length=1)
    source_url: HttpUrl
    retrieved_at: datetime
    confidence: Confidence


class UserBuildSpec(ContractModel):
    project_name: str = Field(min_length=1)
    city: str = Field(default="Austin", pattern="^Austin$")
    state: str = Field(default="TX", pattern="^TX$")
    property_type: PropertyType
    total_budget_usd: PositiveFloat
    target_lot_sqft: PositiveFloat | None = None
    target_building_sqft: PositiveFloat | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: float | None = Field(default=None, ge=0)
    units: PositiveInt = 1
    style_preferences: list[str] = Field(default_factory=list)
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM


class IntakeNormalizeRequest(ContractModel):
    free_text: str = Field(default="", description="Optional natural-language project request.")
    structured: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional camelCase or snake_case fields collected from the intake form.",
    )


class NormalizedBuildSpecResponse(ContractModel):
    spec: UserBuildSpec | None = None
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Parcel(ContractModel):
    parcel_id: str = Field(min_length=1)
    address: str
    lot_sqft: PositiveFloat | None = None
    zoning: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    sources: list[SourceMetadata] = Field(default_factory=list)


class Listing(ContractModel):
    listing_id: str = Field(min_length=1)
    parcel_id: str | None = None
    address: str
    price_usd: PositiveFloat
    lot_sqft: PositiveFloat | None = None
    source_mode: str = Field(description="prototype, licensed, manual, or public")
    current_inventory: bool = True
    sources: list[SourceMetadata] = Field(default_factory=list)


class ComplianceFinding(ContractModel):
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: FindingStatus
    summary: str = Field(min_length=1)
    confidence: Confidence
    professional_verification_required: bool
    citations: list[SourceMetadata] = Field(default_factory=list)


class DesignOption(ContractModel):
    option_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    strategy: str = Field(description="conservative, balanced, or max_yield")
    target_building_sqft: PositiveFloat
    units: PositiveInt
    assumptions: list[str] = Field(default_factory=list)
    compliance_findings: list[ComplianceFinding] = Field(default_factory=list)


class Document(ContractModel):
    document_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    role: str = Field(description="architect, civil_engineer, surveyor, attorney, or city")
    name: str = Field(min_length=1)
    status: DocumentStatus
    storage_path: str | None = None


class ReviewPacket(ContractModel):
    packet_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    documents: list[Document] = Field(default_factory=list)
    checklist: dict[str, DocumentStatus] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
