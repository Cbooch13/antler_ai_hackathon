from fastapi import APIRouter, HTTPException

from app.services.compliance import evaluate_compliance
from realestate_schemas import ComplianceEvaluationRequest, ComplianceEvaluationResponse

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/evaluate", response_model=ComplianceEvaluationResponse)
def evaluate(request: ComplianceEvaluationRequest) -> ComplianceEvaluationResponse:
    response = evaluate_compliance(request)
    if response is None:
        raise HTTPException(status_code=404, detail="Listing context not found")
    return response
