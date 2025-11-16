-- Migration: Add confidence_score to events table
-- Date: 2025-11-16
-- Description: Add confidence_score column to normalize motion detection sensitivity across cameras

ALTER TABLE events 
ADD COLUMN confidence_score FLOAT NULL 
COMMENT 'Normalized confidence score (0-100%) based on camera-specific thresholds'
AFTER motion_score;

-- Add index for filtering by confidence score (optional, but useful for queries)
CREATE INDEX idx_events_confidence_score ON events(confidence_score);