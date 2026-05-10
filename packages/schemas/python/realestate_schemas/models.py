from __future__ import annotations

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


class MetricBasis(str, Enum):
    KNOWN = "known"
    ESTIMATED = "estimated"
    PUBLIC_DATA_PENDING = "public_data_pending"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    MISSING = "missing"
    UPLOADED = "uploaded"
    NEEDS_REVIEW = "needs_review"
    APPROVED_BY_PROFESSIONAL = "approved_by_professional"
    SUBMITTED_TO_CITY = "submitted_to_city"
    CITY_COMMENTS_RECEIVED = "city_comments_received"


class IngestionSourceKind(str, Enum):
    SOCRATA = "socrata"
    ARCGIS = "arcgis"
    STATIC_DATASET = "static_dataset"


class ListingSourceMode(str, Enum):
    LICENSED = "licensed"
    PROTOTYPE_STATIC_DATASET = "prototype_static_dataset"
    PROTOTYPE_APIFY = "prototype_apify"
    MANUAL = "manual"
    PUBLIC = "public"


class SourceMetadata(ContractModel):
    source_name: str = Field(min_length=1)
    source_url: HttpUrl
    retrieved_at: datetime
    confidence: Confidence
    license_name: str | None = None
    notes: list[str] = Field(default_factory=list)


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
    neighborhood: str | None = None
    price_usd: PositiveFloat
    lot_sqft: PositiveFloat | None = None
    building_sqft: PositiveFloat | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: float | None = Field(default=None, ge=0)
    units: PositiveInt = 1
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    source_mode: ListingSourceMode
    current_inventory: bool = True
    data_year: int | None = None
    prototype_note: str | None = None
    sources: list[SourceMetadata] = Field(default_factory=list)


class RankedListing(ContractModel):
    listing: Listing
    score: float = Field(ge=0, le=100)
    rank_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LotSearchRequest(ContractModel):
    spec: UserBuildSpec
    source_mode: ListingSourceMode = ListingSourceMode.PROTOTYPE_STATIC_DATASET
    limit: int = Field(default=10, ge=1, le=50)


class LotSearchResponse(ContractModel):
    source_mode: ListingSourceMode
    current_inventory: bool
    candidates: list[RankedListing] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source: SourceMetadata | None = None


class PermitRecord(ContractModel):
    permit_id: str = Field(min_length=1)
    permit_type: str | None = None
    work_class: str | None = None
    status: str | None = None
    issue_date: str | None = None
    expiration_date: str | None = None
    address: str | None = None
    description: str | None = None
    square_feet: float | None = Field(default=None, ge=0)
    valuation_usd: float | None = Field(default=None, ge=0)
    units: int | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    raw: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceMetadata] = Field(default_factory=list)


class GisFeatureRecord(ContractModel):
    feature_id: str = Field(min_length=1)
    layer_name: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    geometry: dict[str, Any] | None = None
    sources: list[SourceMetadata] = Field(default_factory=list)


class DataIngestionResponse(ContractModel):
    source_kind: IngestionSourceKind
    source_name: str = Field(min_length=1)
    records: list[PermitRecord | GisFeatureRecord]
    source: SourceMetadata
    warnings: list[str] = Field(default_factory=list)


class MapContext(ContractModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    map_provider: str = "mapbox"
    aerial_image_url: str | None = None
    street_view_url: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ParcelDetailResponse(ContractModel):
    listing: Listing
    parcel: Parcel | None = None
    map_context: MapContext
    zoning_features: list[GisFeatureRecord] = Field(default_factory=list)
    permit_history: list[PermitRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources: list[SourceMetadata] = Field(default_factory=list)


class ComplianceEvaluationRequest(ContractModel):
    spec: UserBuildSpec
    listing_id: str = Field(min_length=1)


class ComplianceFinding(ContractModel):
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: FindingStatus
    summary: str = Field(min_length=1)
    confidence: Confidence
    professional_verification_required: bool
    citations: list[SourceMetadata] = Field(default_factory=list)


class ComplianceMetric(ContractModel):
    category: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: str = Field(min_length=1)
    basis: MetricBasis
    status: FindingStatus
    confidence: Confidence
    source: str = Field(min_length=1)
    notes: str | None = None


class ComplianceEvaluationResponse(ContractModel):
    listing: Listing
    parcel: Parcel
    metrics: list[ComplianceMetric] = Field(default_factory=list)
    findings: list[ComplianceFinding]
    summary: str = Field(min_length=1)
    professional_verification_required: bool = True


class FloorPlanRoom(ContractModel):
    room_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    estimated_sqft: PositiveFloat
    width_ft: PositiveFloat
    depth_ft: PositiveFloat
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(gt=0, le=100)
    height: float = Field(gt=0, le=100)


class FloorPlanWall(ContractModel):
    wall_id: str = Field(min_length=1)
    x1: float = Field(ge=0, le=100)
    y1: float = Field(ge=0, le=100)
    x2: float = Field(ge=0, le=100)
    y2: float = Field(ge=0, le=100)
    wall_type: str = Field(default="interior")


class FloorPlanOpening(ContractModel):
    opening_id: str = Field(min_length=1)
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(gt=0, le=100)
    orientation: str = Field(pattern="^(horizontal|vertical)$")
    opening_type: str = Field(default="door")


class GeneratedVisualExport(ContractModel):
    export_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    format: str = Field(pattern="^svg$")
    content: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


class FloorPlan(ContractModel):
    plan_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    level: str = Field(min_length=1)
    total_sqft: PositiveFloat
    footprint_width_ft: PositiveFloat
    footprint_depth_ft: PositiveFloat
    scale_assumption: str = Field(min_length=1)
    sqft_delta: float = Field(default=0)
    rooms: list[FloorPlanRoom] = Field(default_factory=list)
    walls: list[FloorPlanWall] = Field(default_factory=list)
    openings: list[FloorPlanOpening] = Field(default_factory=list)
    visual_exports: list[GeneratedVisualExport] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DesignOption(ContractModel):
    option_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    strategy: str = Field(description="human_comfort or space_utilization")
    target_building_sqft: PositiveFloat
    units: PositiveInt
    floor_plans: list[FloorPlan] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    compliance_findings: list[ComplianceFinding] = Field(default_factory=list)


class DesignGenerationRequest(ContractModel):
    spec: UserBuildSpec
    listing_id: str = Field(min_length=1)


class DesignGenerationResponse(ContractModel):
    listing: Listing
    parcel: Parcel
    options: list[DesignOption] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
