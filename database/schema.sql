-- ============================================================================
-- Security Camera System - Database Schema
-- ============================================================================
-- Purpose: Multi-camera security system with centralized event storage
-- Database: MariaDB 10.5+
-- Tables: cameras, events, logs
-- ============================================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS security_cameras
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Use the database
USE security_cameras;

-- ============================================================================
-- TABLE 1: cameras
-- ============================================================================
-- Stores metadata about each camera in the system
-- Each camera registers itself on startup via the API

CREATE TABLE IF NOT EXISTS cameras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL COMMENT 'User-defined identifier (e.g., camera_1)',
    name VARCHAR(100) COMMENT 'Human-readable name (e.g., Front Door)',
    location VARCHAR(200) COMMENT 'Physical location description',
    ip_address VARCHAR(45) COMMENT 'Camera IP address for MJPEG streaming',
    last_seen DATETIME(6) COMMENT 'Last heartbeat timestamp (Phase 2)',
    status VARCHAR(20) DEFAULT 'offline' COMMENT 'Camera status: online, offline, error',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'When camera first registered',
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Last metadata update',
    
    INDEX idx_camera_id (camera_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Camera registration and metadata';

-- ============================================================================
-- TABLE 2: events
-- ============================================================================
-- Stores motion detection events with associated files
-- One row per event, progressively updated as files arrive

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Event ID used in filenames',
    camera_id VARCHAR(50) NOT NULL COMMENT 'Which camera detected this event',
    timestamp DATETIME(6) NOT NULL COMMENT 'When motion was detected',
    motion_score FLOAT COMMENT 'Number of changed pixels that triggered detection',
    
    -- File paths (relative to /mnt/security_footage)
    image_a_path VARCHAR(500) COMMENT 'Picture A (T+0s): camera_1/pictures/42_20251026_143022_a.jpg',
    image_b_path VARCHAR(500) COMMENT 'Picture B (T+4s): camera_1/pictures/42_20251026_143022_b.jpg',
    thumbnail_path VARCHAR(500) COMMENT 'Thumbnail: camera_1/thumbs/42_20251026_143022_thumb.jpg',
    video_h264_path VARCHAR(500) COMMENT 'Raw H.264 video: camera_1/videos/42_20251026_143022_video.h264',
    video_mp4_path VARCHAR(500) COMMENT 'Converted MP4 video: camera_1/videos/42_20251026_143022_video.mp4',
    video_duration FLOAT COMMENT 'Video length in seconds (estimated by camera)',
    
    -- Transfer status (updated by cameras as files arrive)
    image_a_transferred BOOLEAN DEFAULT FALSE COMMENT 'TRUE when Picture A on NFS',
    image_b_transferred BOOLEAN DEFAULT FALSE COMMENT 'TRUE when Picture B on NFS',
    thumbnail_transferred BOOLEAN DEFAULT FALSE COMMENT 'TRUE when thumbnail on NFS',
    video_transferred BOOLEAN DEFAULT FALSE COMMENT 'TRUE when H.264 video on NFS',
    
    -- MP4 conversion status (managed by central server worker)
    mp4_conversion_status VARCHAR(20) DEFAULT 'pending' COMMENT 'Values: pending, processing, complete, failed',
    mp4_converted_at DATETIME(6) COMMENT 'When MP4 conversion completed',
    
    -- AI analysis (Phase 2 - columns reserved now)
    ai_processed BOOLEAN DEFAULT FALSE COMMENT 'TRUE when AI analysis complete',
    ai_processed_at DATETIME(6) COMMENT 'When AI analysis completed',
    ai_person_detected BOOLEAN COMMENT 'TRUE if person detected in images',
    ai_confidence FLOAT COMMENT 'AI confidence score (0.0 to 1.0)',
    ai_objects JSON COMMENT 'Detected objects as JSON array',
    ai_description TEXT COMMENT 'AI-generated description of the event',
    
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'When event record created',
    
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE,
    
    INDEX idx_camera_timestamp (camera_id, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_mp4_status (mp4_conversion_status),
    INDEX idx_ai_processed (ai_processed),
    INDEX idx_person_detected (ai_person_detected)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Motion detection events with file tracking';

-- ============================================================================
-- TABLE 3: logs
-- ============================================================================
-- Centralized logging from all cameras and central server
-- Allows viewing logs by source (camera_1, camera_2, central, etc.)

CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(50) NOT NULL COMMENT 'Log source: camera_1, camera_2, camera_3, camera_4, central',
    timestamp DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'When log entry created',
    level VARCHAR(20) NOT NULL COMMENT 'Log level: INFO, WARNING, ERROR',
    message TEXT NOT NULL COMMENT 'Log message content',
    
    INDEX idx_source (source),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_level (level),
    INDEX idx_source_timestamp (source, timestamp DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Centralized logging from all components';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show created tables
SHOW TABLES;

-- Show table structures
DESCRIBE cameras;
DESCRIBE events;
DESCRIBE logs;

-- Show indexes
SHOW INDEX FROM cameras;
SHOW INDEX FROM events;
SHOW INDEX FROM logs;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. All DATETIME fields use microsecond precision DATETIME(6)
-- 2. All file paths are relative to /mnt/security_footage
-- 3. AI columns are NULL until Phase 2 implementation
-- 4. Foreign key CASCADE: deleting a camera deletes all its events
-- 5. Indexes optimized for common queries:
--    - Events by camera and date
--    - Events needing MP4 conversion
--    - Logs by source and date
-- ============================================================================