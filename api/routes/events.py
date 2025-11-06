"""
Event-related API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from api.database import get_db
from api.models import Event, Camera
from api.schemas import EventCreateRequest, EventResponse, FileUpdateRequest, EventListResponse, EventStatusUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    request: EventCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new motion detection event.
    
    Called by cameras when motion is detected. Returns event_id which camera
    uses to name files (e.g., 42_20251028_143022_a.jpg).
    
    - **camera_id**: Camera identifier (must be registered first)
    - **timestamp**: When motion was detected (ISO 8601 format)
    - **motion_score**: Number of changed pixels that triggered detection
    
    Returns the created event record with auto-generated event_id.
    
    **Initial State:**
    - All file paths are NULL (files not created yet)
    - All transfer flags are FALSE (files not transferred yet)
    - MP4 conversion status is "pending"
    - Camera will update via PATCH as files are transferred (Session 1A-6)
    """
    try:
        # Validate that camera exists
        camera = db.query(Camera).filter(Camera.camera_id == request.camera_id).first()
        if not camera:
            logger.warning(f"Event creation failed: Camera {request.camera_id} not registered")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {request.camera_id} not registered. Please register camera first."
            )
        
        # Create new event
        logger.info(f"Creating event for camera {request.camera_id} at {request.timestamp}")
        
        new_event = Event(
            camera_id=request.camera_id,
            timestamp=request.timestamp,
            motion_score=request.motion_score,
            
            # File paths - initially NULL
            image_a_path=None,
            image_b_path=None,
            thumbnail_path=None,
            video_h264_path=None,
            video_mp4_path=None,
            video_duration=None,
            
            # Transfer status - initially FALSE
            image_a_transferred=False,
            image_b_transferred=False,
            thumbnail_transferred=False,
            video_transferred=False,
            
            # MP4 conversion - initially pending
            mp4_conversion_status="pending",
            mp4_converted_at=None,
            
            # AI analysis (Phase 2) - initially FALSE/NULL
            ai_processed=False,
            ai_processed_at=None,
            ai_person_detected=None,
            ai_confidence=None,
            ai_objects=None,
            ai_description=None,
            
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        logger.info(f"Event created successfully: event_id={new_event.id}, camera={request.camera_id}")
        
        return new_event
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for camera not found)
        raise
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating event for camera {request.camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.patch("/events/{event_id}/files", response_model=EventResponse)
def update_event_files(
    event_id: int,
    request: FileUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update file transfer status for an event.
    
    Called by cameras after successfully transferring a file to NFS.
    Updates the corresponding path and transfer flag in the event record.
    
    - **event_id**: Event ID (from POST /api/v1/events response)
    - **file_type**: Which file was transferred (image_a, image_b, thumbnail, video)
    - **file_path**: Path relative to /mnt/security_footage
    - **transferred**: Transfer status (always true for now)
    - **video_duration**: Video length in seconds (only for video file_type)
    
    Returns the updated event record.
    
    **File Type Mapping:**
    - image_a → image_a_path, image_a_transferred
    - image_b → image_b_path, image_b_transferred
    - thumbnail → thumbnail_path, thumbnail_transferred
    - video → video_h264_path, video_transferred (+ triggers MP4 conversion)
    """
    try:
        # Find event
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            logger.warning(f"File update failed: Event {event_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        # Log update
        logger.info(f"Updating event {event_id} ({event.camera_id}): {request.file_type} transferred")
        
        # Update corresponding fields based on file_type
        # Use setattr for path fields to satisfy static type checkers that expect Column[...] descriptors.
        if request.file_type == "image_a":
            setattr(event, "image_a_path", request.file_path)
            setattr(event, "image_a_transferred", request.transferred)
        
        elif request.file_type == "image_b":
            setattr(event, "image_b_path", request.file_path)
            setattr(event, "image_b_transferred", request.transferred)
        
        elif request.file_type == "thumbnail":
            setattr(event, "thumbnail_path", request.file_path)
            setattr(event, "thumbnail_transferred", request.transferred)
        
        elif request.file_type == "video":
            setattr(event, "video_h264_path", request.file_path)
            setattr(event, "video_transferred", request.transferred)
            
            # Update video duration if provided
            if request.video_duration is not None:
                setattr(event, "video_duration", request.video_duration)
            
            # Log that video is ready for MP4 conversion
            if request.transferred:
                logger.info(f"Event {event_id} video transferred - eligible for MP4 conversion")
        
        # Note: file_type validation is handled by Pydantic validator
        # Invalid file_type will return 422 automatically
        
        db.commit()
        db.refresh(event)
        
        logger.info(f"Event {event_id} updated successfully: {request.file_type}")
        
        return event
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event {event_id} files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event files: {str(e)}"
        )


@router.get("/events", response_model=EventListResponse)
def list_events(
    camera_id: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List events with optional filtering and pagination.
    
    Returns events sorted by timestamp (newest first).
    
    **Query Parameters:**
    - **camera_id**: Filter by specific camera (e.g., "camera_1")
    - **date**: Filter by date ("today", "yesterday", or "YYYY-MM-DD")
    - **limit**: Max results to return (default: 50, max: 200)
    - **offset**: Skip first N results for pagination (default: 0)
    
    **Examples:**
    - `/events` → 50 most recent events from all cameras
    - `/events?camera_id=camera_1` → 50 most recent events from camera_1
    - `/events?date=today` → Today's events from all cameras
    - `/events?camera_id=camera_1&date=today` → Today's events from camera_1
    - `/events?limit=10&offset=0` → First 10 events (page 1)
    - `/events?limit=10&offset=10` → Next 10 events (page 2)
    
    **Returns:**
    - Array of events with pagination metadata (total, limit, offset)
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 200:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="limit must be between 1 and 200"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="offset must be non-negative"
            )
        
        # Build query
        query = db.query(Event)
        
        # Filter by camera_id if provided
        if camera_id:
            query = query.filter(Event.camera_id == camera_id)
            logger.debug(f"Filtering events by camera_id: {camera_id}")
        
        # Filter by date if provided
        if date:
            try:
                if date == "today":
                    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    end = start + timedelta(days=1)
                elif date == "yesterday":
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    start = today - timedelta(days=1)
                    end = today
                else:
                    # Parse YYYY-MM-DD
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    start = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                    end = start + timedelta(days=1)
                
                query = query.filter(Event.timestamp >= start, Event.timestamp < end)
                logger.debug(f"Filtering events by date: {date} ({start} to {end})")
            
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid date format. Use 'today', 'yesterday', or 'YYYY-MM-DD'"
                )
        
        # Get total count (before pagination)
        total = query.count()
        
        # Sort by timestamp DESC (newest first)
        query = query.order_by(Event.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        events = query.all()
        
        logger.info(f"Returning {len(events)} events (total: {total}, limit: {limit}, offset: {offset})")
        
        return EventListResponse(
            events=events,
            total=total,
            limit=limit,
            offset=offset
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}"
        )


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single event by ID.
    
    Returns complete event record with all fields.
    
    - **event_id**: Event ID from database
    
    **Returns:**
    - Complete event record
    - 404 if event not found
    """
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            logger.warning(f"Event {event_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        logger.info(f"Returning event {event_id} (camera: {event.camera_id})")
        
        return event
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event: {str(e)}"
        )

@router.patch("/events/{event_id}/status", response_model=EventResponse)
def update_event_status(
    event_id: int,
    request: EventStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update event processing status.
    
    Called by cameras when event processing is interrupted (e.g., for live streaming)
    or when event processing completes or fails.
    
    - **event_id**: Event ID (from POST /api/v1/events response)
    - **status**: New status value
    
    **Valid Status Values:**
    - "processing" - Event currently being processed (initial state)
    - "complete" - Event fully processed, all files saved
    - "interrupted" - Event aborted (e.g., for live streaming)
    - "failed" - Event processing failed with error
    
    Returns the updated event record.
    
    **Use Cases:**
    - Camera aborts event for live streaming → status = "interrupted"
    - Camera finishes processing normally → status = "complete"
    - Camera encounters error → status = "failed"
    """
    try:
        # Find event
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            logger.warning(f"Status update failed: Event {event_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        # Validate status value
        valid_statuses = ["processing", "complete", "interrupted", "failed"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Log status change
        old_status = event.status if hasattr(event, 'status') else 'unknown'
        logger.info(
            f"Updating event {event_id} ({event.camera_id}): "
            f"status {old_status} → {request.status}"
        )
        
        # Update status
        setattr(event, "status", request.status)
        
        # Commit changes
        db.commit()
        db.refresh(event)
        
        logger.info(f"Event {event_id} status updated successfully: {request.status}")
        
        return event
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event {event_id} status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event status: {str(e)}"
        )
