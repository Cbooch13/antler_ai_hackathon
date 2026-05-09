from fastapi import APIRouter

from app.services.listings import search_lots
from realestate_schemas import LotSearchRequest, LotSearchResponse

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/search", response_model=LotSearchResponse)
def search_listings(request: LotSearchRequest) -> LotSearchResponse:
    return search_lots(request)
