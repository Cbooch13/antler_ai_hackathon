from fastapi import APIRouter, HTTPException

from app.services.listings import get_listing_detail, search_lots
from realestate_schemas import LotSearchRequest, LotSearchResponse, ParcelDetailResponse

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/search", response_model=LotSearchResponse)
def search_listings(request: LotSearchRequest) -> LotSearchResponse:
    return search_lots(request)


@router.get("/{listing_id}/detail", response_model=ParcelDetailResponse)
def listing_detail(listing_id: str) -> ParcelDetailResponse:
    detail = get_listing_detail(listing_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return detail
