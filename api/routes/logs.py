"""
Log-related API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging

from api.database import get_db
from api.models import Log
from api.schemas import LogEntry, LogIngestResponse, LogResponse, LogListResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/logs", response_model=LogIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_logs(
    logs: List[LogEntry],
    db: Session = Depends(get_db)
):
    """
    Ingest a batch of log entries from cameras or central server.
    
    Accepts an array of log entries and inserts them into the database.
    All entries are inserted in a single transaction (all-or-nothing).
    
    - **source**: Log source identifier (e.g., "camera_1", "central")
    - **timestamp**: When log entry was generated (ISO 8601 format)
    - **level**: Log severity level (INFO, WARNING, ERROR)
    - **message**: Log message content
    
    Returns the number of logs inserted.
    
    **Log Levels:**
    - INFO: Normal operations
    - WARNING: Unusual but handled situations
    - ERROR: Failures requiring attention
    
    **Usage:**
    Cameras buffer logs locally and send batches every ~10 seconds.
    Central server components can also log via this endpoint.
    """
    try:
        # Validate array is not empty
        if not logs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Log array cannot be empty"
            )
        
        # Extract source for logging (use first entry's source)
        source = logs[0].source if logs else "unknown"
        count = len(logs)
        
        logger.info(f"Ingesting {count} log entries from {source}")
        
        # Create Log objects for bulk insert
        log_objects = []
        for log_entry in logs:
            log_obj = Log(
                source=log_entry.source,
                timestamp=log_entry.timestamp,
                level=log_entry.level,
                message=log_entry.message
            )
            log_objects.append(log_obj)
        
        # Bulk insert (more efficient than individual inserts)
        db.bulk_save_objects(log_objects)
        db.commit()
        
        logger.info(f"Successfully inserted {count} log entries from {source}")
        
        return LogIngestResponse(
            status="success",
            logs_inserted=count
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for empty array)
        raise
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting logs from {source if 'source' in locals() else 'unknown'}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert logs: {str(e)}"
        )


@router.get("/logs", response_model=LogListResponse)
def get_logs(
    source: Optional[str] = None,
    level: Optional[str] = None,
    after: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Retrieve logs with optional filtering and pagination.
    
    Returns logs sorted by timestamp (newest first).
    
    **Query Parameters:**
    - **source** (optional): Filter by source (e.g., "camera_1", "central")
    - **level** (optional): Filter by level ("INFO", "WARNING", "ERROR")
    - **after** (optional): Return logs on or after this timestamp (ISO 8601 format)
      - If not provided, defaults to 15 minutes ago
    - **limit** (optional): Max results (default: 100, max: 500)
    - **offset** (optional): Skip first N results (default: 0)
    
    **Examples:**
    - `/api/v1/logs` - Last 15 minutes of logs
    - `/api/v1/logs?after=2025-10-28T14:00:00` - Logs from Oct 28 14:00 onward
    - `/api/v1/logs?source=camera_1` - Camera 1 logs from last 15 minutes
    - `/api/v1/logs?level=ERROR&after=2025-10-28T00:00:00` - All error logs from Oct 28
    - `/api/v1/logs?source=camera_1&level=ERROR&after=2025-10-28T14:00:00` - Specific filters
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 500:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="limit must be between 1 and 500"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="offset must be non-negative"
            )
        
        # Validate level if provided
        if level and level not in ["INFO", "WARNING", "ERROR"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="level must be one of: INFO, WARNING, ERROR"
            )
        
        # Default to 15 minutes ago if 'after' not provided
        if after is None:
            after = datetime.now(timezone.utc) - timedelta(minutes=15)
        
        # Build query
        query = db.query(Log)
        
        # Filter by timestamp (on or after the specified time)
        query = query.filter(Log.timestamp >= after)
        
        # Filter by source if provided
        if source:
            query = query.filter(Log.source == source)
        
        # Filter by level if provided
        if level:
            query = query.filter(Log.level == level)
        
        # Get total count
        total = query.count()
        
        # Sort by timestamp DESC (newest first)
        query = query.order_by(Log.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute
        logs = query.all()
        
        logger.info(f"Returning {len(logs)} logs (total: {total}, source: {source}, level: {level}, after: {after})")
        
        # Convert SQLAlchemy Log objects to Pydantic LogResponse objects
        # This ensures the types match LogListResponse (List[LogResponse])
        logs_out = [LogResponse.from_orm(l) for l in logs]
        
        return LogListResponse(
            logs=logs_out,
            total=total,
            limit=limit,
            offset=offset
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )