-- Migration: Add status column to events table
-- Date: 2025-11-06
-- Purpose: Track event processing status (complete, interrupted, failed)

-- Add status column
ALTER TABLE events 
ADD COLUMN status VARCHAR(20) DEFAULT 'processing' 
COMMENT 'Event processing status: processing, complete, interrupted, failed'
AFTER created_at;

-- Add index for status queries
CREATE INDEX idx_status ON events(status);

-- Update existing events to 'complete' status
-- (They were processed before this feature existed)
UPDATE events 
SET status = 'complete' 
WHERE status = 'processing';

-- Verify migration
SELECT 
    COUNT(*) as total_events,
    status,
    COUNT(*) as count_per_status
FROM events
GROUP BY status;

-- Expected output after migration:
-- All existing events should show status = 'complete'
-- New events will start with status = 'processing'