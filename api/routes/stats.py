"""
Camera statistics endpoint
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, cast

from api.database import get_db
from api.models import Event  # Changed from Events to Event

router = APIRouter()


@router.get("/cameras/{camera_id}/stats")
def get_camera_stats(
    camera_id: str,
    hours: int = Query(default=24, ge=1, le=168),  # 1-168 hours (1 week max)
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get camera statistics for specified time period.
    
    Args:
        camera_id: Camera identifier (e.g., "camera_1")
        hours: Number of hours to look back (default: 24, max: 168)
        db: Database session
    
    Returns:
        {
            'events': <count>,
            'files': <count>,
            'bytes': <total bytes>,
            'period_hours': <hours>
        }
    """
    # Calculate cutoff timestamp
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Count events for this camera in the time period
    events_count = db.query(Event).filter(
        Event.camera_id == camera_id,  # Changed to camera_id
        Event.timestamp >= cutoff
    ).count()
    
    # Get events with transferred files
    events_with_files = db.query(Event).filter(
        Event.camera_id == camera_id,
        Event.timestamp >= cutoff
    ).all()
    
    # Count files and bytes
    # Since files are stored as paths in Event model (not separate EventFiles table)
    total_files = 0
    total_bytes = 0
    
    for event in events_with_files:
        # Count transferred files
        if event.image_a_transferred is True:
            total_files += 1
        if event.image_b_transferred is True:
            total_files += 1
        if event.thumbnail_transferred is True:
            total_files += 1
        if event.video_transferred is True:
            total_files += 1
        
        # Note: Your Event model doesn't store file sizes
        # So we can't calculate total_bytes accurately
        # We'll estimate based on typical file sizes
        if event.image_a_transferred is True:
            total_bytes += 200000  # ~200KB per image
        if event.image_b_transferred is True:
            total_bytes += 200000
        if event.thumbnail_transferred is True:
            total_bytes += 50000   # ~50KB per thumbnail
        if event.video_transferred is True:
            # Cast to Optional[float] for type checkers and safely handle non-numeric values at runtime
            duration = cast(Optional[float], getattr(event, "video_duration", None))
            if duration is not None:
                try:
                    total_bytes += int(duration * 500000)  # ~500KB per second of video
                except (TypeError, ValueError):
                    # If duration isn't a numeric value, skip adding bytes
                    pass
    
    return {
        'events': events_count,
        'files': total_files,
        'bytes': total_bytes,
        'period_hours': hours
    }