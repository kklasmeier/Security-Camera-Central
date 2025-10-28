"""
Pydantic Schemas for Request/Response Validation
These models define the structure of API requests and responses
"""
from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str
    database_connected: bool
    timestamp: datetime
    version: str


# Placeholder for future schemas (Sessions 1A-4 through 1A-9)
# 
# Examples that will be added in future sessions:
# - CameraRegisterRequest
# - CameraRegisterResponse
# - EventCreateRequest
# - EventCreateResponse
# - EventResponse
# - EventListResponse
# - FileUpdateRequest
# - LogCreateRequest
# - LogResponse