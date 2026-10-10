"""Health check endpoint.

GET /health returns 200 with a minimal JSON body.  Its purpose is operational:
- load-balancers ping it to decide whether to send traffic here
- test suites use it as the simplest possible smoke-test of the app

Design:
- No authentication required — liveness checks should always be reachable.
- Returns `status: "ok"` and the service version.
- Does NOT check downstream dependencies (DB, models) here.
  A deeper "readiness" check (e.g. GET /health/ready) would do that,
  but it's not needed in this sub-step.
"""

from fastapi import APIRouter

from src.api.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns 200 when the API process is running.",
)
def get_health() -> HealthResponse:
    """Liveness check.  Always returns 200 while the process is alive."""
    return HealthResponse(status="ok", version="0.1.0")
