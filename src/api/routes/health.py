"""Health check endpoint."""

from fastapi import APIRouter
from src.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")
