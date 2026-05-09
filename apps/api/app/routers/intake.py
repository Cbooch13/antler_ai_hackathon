from fastapi import APIRouter

from app.services.intake import normalize_build_spec
from realestate_schemas import IntakeNormalizeRequest, NormalizedBuildSpecResponse

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("/normalize", response_model=NormalizedBuildSpecResponse)
def normalize_intake(request: IntakeNormalizeRequest) -> NormalizedBuildSpecResponse:
    return normalize_build_spec(request)
