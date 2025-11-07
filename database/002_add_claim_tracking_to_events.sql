-- Migration: Add claim tracking columns and conversion status index
-- Date: 2025-11-06
-- Purpose: Support atomic job claiming and improve lookup performance 
--           for the MP4 conversion daemon.

-- Add columns for claim tracking
ALTER TABLE events 
ADD COLUMN mp4_claimed_by VARCHAR(64) NULL 
    COMMENT 'Worker identifier that claimed the MP4 conversion job (hostname:pid)'
AFTER mp4_conversion_status,
ADD COLUMN mp4_claimed_at DATETIME(6) NULL 
    COMMENT 'Timestamp when the MP4 conversion job was claimed'
AFTER mp4_claimed_by;

-- Add composite index for faster lookup of pending conversions
CREATE INDEX idx_video_transferred_status 
ON events (video_transferred, mp4_conversion_status);

-- Verify migration
SHOW COLUMNS FROM events LIKE 'mp4_claimed%';
SHOW INDEX FROM events WHERE Key_name = 'idx_video_transferred_status';

-- Expected output after migration:
-- Two new columns: mp4_claimed_by, mp4_claimed_at
-- One new index: idx_video_transferred_status
-- The MP4 converter daemon will use these for efficient job claiming.
