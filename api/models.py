"""
SQLAlchemy ORM Models
Defines the database schema as Python classes
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from api.database import Base
from sqlalchemy import Column, String

class Camera(Base):
    """Camera table - stores information about each camera"""
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=False)
    last_seen = Column(DateTime, nullable=True)
    status = Column(String(20), default="offline")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    events = relationship("Event", back_populates="camera")


class Event(Base):
    """Event table - stores motion detection events"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), ForeignKey("cameras.camera_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    motion_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    status = Column(
        String(20),
        default="processing",
        nullable=False,
        comment="Event processing status: processing, complete, interrupted, failed"
    )

    # File paths (on NFS share) - relative to /mnt/security_footage
    image_a_path = Column(String(500), nullable=True)
    image_b_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    video_h264_path = Column(String(500), nullable=True)
    video_mp4_path = Column(String(500), nullable=True)
    video_duration = Column(Float, nullable=True)  # Duration in seconds
    
    # File transfer status flags
    image_a_transferred = Column(Boolean, default=False)
    image_b_transferred = Column(Boolean, default=False)
    thumbnail_transferred = Column(Boolean, default=False)
    video_transferred = Column(Boolean, default=False)
    
    # MP4 conversion status (managed by central server worker)
    mp4_conversion_status = Column(String(20), default="pending")  # Values: pending, processing, complete, failed
    mp4_converted_at = Column(DateTime, nullable=True)
    
    # AI analysis (Phase 2)
    ai_processed = Column(Boolean, default=False)
    ai_processed_at = Column(DateTime, nullable=True)
    ai_person_detected = Column(Boolean, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_objects = Column(Text, nullable=True)  # JSON string of detected objects
    ai_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    camera = relationship("Camera", back_populates="events")


class Log(Base):
    """Log table - stores centralized logs from cameras and central server"""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)  # 'central' or camera_id
    timestamp = Column(DateTime, nullable=False, index=True)  # Provided by source (camera/central)
    level = Column(String(20), nullable=False, index=True)   # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    
    # NOTE: No camera_id foreign key - logs table is independent
    # The 'source' field contains the camera_id or 'central' as a string
    # NOTE: No created_at column - using timestamp for when log was created