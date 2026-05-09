from datetime import datetime, timezone

from integrations import (
    AUSTIN_PERMITS_DATASET_ID,
    AUSTIN_TCAD_PARCEL_FEATURE_LAYER_URL,
    AUSTIN_ZONING_FEATURE_LAYER_URL,
    SocrataPermitClient,
    build_tcad_parcel_client,
    build_zoning_client,
)
from realestate_schemas import Confidence, DataIngestionResponse, IngestionSourceKind, SourceMetadata


def fetch_recent_permits(limit: int = 25) -> DataIngestionResponse:
    records = SocrataPermitClient().recent_permits(limit=limit)
    source = records[0].sources[0] if records else _source(
        "Austin Open Data issued construction permits",
        f"https://data.austintexas.gov/resource/{AUSTIN_PERMITS_DATASET_ID}.json",
        "City of Austin Open Data terms",
    )
    return DataIngestionResponse(
        source_kind=IngestionSourceKind.SOCRATA,
        source_name="Austin issued construction permits",
        records=records,
        source=source,
        warnings=[
            "Permit data is used for context and should be verified against official Austin records."
        ],
    )


def fetch_zoning_sample(limit: int = 25) -> DataIngestionResponse:
    records = build_zoning_client().query(limit=limit, return_geometry=False)
    source = records[0].sources[0] if records else _source(
        "Austin ArcGIS zoning",
        AUSTIN_ZONING_FEATURE_LAYER_URL,
        "City of Austin GIS service terms",
    )
    return DataIngestionResponse(
        source_kind=IngestionSourceKind.ARCGIS,
        source_name="Austin zoning",
        records=records,
        source=source,
        warnings=[
            "Zoning layer data is spatial context, not an official zoning interpretation."
        ],
    )


def fetch_tcad_parcel_sample(limit: int = 25) -> DataIngestionResponse:
    records = build_tcad_parcel_client().query(limit=limit, return_geometry=False)
    source = records[0].sources[0] if records else _source(
        "Austin ArcGIS TCAD parcels",
        AUSTIN_TCAD_PARCEL_FEATURE_LAYER_URL,
        "City of Austin GIS service terms",
    )
    return DataIngestionResponse(
        source_kind=IngestionSourceKind.ARCGIS,
        source_name="TCAD parcels",
        records=records,
        source=source,
        warnings=[
            "Parcel data is used for matching and should be verified by survey/title review."
        ],
    )


def _source(source_name: str, source_url: str, license_name: str) -> SourceMetadata:
    return SourceMetadata(
        source_name=source_name,
        source_url=source_url,
        retrieved_at=datetime.now(timezone.utc),
        confidence=Confidence.HIGH,
        license_name=license_name,
        notes=["Source returned no records for this request."],
    )
