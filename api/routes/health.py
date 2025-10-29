"""
Health check endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from api.database import get_db, check_database_connection
from api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint - returns API status and database connection status
    
    Returns:
        - status: "healthy" if API is running
        - timestamp: Current server time
        - database: "connected" or "disconnected"
    """
    # Check database connection
    db_status = "connected" if check_database_connection() else "disconnected"
    
    # Return health status (NO VERSION FIELD)
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        database=db_status
    )