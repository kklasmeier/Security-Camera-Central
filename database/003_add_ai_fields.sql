-- Migration script to add AI processing fields to events table
-- Run this on the security_cameras database

USE security_cameras;

-- Add ai_phrase field (short phrase from deepseek)
ALTER TABLE events 
ADD COLUMN ai_phrase VARCHAR(500) NULL 
AFTER ai_description;

-- Add ai_error field (error messages from failed AI processing)
ALTER TABLE events 
ADD COLUMN ai_error TEXT NULL 
AFTER ai_phrase;

-- Verify the changes
DESCRIBE events;