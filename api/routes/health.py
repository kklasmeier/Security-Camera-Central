"""
Health Check Endpoint
Provides API status and database connectivity check
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from api.database import get_db
from api.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns:
        - status: "healthy" or "unhealthy"
        - database_connected: True if DB connection works
        - timestamp: Current server time
        - version: API version
    
    This endpoint can be used for:
    - Monitoring/alerting systems
    - Load balancer health checks
    - Debugging connectivity issues
    """
    database_connected = False
    status = "unhealthy"
    
    try:
        # Test database connection by executing a simple query
        db.execute(text("SELECT 1"))
        database_connected = True
        status = "healthy"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        database_connected = False
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        database_connected=database_connected,
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )
