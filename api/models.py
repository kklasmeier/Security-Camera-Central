"""
SQLAlchemy ORM Models
Defines the database schema as Python classes
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from api.database import Base


class Camera(Base):
    """Camera table - stores information about each camera"""
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    status = Column(String(20), default="active")
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    events = relationship("Event", back_populates="camera")
    logs = relationship("Log", back_populates="camera")


class Event(Base):
    """Event table - stores motion detection events"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), ForeignKey("cameras.camera_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    motion_score = Column(Float, nullable=True)
    
    # File transfer status flags
    picture_a_transferred = Column(Boolean, default=False)
    picture_b_transferred = Column(Boolean, default=False)
    thumbnail_transferred = Column(Boolean, default=False)
    video_transferred = Column(Boolean, default=False)
    
    # File paths (on NFS share)
    picture_a_path = Column(String(255), nullable=True)
    picture_b_path = Column(String(255), nullable=True)
    thumbnail_path = Column(String(255), nullable=True)
    video_h264_path = Column(String(255), nullable=True)
    video_mp4_path = Column(String(255), nullable=True)
    
    # MP4 conversion status
    mp4_conversion_pending = Column(Boolean, default=False)
    mp4_conversion_complete = Column(Boolean, default=False)
    mp4_conversion_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    camera = relationship("Camera", back_populates="events")


class Log(Base):
    """Log table - stores centralized logs from cameras and central server"""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(50), nullable=False, index=True)  # 'central' or camera_id
    level = Column(String(20), nullable=False, index=True)   # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    camera_id = Column(String(50), ForeignKey("cameras.camera_id"), nullable=True, index=True)
    
    # Relationships
    camera = relationship("Camera", back_populates="logs")