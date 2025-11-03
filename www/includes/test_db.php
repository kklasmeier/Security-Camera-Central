<?php
/**
 * Test Script for New Database Class and Functions
 * Run this from command line: php test_db.php
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "=================================================\n";
echo "Security Camera Database Migration Test Suite\n";
echo "=================================================\n\n";

// Include files
require_once 'config.php';
require_once 'db.php';
require_once 'functions.php';

$test_results = [];
$total_tests = 0;
$passed_tests = 0;

/**
 * Helper function to run a test
 */
function run_test($name, $callback) {
    global $test_results, $total_tests, $passed_tests;
    
    $total_tests++;
    echo "Test {$total_tests}: {$name}... ";
    
    try {
        $result = $callback();
        if ($result === true) {
            echo "✓ PASS\n";
            $test_results[] = ['name' => $name, 'status' => 'PASS'];
            $passed_tests++;
            return true;
        } else {
            echo "✗ FAIL: {$result}\n";
            $test_results[] = ['name' => $name, 'status' => 'FAIL', 'reason' => $result];
            return false;
        }
    } catch (Exception $e) {
        echo "✗ ERROR: " . $e->getMessage() . "\n";
        $test_results[] = ['name' => $name, 'status' => 'ERROR', 'reason' => $e->getMessage()];
        return false;
    }
}

// ========================================
// TEST 1: Configuration Loading
// ========================================
run_test("Config - Database credentials loaded", function() {
    if (empty(DB_HOST)) return "DB_HOST not defined";
    if (empty(DB_NAME)) return "DB_NAME not defined";
    if (empty(DB_USER)) return "DB_USER not defined";
    if (empty(DB_PASS)) return "DB_PASS not defined";
    
    echo "\n    DB_HOST: " . DB_HOST;
    echo "\n    DB_NAME: " . DB_NAME;
    echo "\n    DB_USER: " . DB_USER;
    echo "\n    DB_PASS: " . str_repeat('*', strlen(DB_PASS)) . " ";
    
    return true;
});

run_test("Config - Media paths configured", function() {
    if (empty(MEDIA_ROOT)) return "MEDIA_ROOT not defined";
    if (empty(MEDIA_URL_PREFIX)) return "MEDIA_URL_PREFIX not defined";
    
    echo "\n    MEDIA_ROOT: " . MEDIA_ROOT;
    echo "\n    MEDIA_URL_PREFIX: " . MEDIA_URL_PREFIX . " ";
    
    return true;
});

// ========================================
// TEST 2: Database Connection
// ========================================
$db = new Database();

run_test("Database - Connection established", function() use ($db) {
    if (!$db->isConnected()) {
        return "Failed to connect to database";
    }
    return true;
});

// ========================================
// TEST 3: Camera Methods
// ========================================
run_test("Cameras - Get all cameras", function() use ($db) {
    $cameras = $db->get_all_cameras();
    
    if (!is_array($cameras)) {
        return "Expected array, got " . gettype($cameras);
    }
    
    if (empty($cameras)) {
        return "No cameras found in database";
    }
    
    echo "\n    Found " . count($cameras) . " cameras:";
    foreach ($cameras as $camera) {
        echo "\n      - {$camera['camera_id']}: {$camera['name']} ({$camera['status']})";
    }
    echo " ";
    
    return true;
});

run_test("Cameras - Get specific camera (camera_1)", function() use ($db) {
    $camera = $db->get_camera_by_id('camera_1');
    
    if ($camera === null) {
        return "Camera 'camera_1' not found";
    }
    
    if (!isset($camera['name']) || !isset($camera['camera_id'])) {
        return "Camera record missing required fields";
    }
    
    echo "\n    Camera: {$camera['camera_id']} - {$camera['name']} ";
    
    return true;
});

run_test("Cameras - Get camera name", function() use ($db) {
    $name = $db->get_camera_name('camera_1');
    
    if (empty($name)) {
        return "Failed to get camera name";
    }
    
    echo "\n    camera_1 name: {$name} ";
    
    return true;
});

// ========================================
// TEST 4: Event Methods
// ========================================
run_test("Events - Get total event count", function() use ($db) {
    $count = $db->get_event_count();
    
    if (!is_int($count)) {
        return "Expected integer, got " . gettype($count);
    }
    
    echo "\n    Total events: {$count} ";
    
    return true;
});

run_test("Events - Get event count by camera (camera_1)", function() use ($db) {
    $count = $db->get_event_count('camera_1');
    
    if (!is_int($count)) {
        return "Expected integer, got " . gettype($count);
    }
    
    echo "\n    camera_1 events: {$count} ";
    
    return true;
});

run_test("Events - Get recent events (all cameras)", function() use ($db) {
    $events = $db->get_recent_events(10, 0);
    
    if (!is_array($events)) {
        return "Expected array, got " . gettype($events);
    }
    
    if (empty($events)) {
        return "No events found";
    }
    
    echo "\n    Retrieved " . count($events) . " events";
    echo "\n    Most recent: {$events[0]['camera_id']} at {$events[0]['timestamp']} (score: {$events[0]['motion_score']}) ";
    
    return true;
});

run_test("Events - Get recent events (camera_1 only)", function() use ($db) {
    $events = $db->get_recent_events(10, 0, 'camera_1');
    
    if (!is_array($events)) {
        return "Expected array, got " . gettype($events);
    }
    
    // Verify all events are from camera_1
    foreach ($events as $event) {
        if ($event['camera_id'] !== 'camera_1') {
            return "Found event from wrong camera: {$event['camera_id']}";
        }
    }
    
    echo "\n    Retrieved " . count($events) . " events from camera_1 ";
    
    return true;
});

run_test("Events - Get specific event by ID", function() use ($db) {
    // First get a valid event ID
    $events = $db->get_recent_events(1, 0);
    if (empty($events)) {
        return "No events available to test";
    }
    
    $event_id = $events[0]['id'];
    $event = $db->get_event_by_id($event_id);
    
    if ($event === null) {
        return "Failed to retrieve event {$event_id}";
    }
    
    if ($event['id'] != $event_id) {
        return "Retrieved wrong event";
    }
    
    echo "\n    Event #{$event_id}: {$event['camera_id']} at {$event['timestamp']} ";
    
    return true;
});

run_test("Events - Navigation (next/previous)", function() use ($db) {
    // Get a middle event
    $events = $db->get_recent_events(100, 50);
    if (empty($events)) {
        return "No events available to test";
    }
    
    $event_id = $events[0]['id'];
    
    $next = $db->get_next_event_id($event_id);
    $prev = $db->get_previous_event_id($event_id);
    
    if ($next === null && $prev === null) {
        return "Both next and previous are null (unexpected)";
    }
    
    echo "\n    Event #{$event_id}: prev={$prev}, next={$next} ";
    
    return true;
});

// ========================================
// TEST 5: Log Methods
// ========================================
run_test("Logs - Get log count", function() use ($db) {
    $count = $db->get_log_count();
    
    if (!is_int($count)) {
        return "Expected integer, got " . gettype($count);
    }
    
    echo "\n    Total logs: {$count} ";
    
    return true;
});

run_test("Logs - Get logs with level filter", function() use ($db) {
    $logs = $db->get_logs(100, 0, ['ERROR'], 'DESC');
    
    if (!is_array($logs)) {
        return "Expected array, got " . gettype($logs);
    }
    
    // Verify all logs are ERROR level
    foreach ($logs as $log) {
        if ($log['level'] !== 'ERROR') {
            return "Found log with wrong level: {$log['level']}";
        }
    }
    
    echo "\n    Retrieved " . count($logs) . " ERROR logs ";
    
    return true;
});

run_test("Logs - Get logs with source filter", function() use ($db) {
    $logs = $db->get_logs(100, 0, null, 'DESC', 'camera_1');
    
    if (!is_array($logs)) {
        return "Expected array, got " . gettype($logs);
    }
    
    // Verify all logs are from camera_1
    foreach ($logs as $log) {
        if ($log['source'] !== 'camera_1') {
            return "Found log from wrong source: {$log['source']}";
        }
    }
    
    echo "\n    Retrieved " . count($logs) . " logs from camera_1 ";
    
    return true;
});

// ========================================
// TEST 6: Helper Functions
// ========================================
run_test("Functions - Format event timestamp", function() {
    $timestamp = date('Y-m-d H:i:s'); // Today
    $formatted = format_event_timestamp($timestamp);
    
    if (strpos($formatted, 'Today') === false) {
        return "Expected 'Today' in formatted timestamp, got: {$formatted}";
    }
    
    echo "\n    Formatted: {$formatted} ";
    
    return true;
});

run_test("Functions - Get motion badge", function() {
    $low = get_motion_badge(100);
    $medium = get_motion_badge(200);
    $high = get_motion_badge(300);
    
    if ($low['color'] !== 'low') return "Low badge incorrect";
    if ($medium['color'] !== 'medium') return "Medium badge incorrect";
    if ($high['color'] !== 'high') return "High badge incorrect";
    
    echo "\n    Low: {$low['label']}, Medium: {$medium['label']}, High: {$high['label']} ";
    
    return true;
});

run_test("Functions - Get thumbnail URL", function() use ($db) {
    $events = $db->get_recent_events(1, 0);
    if (empty($events)) {
        return "No events available";
    }
    
    $url = get_thumbnail_url($events[0]);
    
    if (empty($url)) {
        return "Failed to generate thumbnail URL";
    }
    
    echo "\n    URL: {$url} ";
    
    return true;
});

run_test("Functions - Path conversion (relative to web URL)", function() use ($db) {
    $events = $db->get_recent_events(1, 0);
    if (empty($events)) {
        return "No events available";
    }
    
    $event = $events[0];
    
    // Check if paths are converted correctly
    if (!empty($event['thumbnail_path'])) {
        $url = get_thumbnail_url($event);
        
        if (substr($url, 0, strlen(MEDIA_URL_PREFIX)) !== MEDIA_URL_PREFIX && substr($url, 0, 5) !== 'data:') {
            return "URL doesn't start with correct prefix: {$url}";
        }
        
        echo "\n    DB path: {$event['thumbnail_path']}";
        echo "\n    Web URL: {$url} ";
    }
    
    return true;
});

// ========================================
// TEST 7: Streaming Control (Placeholder)
// ========================================
run_test("Streaming - Get flag (placeholder)", function() use ($db) {
    $flag = $db->get_streaming_flag('camera_1');
    
    if (!is_int($flag)) {
        return "Expected integer, got " . gettype($flag);
    }
    
    echo "\n    Flag value: {$flag} ";
    
    return true;
});

run_test("Streaming - Set flag (placeholder)", function() use ($db) {
    $result = $db->set_streaming_flag(1, 'camera_1');
    
    if (!is_bool($result)) {
        return "Expected boolean, got " . gettype($result);
    }
    
    echo "\n    Result: " . ($result ? 'true' : 'false') . " ";
    
    return true;
});

// ========================================
// Summary
// ========================================
echo "\n=================================================\n";
echo "Test Summary\n";
echo "=================================================\n";
echo "Total Tests: {$total_tests}\n";
echo "Passed: {$passed_tests}\n";
echo "Failed: " . ($total_tests - $passed_tests) . "\n";
echo "Success Rate: " . round(($passed_tests / $total_tests) * 100, 1) . "%\n";

if ($passed_tests === $total_tests) {
    echo "\n✓ All tests passed! Database migration successful.\n";
    exit(0);
} else {
    echo "\n✗ Some tests failed. Review errors above.\n";
    exit(1);
}
?>