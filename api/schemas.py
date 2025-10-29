"""
Pydantic Schemas for Request/Response Validation
Defines data structures for API requests and responses
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Literal, List
import re


# ============================================================================
# HEALTH CHECK SCHEMA
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint"""
    status: str
    timestamp: datetime
    database: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-28T10:30:00",
                "database": "connected"
            }
        }


# Alias for backward compatibility with existing health.py
HealthResponse = HealthCheckResponse


# ============================================================================
# CAMERA SCHEMAS
# ============================================================================

class CameraRegisterRequest(BaseModel):
    """Request schema for camera registration"""
    camera_id: str = Field(..., min_length=1, max_length=50, description="Unique camera identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable camera name")
    location: str = Field(..., min_length=1, max_length=200, description="Physical location")
    ip_address: str = Field(..., max_length=45, description="Camera IP address")
    
    @validator('camera_id')
    def validate_camera_id(cls, v):
        """Validate camera_id format (alphanumeric + underscore only)"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('camera_id must contain only alphanumeric characters and underscores')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format (basic validation)"""
        # Basic IPv4 validation
        parts = v.split('.')
        if len(parts) == 4:
            try:
                if all(0 <= int(part) <= 255 for part in parts):
                    return v
            except ValueError:
                pass
        # If not valid IPv4, accept as-is (could be IPv6 or hostname)
        # More strict validation can be added if needed
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "camera_1",
                "name": "Front Door",
                "location": "Main Entrance",
                "ip_address": "192.168.1.201"
            }
        }


class CameraResponse(BaseModel):
    """Response schema for camera data"""
    id: int
    camera_id: str
    name: str
    location: str
    ip_address: str
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model


# ============================================================================
# EVENT SCHEMAS
# ============================================================================

class EventCreateRequest(BaseModel):
    """Request schema for creating a new event"""
    camera_id: str = Field(..., max_length=50, description="Camera identifier (must be registered)")
    timestamp: datetime = Field(..., description="When motion was detected (ISO 8601 format)")
    motion_score: float = Field(..., ge=0, description="Number of changed pixels")
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        """Parse timestamp string to datetime object"""
        if isinstance(v, str):
            try:
                # Parse ISO 8601 format
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('timestamp must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffff)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "camera_1",
                "timestamp": "2025-10-28T14:30:22.186476",
                "motion_score": 75.3
            }
        }


class FileUpdateRequest(BaseModel):
    """Request schema for updating file transfer status"""
    file_type: str = Field(
        ..., 
        description="Type of file being updated (image_a, image_b, thumbnail, video)"
    )
    file_path: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="Path relative to /mnt/security_footage"
    )
    transferred: bool = Field(
        ..., 
        description="Transfer status (true = successfully transferred)"
    )
    video_duration: Optional[float] = Field(
        None, 
        gt=0, 
        description="Video duration in seconds (only for file_type='video')"
    )
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file_type is one of the allowed values"""
        valid_types = ["image_a", "image_b", "thumbnail", "video"]
        if v not in valid_types:
            raise ValueError(
                f"Invalid file_type '{v}'. Must be one of: {', '.join(valid_types)}"
            )
        return v
    
    @validator('video_duration')
    def validate_video_duration(cls, v, values):
        """Validate video_duration only provided for video file_type"""
        if v is not None and values.get('file_type') != 'video':
            raise ValueError('video_duration can only be provided for file_type="video"')
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "file_type": "image_a",
                    "file_path": "camera_1/pictures/42_20251028_143022_a.jpg",
                    "transferred": True
                },
                {
                    "file_type": "video",
                    "file_path": "camera_1/videos/42_20251028_143022_video.h264",
                    "transferred": True,
                    "video_duration": 30.5
                }
            ]
        }


class EventResponse(BaseModel):
    """Response schema for event data"""
    id: int
    camera_id: str
    timestamp: datetime
    motion_score: Optional[float] = None
    
    # File paths
    image_a_path: Optional[str] = None
    image_b_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    video_h264_path: Optional[str] = None
    video_mp4_path: Optional[str] = None
    video_duration: Optional[float] = None
    
    # Transfer status
    image_a_transferred: bool
    image_b_transferred: bool
    thumbnail_transferred: bool
    video_transferred: bool
    
    # MP4 conversion
    mp4_conversion_status: str
    mp4_converted_at: Optional[datetime] = None
    
    # AI analysis (Phase 2)
    ai_processed: bool
    ai_processed_at: Optional[datetime] = None
    ai_person_detected: Optional[bool] = None
    ai_confidence: Optional[float] = None
    ai_objects: Optional[str] = None  # JSON string
    ai_description: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventListResponse(BaseModel):
    """Response schema for list of events with pagination metadata"""
    events: List[EventResponse] = Field(..., description="Array of events")
    total: int = Field(..., ge=0, description="Total number of events matching query")
    limit: int = Field(..., ge=1, le=200, description="Max results returned")
    offset: int = Field(..., ge=0, description="Number of results skipped")
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "id": 42,
                        "camera_id": "camera_1",
                        "timestamp": "2025-10-28T14:30:22.186476",
                        "motion_score": 75.3,
                        "image_a_path": "camera_1/pictures/42_20251028_143022_a.jpg",
                        "image_b_path": "camera_1/pictures/42_20251028_143022_b.jpg",
                        "thumbnail_path": "camera_1/thumbs/42_20251028_143022_thumb.jpg",
                        "video_h264_path": "camera_1/videos/42_20251028_143022_video.h264",
                        "video_mp4_path": "camera_1/videos/42_20251028_143022_video.mp4",
                        "video_duration": 30.5,
                        "image_a_transferred": True,
                        "image_b_transferred": True,
                        "thumbnail_transferred": True,
                        "video_transferred": True,
                        "mp4_conversion_status": "complete",
                        "mp4_converted_at": "2025-10-28T14:31:00.000000",
                        "ai_processed": False,
                        "ai_processed_at": None,
                        "ai_person_detected": None,
                        "ai_confidence": None,
                        "ai_objects": None,
                        "ai_description": None,
                        "created_at": "2025-10-28T14:30:22.200000"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


# ============================================================================
# LOG SCHEMAS
# ============================================================================

class LogEntry(BaseModel):
    """Schema for a single log entry"""
    source: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="Log source identifier (e.g., camera_1, central)"
    )
    timestamp: datetime = Field(
        ..., 
        description="When log entry was generated (ISO 8601 format)"
    )
    level: Literal["INFO", "WARNING", "ERROR"] = Field(
        ..., 
        description="Log severity level"
    )
    message: str = Field(
        ..., 
        min_length=1, 
        description="Log message content"
    )
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        """Parse timestamp string to datetime object"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('timestamp must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffff)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "camera_1",
                "timestamp": "2025-10-28T14:30:22.186476",
                "level": "INFO",
                "message": "Motion detected at threshold 75.3"
            }
        }


class LogIngestResponse(BaseModel):
    """Response schema for log ingestion"""
    status: str = Field(default="success", description="Status of operation")
    logs_inserted: int = Field(..., description="Number of logs inserted")


class LogResponse(BaseModel):
    """Response schema for a single log entry"""
    id: int
    source: str
    timestamp: datetime
    level: str
    message: str
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model


class LogListResponse(BaseModel):
    """Response schema for list of logs with pagination"""
    logs: List[LogResponse] = Field(..., description="Array of log entries")
    total: int = Field(..., ge=0, description="Total number of logs matching query")
    limit: int = Field(..., ge=1, le=500, description="Max results returned")
    offset: int = Field(..., ge=0, description="Number of results skipped")
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "id": 123,
                        "source": "camera_1",
                        "timestamp": "2025-10-28T14:30:22.186476",
                        "level": "INFO",
                        "message": "Motion detected at threshold 75.3"
                    }
                ],
                "total": 1,
                "limit": 100,
                "offset": 0
            }
        }