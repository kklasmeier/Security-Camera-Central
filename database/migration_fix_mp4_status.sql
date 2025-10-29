-- ============================================================================
-- Migration: Fix MP4 Conversion Status Fields
-- ============================================================================
-- 
-- Changes:
--   OLD: mp4_conversion_pending, mp4_conversion_complete, mp4_conversion_error
--   NEW: mp4_conversion_status, mp4_converted_at
-- 
-- Also adds missing fields from spec:
--   - Rename picture_* to image_*
--   - Add video_duration
--   - Add AI analysis fields (Phase 2 prep)
-- 
-- Run this on the security_cameras database
-- ============================================================================

USE security_cameras;

-- Step 1: Drop old MP4 conversion fields
ALTER TABLE events DROP COLUMN IF EXISTS mp4_conversion_pending;
ALTER TABLE events DROP COLUMN IF EXISTS mp4_conversion_complete;
ALTER TABLE events DROP COLUMN IF EXISTS mp4_conversion_error;

-- Step 2: Add new MP4 conversion fields
ALTER TABLE events ADD COLUMN mp4_conversion_status VARCHAR(20) DEFAULT 'pending' AFTER video_transferred;
ALTER TABLE events ADD COLUMN mp4_converted_at DATETIME NULL AFTER mp4_conversion_status;

-- Step 3: Rename picture_* columns to image_* (if they exist)
-- Check if old column names exist and rename them
ALTER TABLE events CHANGE COLUMN picture_a_path image_a_path VARCHAR(255) NULL;
ALTER TABLE events CHANGE COLUMN picture_b_path image_b_path VARCHAR(255) NULL;
ALTER TABLE events CHANGE COLUMN picture_a_transferred image_a_transferred BOOLEAN DEFAULT FALSE;
ALTER TABLE events CHANGE COLUMN picture_b_transferred image_b_transferred BOOLEAN DEFAULT FALSE;

-- Step 4: Add video_duration field (if not exists)
ALTER TABLE events ADD COLUMN IF NOT EXISTS video_duration FLOAT NULL AFTER video_mp4_path;

-- Step 5: Add AI analysis fields (Phase 2 preparation)
ALTER TABLE events ADD COLUMN IF NOT EXISTS ai_processed BOOLEAN DEFAULT FALSE AFTER mp4_converted_at;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ai_processed_at DATETIME NULL AFTER ai_processed;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ai_person_detected BOOLEAN NULL AFTER ai_processed_at;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ai_confidence FLOAT NULL AFTER ai_person_detected;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ai_objects TEXT NULL AFTER ai_confidence;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ai_description TEXT NULL AFTER ai_objects;

-- Step 6: Verify changes
SELECT 
    'Migration complete - verify columns below:' AS status;

DESCRIBE events;

-- Step 7: Show sample of updated structure
SELECT 
    id,
    camera_id,
    timestamp,
    image_a_transferred,
    image_b_transferred,
    thumbnail_transferred,
    video_transferred,
    mp4_conversion_status,
    mp4_converted_at,
    ai_processed
FROM events
LIMIT 5;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- Uncomment and run these commands if you need to rollback:
--
-- ALTER TABLE events DROP COLUMN mp4_conversion_status;
-- ALTER TABLE events DROP COLUMN mp4_converted_at;
-- ALTER TABLE events DROP COLUMN video_duration;
-- ALTER TABLE events DROP COLUMN ai_processed;
-- ALTER TABLE events DROP COLUMN ai_processed_at;
-- ALTER TABLE events DROP COLUMN ai_person_detected;
-- ALTER TABLE events DROP COLUMN ai_confidence;
-- ALTER TABLE events DROP COLUMN ai_objects;
-- ALTER TABLE events DROP COLUMN ai_description;
--
-- ALTER TABLE events ADD COLUMN mp4_conversion_pending BOOLEAN DEFAULT FALSE;
-- ALTER TABLE events ADD COLUMN mp4_conversion_complete BOOLEAN DEFAULT FALSE;
-- ALTER TABLE events ADD COLUMN mp4_conversion_error TEXT NULL;
--
-- ALTER TABLE events CHANGE COLUMN image_a_path picture_a_path VARCHAR(255) NULL;
-- ALTER TABLE events CHANGE COLUMN image_b_path picture_b_path VARCHAR(255) NULL;
-- ALTER TABLE events CHANGE COLUMN image_a_transferred picture_a_transferred BOOLEAN DEFAULT FALSE;
-- ALTER TABLE events CHANGE COLUMN image_b_transferred picture_b_transferred BOOLEAN DEFAULT FALSE;
-- ============================================================================