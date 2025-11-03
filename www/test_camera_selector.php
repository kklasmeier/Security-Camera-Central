<?php
require_once 'includes/session.php';
require_once 'includes/db.php';
require_once 'includes/camera_selector.php';

// Handle form submission
handle_camera_selection();

$selected = get_selected_camera();
?>
<!DOCTYPE html>
<html>
<head>
    <title>Camera Selector Test</title>
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
            margin-bottom: 10px;
        }
        
        h2 {
            color: #ffffff;
            margin-top: 30px;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .info-box {
            background: #2a2a2a;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        
        .info-box strong {
            color: #4CAF50;
        }
        
        .camera-selector-form {
            background: #2a2a2a;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .camera-selector-form label {
            margin-right: 10px;
            font-weight: 500;
            color: #e0e0e0;
        }
        
        .camera-selector-form select {
            padding: 8px 12px;
            border: 1px solid #404040;
            border-radius: 4px;
            background: #1a1a1a;
            color: #e0e0e0;
            font-size: 14px;
            cursor: pointer;
        }
        
        .camera-selector-form select:hover {
            border-color: #4CAF50;
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
        }
        
        .test-section {
            margin: 30px 0;
        }
    </style>
</head>
<body>
    <h1>Camera Selector Component Test</h1>
    
    <div class="info-box">
        <strong>Currently Selected:</strong> <?php echo htmlspecialchars($selected); ?>
    </div>
    
    <div class="test-section">
        <?php render_camera_selector('test_camera_selector.php'); ?>
    </div>
    
    <h2>Test Instructions:</h2>
    <ol>
        <li>Select different cameras from the dropdown</li>
        <li>Verify page auto-submits on change</li>
        <li>Verify "Currently Selected" updates after each change</li>
        <li>Verify correct option is pre-selected in dropdown</li>
        <li>Try refreshing (F5) - should not ask to resubmit form</li>
    </ol>
    
    <h2>Session Debug</h2>
    <pre><?php print_r($_SESSION); ?></pre>
</body>
</html>