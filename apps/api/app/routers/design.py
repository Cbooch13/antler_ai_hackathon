from fastapi import APIRouter, HTTPException

from app.services.design import generate_design_options
from realestate_schemas import DesignGenerationRequest, DesignGenerationResponse

router = APIRouter(prefix="/design", tags=["design"])


@router.post("/schematics", response_model=DesignGenerationResponse)
def schematics(request: DesignGenerationRequest) -> DesignGenerationResponse:
    response = generate_design_options(request)
    if response is None:
        raise HTTPException(status_code=404, detail="Listing context not found")
    return response
