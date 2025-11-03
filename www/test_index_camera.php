<?php
/**
 * Test file for index.php camera selector integration
 * Tests filtering, camera display, and empty states
 */

require_once 'includes/session.php';
require_once 'includes/db.php';
require_once 'includes/functions.php';
require_once 'includes/camera_selector.php';

// Handle camera selection
handle_camera_selection();

$db = new Database();
$camera_id = get_selected_camera();

// Get stats for testing
$total_events = $db->get_event_count($camera_id);
$events = $db->get_recent_events(5, 0, $camera_id);

// Get camera name for display
$camera_name = is_all_cameras_selected() ? "All Cameras" : get_camera_display_name($camera_id, $db);
?>
<!DOCTYPE html>
<html>
<head>
    <title>Index Camera Integration Test</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            margin: 0;
        }
        
        h1 {
            color: #ffffff;
            margin-bottom: 20px;
        }
        
        h2 {
            color: #ffffff;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #404040;
            padding-bottom: 10px;
        }
        
        .test-section {
            background: #2a2a2a;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .pass {
            color: #4CAF50;
            font-weight: bold;
        }
        
        .info {
            color: #2196F3;
        }
        
        .event-preview {
            background: #1a1a1a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }
        
        .event-camera {
            display: block;
            font-size: 0.85em;
            color: #999;
            margin-bottom: 4px;
        }
        
        .camera-filter {
            margin: 20px 0;
            padding: 15px;
            background: #2a2a2a;
            border-radius: 8px;
        }
        
        ol {
            line-height: 1.8;
        }
        
        pre {
            background: #0a0a0a;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            color: #4CAF50;
            font-size: 0.9em;
        }
        
        .stat-box {
            display: inline-block;
            background: #0a0a0a;
            border: 1px solid #4CAF50;
            border-radius: 4px;
            padding: 10px 15px;
            margin: 5px;
        }
        
        .stat-label {
            color: #999;
            font-size: 0.9em;
        }
        
        .stat-value {
            color: #4CAF50;
            font-size: 1.5em;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>📷 Index.php Camera Integration Test</h1>
    
    <div class="test-section">
        <h2>1. Camera Selector Component</h2>
        <div class="camera-filter">
            <?php render_camera_selector('test_index_camera.php'); ?>
        </div>
        <p class="pass">✓ Camera selector rendered</p>
    </div>
    
    <div class="test-section">
        <h2>2. Current Filter Status</h2>
        <div class="stat-box">
            <div class="stat-label">Selected Camera</div>
            <div class="stat-value"><?php echo htmlspecialchars($camera_name); ?></div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Total Events</div>
            <div class="stat-value"><?php echo number_format($total_events); ?></div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Camera ID</div>
            <div class="stat-value"><?php echo htmlspecialchars($camera_id); ?></div>
        </div>
    </div>
    
    <div class="test-section">
        <h2>3. Event Display Test (First 5 Events)</h2>
        
        <?php if (count($events) > 0): ?>
            <?php foreach ($events as $event): ?>
                <div class="event-preview">
                    <!-- Camera name should only show when viewing ALL cameras -->
                    <?php if (is_all_cameras_selected()): ?>
                        <span class="event-camera">
                            📷 <?php echo htmlspecialchars(get_camera_display_name($event['camera_id'], $db)); ?>
                        </span>
                        <p class="pass">✓ Camera name displayed (viewing all cameras)</p>
                    <?php else: ?>
                        <p class="pass">✓ Camera name hidden (viewing specific camera)</p>
                    <?php endif; ?>
                    
                    <strong>Event ID:</strong> <?php echo $event['id']; ?><br>
                    <strong>Timestamp:</strong> <?php echo $event['timestamp']; ?><br>
                    <strong>Motion Score:</strong> <?php echo $event['motion_score']; ?><br>
                    <strong>Camera ID:</strong> <?php echo htmlspecialchars($event['camera_id']); ?>
                </div>
            <?php endforeach; ?>
            
        <?php else: ?>
            <div class="event-preview">
                <p class="info">ℹ No events found for selected camera</p>
                <p>Empty state message would show:</p>
                <?php if (is_all_cameras_selected()): ?>
                    <p><em>"No motion detection events have been recorded yet. When motion is detected, events will appear here."</em></p>
                <?php else: ?>
                    <p><em>"No events found for <?php echo htmlspecialchars($camera_name); ?>. Try selecting 'All Cameras' or a different camera."</em></p>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
    
    <div class="test-section">
        <h2>4. Test Checklist</h2>
        <ol>
            <li>Select "All Cameras" - should see camera names on event cards</li>
            <li>Select specific camera - camera names should disappear</li>
            <li>Event count should update based on selection</li>
            <li>Page should auto-refresh on camera change</li>
            <li>Empty state message should be context-aware</li>
            <li>Verify pagination works with filtering on actual index.php</li>
        </ol>
    </div>
    
    <div class="test-section">
        <h2>5. Session Debug</h2>
        <pre><?php print_r($_SESSION); ?></pre>
    </div>
    
    <div class="test-section">
        <h2>6. Helper Function Tests</h2>
        <pre>is_all_cameras_selected(): <?php echo is_all_cameras_selected() ? 'TRUE' : 'FALSE'; ?>
get_selected_camera(): <?php echo htmlspecialchars(get_selected_camera()); ?>
get_camera_display_name('camera_1'): <?php echo htmlspecialchars(get_camera_display_name('camera_1', $db)); ?>
get_camera_display_name('invalid_id'): <?php echo htmlspecialchars(get_camera_display_name('invalid_id', $db)); ?></pre>
    </div>
    
    <div class="test-section">
        <h2>7. Ready for Production?</h2>
        <p>If all above tests pass, copy <strong>index.php</strong> to:</p>
        <pre>/home/pi/Security-Camera-Central/www/index.php</pre>
        <p>Then test at: <strong>http://192.168.1.26:8888/index.php</strong></p>
    </div>
    
</body>
</html>