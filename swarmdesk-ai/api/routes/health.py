"""GET /health — Health check endpoint."""
from fastapi import APIRouter
from api.models.schemas import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", service="SwarmDesk AI", version="1.0.0")
