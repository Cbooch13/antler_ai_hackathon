from fastapi import APIRouter, Query

from app.services.data_ingestion import (
    fetch_recent_permits,
    fetch_tcad_parcel_sample,
    fetch_zoning_sample,
)
from realestate_schemas import DataIngestionResponse

router = APIRouter(prefix="/data/austin", tags=["austin-data"])


@router.get("/permits/recent", response_model=DataIngestionResponse)
def recent_permits(limit: int = Query(default=25, ge=1, le=100)) -> DataIngestionResponse:
    return fetch_recent_permits(limit=limit)


@router.get("/zoning/sample", response_model=DataIngestionResponse)
def zoning_sample(limit: int = Query(default=25, ge=1, le=100)) -> DataIngestionResponse:
    return fetch_zoning_sample(limit=limit)


@router.get("/parcels/sample", response_model=DataIngestionResponse)
def parcel_sample(limit: int = Query(default=25, ge=1, le=100)) -> DataIngestionResponse:
    return fetch_tcad_parcel_sample(limit=limit)
