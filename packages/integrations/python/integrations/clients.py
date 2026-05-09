import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from realestate_schemas import (
    Confidence,
    GisFeatureRecord,
    IngestionSourceKind,
    PermitRecord,
    SourceMetadata,
)


AUSTIN_PERMITS_DATASET_ID = "3syk-w9eu"
AUSTIN_SOCRATA_BASE_URL = "https://data.austintexas.gov/resource"
AUSTIN_ZONING_FEATURE_LAYER_URL = (
    "https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/"
    "Publish_Zoning_AGOL/FeatureServer/0"
)
AUSTIN_TCAD_PARCEL_FEATURE_LAYER_URL = (
    "https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/"
    "EXTERNAL_tcad_parcel/FeatureServer/0"
)


@dataclass(frozen=True)
class IntegrationRegistry:
    socrata_enabled: bool = False
    arcgis_enabled: bool = False
    apify_enabled: bool = False
    mapbox_enabled: bool = False
    google_maps_enabled: bool = False
    autohdr_enabled: bool = False

    @classmethod
    def stage_zero(cls) -> "IntegrationRegistry":
        return cls()

    @classmethod
    def from_env(cls) -> "IntegrationRegistry":
        return cls(
            socrata_enabled=True,
            arcgis_enabled=True,
            apify_enabled=bool(os.getenv("APIFY_API_TOKEN")),
            mapbox_enabled=bool(os.getenv("NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN")),
            google_maps_enabled=bool(os.getenv("GOOGLE_MAPS_API_KEY")),
            autohdr_enabled=bool(os.getenv("AUTOHDR_API_KEY")),
        )


@dataclass(frozen=True)
class SocrataConfig:
    base_url: str = AUSTIN_SOCRATA_BASE_URL
    dataset_id: str = AUSTIN_PERMITS_DATASET_ID
    app_token: str | None = None

    @property
    def dataset_url(self) -> str:
        return f"{self.base_url}/{self.dataset_id}.json"


class SocrataPermitClient:
    def __init__(
        self,
        config: SocrataConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = config or SocrataConfig(app_token=os.getenv("SOCRATA_APP_TOKEN"))
        self.http_client = http_client or httpx.Client(timeout=20)

    def recent_permits(self, limit: int = 25) -> list[PermitRecord]:
        limit = max(1, min(limit, 100))
        headers = {}
        if self.config.app_token:
            headers["X-App-Token"] = self.config.app_token

        response = self.http_client.get(
            self.config.dataset_url,
            params={"$limit": limit},
            headers=headers,
        )
        response.raise_for_status()
        source = _source_metadata(
            source_name="Austin Open Data issued construction permits",
            source_url=self.config.dataset_url,
            confidence=Confidence.HIGH,
            license_name="City of Austin Open Data terms",
            notes=[
                "Public city dataset used for permit history context.",
                "Official permit status should be verified with Austin Development Services.",
            ],
        )
        return [_normalize_permit(row, source) for row in response.json()]


@dataclass(frozen=True)
class ArcGisFeatureLayerConfig:
    layer_url: str
    layer_name: str


class ArcGisFeatureLayerClient:
    def __init__(
        self,
        config: ArcGisFeatureLayerConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self.http_client = http_client or httpx.Client(timeout=20)

    def query(
        self,
        where: str = "1=1",
        limit: int = 25,
        return_geometry: bool = False,
    ) -> list[GisFeatureRecord]:
        limit = max(1, min(limit, 100))
        response = self.http_client.get(
            f"{self.config.layer_url}/query",
            params={
                "f": "json",
                "where": where,
                "outFields": "*",
                "returnGeometry": str(return_geometry).lower(),
                "resultRecordCount": limit,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise httpx.HTTPStatusError(
                payload["error"].get("message", "ArcGIS query failed"),
                request=response.request,
                response=response,
            )

        source = _source_metadata(
            source_name=f"Austin ArcGIS {self.config.layer_name}",
            source_url=self.config.layer_url,
            confidence=Confidence.HIGH,
            license_name="City of Austin GIS service terms",
            notes=[
                "Public GIS layer used for spatial context.",
                "Official zoning interpretation should be verified with Austin Development Services.",
            ],
        )
        features = payload.get("features", [])
        return [
            _normalize_feature(feature, self.config.layer_name, source, index)
            for index, feature in enumerate(features)
        ]


def _normalize_permit(row: dict[str, Any], source: SourceMetadata) -> PermitRecord:
    permit_id = _first_value(
        row,
        ["permit_number", "permitnumber", "permit_num", "permitnum", "permit_id", "id"],
        fallback="unknown-permit",
    )
    latitude = _safe_float(_first_value(row, ["latitude", "lat"]))
    longitude = _safe_float(_first_value(row, ["longitude", "lon", "lng"]))
    return PermitRecord(
        permit_id=str(permit_id),
        permit_type=_optional_string(_first_value(row, ["permit_type", "permittype"])),
        work_class=_optional_string(_first_value(row, ["work_class", "workclass", "permitclass"])),
        status=_optional_string(
            _first_value(row, ["status", "status_current", "permit_status", "permitstatus"])
        ),
        issue_date=_optional_string(_first_value(row, ["issueddate", "issue_date", "issued_date"])),
        expiration_date=_optional_string(
            _first_value(row, ["expiresdate", "expiry_date", "expiration_date", "expires_date"])
        ),
        address=_optional_string(
            _first_value(row, ["original_address1", "originaladdress1", "permit_location", "address"])
        ),
        description=_optional_string(
            _first_value(row, ["description", "work_description", "project_description"])
        ),
        square_feet=_safe_float(
            _first_value(row, ["total_sq_ft", "remodel_repair_footage", "square_feet", "sqft"])
        ),
        valuation_usd=_safe_float(
            _first_value(row, ["total_valuation", "total_job_valuation", "valuation"])
        ),
        units=_safe_int(_first_value(row, ["number_of_units", "units"])),
        latitude=latitude,
        longitude=longitude,
        raw=row,
        sources=[source],
    )


def _normalize_feature(
    feature: dict[str, Any],
    layer_name: str,
    source: SourceMetadata,
    index: int,
) -> GisFeatureRecord:
    attributes = feature.get("attributes") or {}
    feature_id = _first_value(
        attributes,
        ["OBJECTID", "objectid", "FID", "fid", "ID", "id"],
        fallback=f"{layer_name}-{index}",
    )
    return GisFeatureRecord(
        feature_id=str(feature_id),
        layer_name=layer_name,
        attributes=attributes,
        geometry=feature.get("geometry"),
        sources=[source],
    )


def _source_metadata(
    source_name: str,
    source_url: str,
    confidence: Confidence,
    license_name: str,
    notes: list[str],
) -> SourceMetadata:
    return SourceMetadata(
        source_name=source_name,
        source_url=source_url,
        retrieved_at=datetime.now(timezone.utc),
        confidence=confidence,
        license_name=license_name,
        notes=notes,
    )


def _first_value(
    values: dict[str, Any],
    keys: list[str],
    fallback: Any | None = None,
) -> Any:
    lower_lookup = {key.lower(): value for key, value in values.items()}
    for key in keys:
        if key in values:
            return values[key]
        if key.lower() in lower_lookup:
            return lower_lookup[key.lower()]
    return fallback


def _optional_string(value: Any | None) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _safe_float(value: Any | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def build_zoning_client(http_client: httpx.Client | None = None) -> ArcGisFeatureLayerClient:
    return ArcGisFeatureLayerClient(
        ArcGisFeatureLayerConfig(
            layer_url=AUSTIN_ZONING_FEATURE_LAYER_URL,
            layer_name="zoning",
        ),
        http_client=http_client,
    )


def build_tcad_parcel_client(http_client: httpx.Client | None = None) -> ArcGisFeatureLayerClient:
    return ArcGisFeatureLayerClient(
        ArcGisFeatureLayerConfig(
            layer_url=AUSTIN_TCAD_PARCEL_FEATURE_LAYER_URL,
            layer_name="tcad_parcel",
        ),
        http_client=http_client,
    )
