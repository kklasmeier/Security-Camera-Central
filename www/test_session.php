<?php
/**
 * Session Management Test Suite
 * Tests all session functions with edge cases
 * 
 * Access: http://192.168.1.26:8888/test_session.php
 */

require_once 'includes/session.php';

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session Management Tests</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        h1 {
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #2196F3;
            margin-top: 30px;
            padding: 10px;
            background: #2a2a2a;
            border-left: 4px solid #2196F3;
        }
        .test-result {
            background: #2a2a2a;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #666;
        }
        .pass {
            border-left-color: #4CAF50;
        }
        .fail {
            border-left-color: #f44336;
        }
        .result-line {
            margin: 5px 0;
            font-family: 'Courier New', monospace;
        }
        .expected {
            color: #FFC107;
        }
        .actual {
            color: #03A9F4;
        }
        .status {
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 3px;
            display: inline-block;
            margin-left: 10px;
        }
        .status.pass {
            background: #4CAF50;
            color: white;
        }
        .status.fail {
            background: #f44336;
            color: white;
        }
        pre {
            background: #0a0a0a;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border: 1px solid #333;
        }
        .info {
            background: #1565C0;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>🧪 Session Management Test Suite</h1>
    
    <div class="info">
        <strong>Test Environment:</strong><br>
        PHP Version: <?php echo PHP_VERSION; ?><br>
        Session Status: <?php echo session_status() === PHP_SESSION_ACTIVE ? 'Active' : 'Inactive'; ?><br>
        Session ID: <?php echo session_id(); ?>
    </div>

<?php

// Test counter
$test_number = 0;
$passes = 0;
$fails = 0;

/**
 * Helper function to run a test
 */
function run_test($test_name, $expected, $actual) {
    global $test_number, $passes, $fails;
    $test_number++;
    
    $pass = ($expected === $actual);
    $pass ? $passes++ : $fails++;
    
    $status_class = $pass ? 'pass' : 'fail';
    $status_text = $pass ? 'PASS' : 'FAIL';
    
    echo "<div class='test-result $status_class'>";
    echo "<strong>Test $test_number: $test_name</strong>";
    echo "<span class='status $status_class'>$status_text</span><br>";
    echo "<div class='result-line'><span class='expected'>Expected:</span> " . htmlspecialchars(var_export($expected, true)) . "</div>";
    echo "<div class='result-line'><span class='actual'>Actual:</span> " . htmlspecialchars(var_export($actual, true)) . "</div>";
    echo "</div>";
}

// ==============================================================================
// Test 1: Default Selection
// ==============================================================================
echo "<h2>Test 1: Default Selection</h2>";
echo "<p>On first load, session should default to 'all'</p>";

$result = get_selected_camera();
run_test("Default camera selection", 'all', $result);
run_test("is_all_cameras_selected() returns true", true, is_all_cameras_selected());

// ==============================================================================
// Test 2: Set Valid Camera
// ==============================================================================
echo "<h2>Test 2: Set Valid Camera</h2>";
echo "<p>Setting a valid camera ID should persist in session</p>";

set_selected_camera('camera_1');
$result = get_selected_camera();
run_test("Set camera_1", 'camera_1', $result);
run_test("is_all_cameras_selected() returns false", false, is_all_cameras_selected());

// ==============================================================================
// Test 3: Set Back to 'all'
// ==============================================================================
echo "<h2>Test 3: Set Back to All</h2>";
echo "<p>Setting back to 'all' should work correctly</p>";

set_selected_camera('all');
$result = get_selected_camera();
run_test("Set back to 'all'", 'all', $result);
run_test("is_all_cameras_selected() returns true", true, is_all_cameras_selected());

// ==============================================================================
// Test 4: Invalid Value Handling
// ==============================================================================
echo "<h2>Test 4: Invalid Value Handling</h2>";
echo "<p>Invalid camera IDs should default to 'all'</p>";

set_selected_camera('camera_99');
$result = get_selected_camera();
run_test("Invalid camera_99 defaults to 'all'", 'all', $result);

set_selected_camera('invalid_camera');
$result = get_selected_camera();
run_test("Invalid string defaults to 'all'", 'all', $result);

// ==============================================================================
// Test 5: Null Handling
// ==============================================================================
echo "<h2>Test 5: Null Handling</h2>";
echo "<p>Null values should be handled gracefully</p>";

set_selected_camera(null);
$result = get_selected_camera();
run_test("Null input defaults to 'all'", 'all', $result);

// ==============================================================================
// Test 6: Empty String Handling
// ==============================================================================
echo "<h2>Test 6: Empty String Handling</h2>";
echo "<p>Empty strings should default to 'all'</p>";

set_selected_camera('');
$result = get_selected_camera();
run_test("Empty string defaults to 'all'", 'all', $result);

// ==============================================================================
// Test 7: Session Persistence
// ==============================================================================
echo "<h2>Test 7: Session Persistence</h2>";
echo "<p>Value should persist across multiple function calls</p>";

set_selected_camera('camera_2');
$result1 = get_selected_camera();
$result2 = get_selected_camera();
$result3 = get_selected_camera();

run_test("First get returns camera_2", 'camera_2', $result1);
run_test("Second get returns camera_2", 'camera_2', $result2);
run_test("Third get returns camera_2", 'camera_2', $result3);

// ==============================================================================
// Test 8: All Valid Camera IDs
// ==============================================================================
echo "<h2>Test 8: All Valid Camera IDs</h2>";
echo "<p>Test setting each valid camera ID</p>";

$valid_cameras = array('all', 'camera_1', 'camera_2', 'camera_3', 'camera_4');
foreach ($valid_cameras as $camera) {
    set_selected_camera($camera);
    $result = get_selected_camera();
    run_test("Set and get $camera", $camera, $result);
}

// ==============================================================================
// Test 9: Direct Session Corruption Test
// ==============================================================================
echo "<h2>Test 9: Session Corruption Recovery</h2>";
echo "<p>Manually corrupt session and verify recovery</p>";

// Manually corrupt the session
$_SESSION['selected_camera'] = 'corrupted_value';
$result = get_selected_camera();
run_test("Corrupted session returns 'all'", 'all', $result);

// Re-initialize should fix it
initialize_session();
$result = get_selected_camera();
run_test("After re-initialization, still 'all'", 'all', $result);

// ==============================================================================
// Test 10: Type Safety
// ==============================================================================
echo "<h2>Test 10: Type Safety</h2>";
echo "<p>Test with non-string types</p>";

set_selected_camera(123);
$result = get_selected_camera();
run_test("Integer input defaults to 'all'", 'all', $result);

set_selected_camera(array('camera_1'));
$result = get_selected_camera();
run_test("Array input defaults to 'all'", 'all', $result);

set_selected_camera(true);
$result = get_selected_camera();
run_test("Boolean input defaults to 'all'", 'all', $result);

// ==============================================================================
// Summary
// ==============================================================================
echo "<h2>📊 Test Summary</h2>";
echo "<div class='test-result'>";
echo "<strong>Total Tests:</strong> $test_number<br>";
echo "<strong style='color: #4CAF50;'>Passed:</strong> $passes<br>";
echo "<strong style='color: #f44336;'>Failed:</strong> $fails<br>";
echo "<strong>Success Rate:</strong> " . round(($passes / $test_number) * 100, 1) . "%";
echo "</div>";

if ($fails === 0) {
    echo "<div class='info' style='background: #4CAF50;'>";
    echo "<strong>✅ All tests passed!</strong> Session management is working correctly.";
    echo "</div>";
} else {
    echo "<div class='info' style='background: #f44336;'>";
    echo "<strong>❌ Some tests failed.</strong> Please review the failures above.";
    echo "</div>";
}

// ==============================================================================
// Session Contents
// ==============================================================================
echo "<h2>🔍 Current Session Contents</h2>";
echo "<pre>";
print_r($_SESSION);
echo "</pre>";

?>

</body>
</html>