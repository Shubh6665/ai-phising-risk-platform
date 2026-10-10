"""Analysis endpoint."""

from typing import Annotated
from fastapi import APIRouter, Depends, Request
import structlog

from src.api.schemas import AnalyzeRequest, AnalyzeResponse
from src.api.dependencies import get_classical_model, get_nlp_model, get_nlp_tokenizer
from src.api.services import AnalysisService

logger = structlog.get_logger(__name__)

router = APIRouter()

def get_analysis_service(
    classical_model=Depends(get_classical_model),
    nlp_model=Depends(get_nlp_model),
    nlp_tokenizer=Depends(get_nlp_tokenizer),
) -> AnalysisService:
    return AnalysisService(classical_model, nlp_model, nlp_tokenizer)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze email risk",
    description="Returns risk score and probabilities from ensemble models.",
)
def analyze(
    request: Request,
    payload: AnalyzeRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalyzeResponse:
    # Get request_id set by middleware
    request_id = getattr(request.state, "request_id", "unknown")
    
    result = service.analyze_email(
        request_id=request_id,
        text=payload.text,
        subject=payload.subject,
    )
    
    return AnalyzeResponse(**result)
