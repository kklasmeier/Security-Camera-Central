"""
Camera-related API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
import logging

from api.database import get_db
from api.models import Camera
from api.schemas import CameraRegisterRequest, CameraResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/cameras/register", response_model=CameraResponse)
def register_camera(
    request: CameraRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new camera or update existing camera.
    
    - **camera_id**: Unique identifier for camera (e.g., "camera_1")
    - **name**: Human-readable name (e.g., "Front Door")
    - **location**: Physical location (e.g., "Main Entrance")
    - **ip_address**: Camera IP address for MJPEG streaming
    
    Returns the camera record (created or updated).
    
    **Behavior:**
    - If camera_id does not exist: Creates new camera (HTTP 201)
    - If camera_id exists: Updates existing camera (HTTP 200)
    """
    try:
        # Check if camera already exists
        existing_camera = db.query(Camera).filter(Camera.camera_id == request.camera_id).first()
        
        if existing_camera:
            # Update existing camera
            logger.info(f"Camera {request.camera_id} already exists, updating registration")
            
            setattr(existing_camera, "name", request.name)
            setattr(existing_camera, "location", request.location)
            setattr(existing_camera, "ip_address", request.ip_address)
            setattr(existing_camera, "status", "online")
            setattr(existing_camera, "updated_at", datetime.now(timezone.utc))
            
            db.commit()
            db.refresh(existing_camera)
            
            logger.info(f"Camera {request.camera_id} updated successfully")
            
            # Return updated camera (FastAPI will use 200 OK by default for existing)
            return existing_camera
        
        else:
            # Create new camera
            logger.info(f"Registering new camera: {request.camera_id}")
            
            new_camera = Camera(    
                camera_id=request.camera_id,
                name=request.name,
                location=request.location,
                ip_address=request.ip_address,
                status="online",
                last_seen=None,  # Will be updated by heartbeat (Phase 2)
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(new_camera)
            db.commit()
            db.refresh(new_camera)
            
            logger.info(f"Camera {request.camera_id} registered successfully (ID: {new_camera.id})")
            
            # Return new camera
            return new_camera
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering camera {request.camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register camera: {str(e)}"
        )


@router.get("/cameras", response_model=List[CameraResponse])
def list_cameras(db: Session = Depends(get_db)):
    """
    List all registered cameras.
    
    Returns cameras sorted by camera_id (camera_1, camera_2, camera_3, camera_4).
    Used by web UI to populate navigation dropdowns.
    
    **Returns:**
    Array of all registered cameras with:
    - id: Database primary key
    - camera_id: Unique camera identifier
    - name: Human-readable name
    - location: Physical location
    - ip_address: Camera IP address
    - status: Current status (online/offline)
    - last_seen: Last heartbeat timestamp
    - created_at: Registration timestamp
    - updated_at: Last update timestamp
    """
    try:
        cameras = db.query(Camera).order_by(Camera.camera_id).all()
        
        logger.info(f"Returning {len(cameras)} cameras")
        
        return cameras
    
    except Exception as e:
        logger.error(f"Error listing cameras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cameras: {str(e)}"
        )