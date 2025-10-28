-- ============================================================================
-- Security Camera System - Database Test Script
-- ============================================================================
-- Purpose: Validate database schema and test basic operations
-- Usage: mysql -u securitycam -p security_cameras < test_database.sql
-- ============================================================================

USE security_cameras;

SELECT '============================================' AS '';
SELECT 'Security Camera Database - Test Suite' AS '';
SELECT '============================================' AS '';
SELECT '' AS '';

-- ============================================================================
-- TEST 1: Verify Tables Exist
-- ============================================================================

SELECT 'TEST 1: Verify Tables Exist' AS '';
SELECT '------------------------------------' AS '';

SELECT COUNT(*) AS table_count, 
       'Expected: 3' AS expected
FROM information_schema.tables 
WHERE table_schema = 'security_cameras';

SHOW TABLES;

SELECT '' AS '';

-- ============================================================================
-- TEST 2: Verify Table Structures
-- ============================================================================

SELECT 'TEST 2: Verify Table Structures' AS '';
SELECT '------------------------------------' AS '';

SELECT 'cameras table:' AS '';
DESCRIBE cameras;
SELECT '' AS '';

SELECT 'events table:' AS '';
DESCRIBE events;
SELECT '' AS '';

SELECT 'logs table:' AS '';
DESCRIBE logs;
SELECT '' AS '';

-- ============================================================================
-- TEST 3: Verify Indexes
-- ============================================================================

SELECT 'TEST 3: Verify Indexes' AS '';
SELECT '------------------------------------' AS '';

SELECT table_name, index_name, column_name
FROM information_schema.statistics
WHERE table_schema = 'security_cameras'
ORDER BY table_name, index_name, seq_in_index;

SELECT '' AS '';

-- ============================================================================
-- TEST 4: Insert Test Camera
-- ============================================================================

SELECT 'TEST 4: Insert Test Camera' AS '';
SELECT '------------------------------------' AS '';

-- Clean up any existing test data first
DELETE FROM logs WHERE source = 'test_camera';
DELETE FROM events WHERE camera_id = 'test_camera';
DELETE FROM cameras WHERE camera_id = 'test_camera';

-- Insert test camera
INSERT INTO cameras (camera_id, name, location, ip_address, status)
VALUES ('test_camera', 'Test Camera', 'Test Location', '192.168.1.99', 'online');

SELECT 'Inserted camera:' AS '';
SELECT * FROM cameras WHERE camera_id = 'test_camera';

SELECT '' AS '';

-- ============================================================================
-- TEST 5: Insert Test Event
-- ============================================================================

SELECT 'TEST 5: Insert Test Event' AS '';
SELECT '------------------------------------' AS '';

INSERT INTO events (
    camera_id, 
    timestamp, 
    motion_score,
    image_a_path,
    thumbnail_path,
    image_a_transferred,
    thumbnail_transferred
)
VALUES (
    'test_camera',
    NOW(6),
    75.5,
    'test_camera/pictures/1_20251027_120000_a.jpg',
    'test_camera/thumbs/1_20251027_120000_thumb.jpg',
    TRUE,
    TRUE
);

SELECT 'Inserted event:' AS '';
SELECT id, camera_id, timestamp, motion_score, 
       image_a_path, image_a_transferred,
       thumbnail_path, thumbnail_transferred,
       mp4_conversion_status
FROM events 
WHERE camera_id = 'test_camera';

SELECT '' AS '';

-- ============================================================================
-- TEST 6: Update Event with Additional Files
-- ============================================================================

SELECT 'TEST 6: Update Event with Additional Files' AS '';
SELECT '------------------------------------' AS '';

-- Get the event ID we just created
SET @test_event_id = LAST_INSERT_ID();

-- Update with Picture B
UPDATE events 
SET image_b_path = 'test_camera/pictures/1_20251027_120000_b.jpg',
    image_b_transferred = TRUE
WHERE id = @test_event_id;

-- Update with video
UPDATE events 
SET video_h264_path = 'test_camera/videos/1_20251027_120000_video.h264',
    video_duration = 30.5,
    video_transferred = TRUE
WHERE id = @test_event_id;

SELECT 'Updated event:' AS '';
SELECT id, camera_id, 
       image_a_transferred, image_b_transferred, 
       thumbnail_transferred, video_transferred,
       video_duration,
       mp4_conversion_status
FROM events 
WHERE id = @test_event_id;

SELECT '' AS '';

-- ============================================================================
-- TEST 7: Test MP4 Conversion Status Update
-- ============================================================================

SELECT 'TEST 7: MP4 Conversion Status' AS '';
SELECT '------------------------------------' AS '';

-- Simulate MP4 conversion starting
UPDATE events 
SET mp4_conversion_status = 'processing'
WHERE id = @test_event_id;

SELECT 'Status: processing' AS '';
SELECT id, mp4_conversion_status, mp4_converted_at
FROM events 
WHERE id = @test_event_id;

-- Simulate MP4 conversion complete
UPDATE events 
SET mp4_conversion_status = 'complete',
    mp4_converted_at = NOW(6),
    video_mp4_path = 'test_camera/videos/1_20251027_120000_video.mp4'
WHERE id = @test_event_id;

SELECT 'Status: complete' AS '';
SELECT id, mp4_conversion_status, mp4_converted_at, video_mp4_path
FROM events 
WHERE id = @test_event_id;

SELECT '' AS '';

-- ============================================================================
-- TEST 8: Insert Test Logs
-- ============================================================================

SELECT 'TEST 8: Insert Test Logs' AS '';
SELECT '------------------------------------' AS '';

INSERT INTO logs (source, level, message)
VALUES 
    ('test_camera', 'INFO', 'Test log message 1'),
    ('test_camera', 'WARNING', 'Test log message 2'),
    ('test_camera', 'ERROR', 'Test log message 3'),
    ('central', 'INFO', 'Central server test log');

SELECT 'Inserted logs:' AS '';
SELECT id, source, timestamp, level, message
FROM logs
WHERE source IN ('test_camera', 'central')
ORDER BY timestamp DESC;

SELECT '' AS '';

-- ============================================================================
-- TEST 9: Test Foreign Key Constraint
-- ============================================================================

SELECT 'TEST 9: Foreign Key Constraint' AS '';
SELECT '------------------------------------' AS '';

-- Attempt to insert event with non-existent camera (should fail)
SELECT 'Attempting to insert event with invalid camera_id...' AS '';

-- This should produce an error
INSERT INTO events (camera_id, timestamp, motion_score)
VALUES ('nonexistent_camera', NOW(6), 50.0);

-- If we get here, foreign key constraint failed
SELECT 'ERROR: Foreign key constraint did not prevent invalid insert!' AS '';

SELECT '' AS '';

-- ============================================================================
-- TEST 10: Query Performance Tests
-- ============================================================================

SELECT 'TEST 10: Query Performance (Index Usage)' AS '';
SELECT '------------------------------------' AS '';

-- Test 1: Events by camera and date (should use idx_camera_timestamp)
EXPLAIN SELECT * FROM events 
WHERE camera_id = 'test_camera' 
ORDER BY timestamp DESC 
LIMIT 10;

SELECT '' AS '';

-- Test 2: Events needing MP4 conversion (should use idx_mp4_status)
EXPLAIN SELECT * FROM events 
WHERE mp4_conversion_status = 'pending' 
LIMIT 10;

SELECT '' AS '';

-- Test 3: Logs by source (should use idx_source_timestamp)
EXPLAIN SELECT * FROM logs 
WHERE source = 'test_camera' 
ORDER BY timestamp DESC 
LIMIT 10;

SELECT '' AS '';

-- ============================================================================
-- TEST 11: Count Statistics
-- ============================================================================

SELECT 'TEST 11: Database Statistics' AS '';
SELECT '------------------------------------' AS '';

SELECT 
    (SELECT COUNT(*) FROM cameras) AS total_cameras,
    (SELECT COUNT(*) FROM events) AS total_events,
    (SELECT COUNT(*) FROM logs) AS total_logs;

SELECT '' AS '';

-- ============================================================================
-- TEST 12: Clean Up Test Data
-- ============================================================================

SELECT 'TEST 12: Cleaning Up Test Data' AS '';
SELECT '------------------------------------' AS '';

-- Delete test logs
DELETE FROM logs WHERE source IN ('test_camera', 'central');
SELECT 'Deleted test logs' AS '';

-- Delete test events (will cascade delete due to foreign key)
DELETE FROM events WHERE camera_id = 'test_camera';
SELECT 'Deleted test events' AS '';

-- Delete test camera
DELETE FROM cameras WHERE camera_id = 'test_camera';
SELECT 'Deleted test camera' AS '';

-- Verify cleanup
SELECT 
    (SELECT COUNT(*) FROM cameras WHERE camera_id = 'test_camera') AS remaining_cameras,
    (SELECT COUNT(*) FROM events WHERE camera_id = 'test_camera') AS remaining_events,
    (SELECT COUNT(*) FROM logs WHERE source IN ('test_camera', 'central')) AS remaining_logs;

SELECT '' AS '';

-- ============================================================================
-- TEST SUMMARY
-- ============================================================================

SELECT '============================================' AS '';
SELECT 'Test Suite Complete!' AS '';
SELECT '============================================' AS '';
SELECT '' AS '';
SELECT 'Expected Results:' AS '';
SELECT '✓ All 3 tables exist' AS '';
SELECT '✓ All indexes created' AS '';
SELECT '✓ Test camera inserted and queried' AS '';
SELECT '✓ Test event created and updated' AS '';
SELECT '✓ MP4 conversion status tracking works' AS '';
SELECT '✓ Logs inserted successfully' AS '';
SELECT '✓ Foreign key constraint failed (expected)' AS '';
SELECT '✓ Indexes used in queries (EXPLAIN output)' AS '';
SELECT '✓ Test data cleaned up' AS '';
SELECT '' AS '';
SELECT 'Note: TEST 9 (Foreign Key Constraint) should produce' AS '';
SELECT 'an error message - this is expected and correct!' AS '';
SELECT '' AS '';

-- ============================================================================
-- END OF TEST SCRIPT
-- ============================================================================