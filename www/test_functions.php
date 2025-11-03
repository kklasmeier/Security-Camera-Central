<?php
/**
 * Test Helper Functions
 * Tests all updated functions for Session 2
 */

require_once 'includes/db.php';
require_once 'includes/functions.php';

echo "=== Security Camera Helper Functions Test ===\n\n";

// Initialize database
$db = new Database();

if (!$db->isConnected()) {
    echo "ERROR: Could not connect to database\n";
    exit(1);
}

echo "✓ Database connected\n\n";

// ============================================================================
// Test 1: Get thumbnail URL
// ============================================================================
echo "--- Test 1: get_thumbnail_url() ---\n";

$test_event = array(
    'thumbnail_path' => 'camera_1/thumbs/42_20251026_143022_thumb.jpg'
);

$url = get_thumbnail_url($test_event);
echo "Input: {$test_event['thumbnail_path']}\n";
echo "Output: $url\n";
echo "Expected: /footage/camera_1/thumbs/42_20251026_143022_thumb.jpg\n";

// Test with missing thumbnail
$test_event_no_thumb = array('thumbnail_path' => '');
$url_no_thumb = get_thumbnail_url($test_event_no_thumb);
echo "Missing thumbnail returns placeholder: " . (strpos($url_no_thumb, 'data:image/svg') === 0 ? "✓ Yes" : "✗ No") . "\n\n";

// ============================================================================
// Test 2: Get video URL
// ============================================================================
echo "--- Test 2: get_video_url() ---\n";

$test_event_video = array(
    'video_mp4_path' => 'camera_1/videos/42_20251026_143022_video.mp4',
    'video_h264_path' => 'camera_1/videos/42_20251026_143022_video.h264'
);

$url = get_video_url($test_event_video);
echo "Input MP4: {$test_event_video['video_mp4_path']}\n";
echo "Output: " . ($url ? $url : "NULL") . "\n";
echo "Expected: /footage/camera_1/videos/42_20251026_143022_video.mp4\n";

// Test with only H264
$test_event_h264_only = array(
    'video_mp4_path' => '',
    'video_h264_path' => 'camera_1/videos/42_20251026_143022_video.h264'
);

$url_h264 = get_video_url($test_event_h264_only);
echo "H264 fallback: " . ($url_h264 ? $url_h264 : "NULL") . "\n";
echo "Expected: /footage/camera_1/videos/42_20251026_143022_video.h264 or NULL if file doesn't exist\n\n";

// ============================================================================
// Test 3: Get image URL
// ============================================================================
echo "--- Test 3: get_image_url() ---\n";

$path = 'camera_1/pictures/42_20251026_143022_a.jpg';
$url = get_image_url($path);
echo "Input: $path\n";
echo "Output: " . ($url ? $url : "NULL") . "\n";
echo "Expected: /footage/camera_1/pictures/42_20251026_143022_a.jpg or NULL if file doesn't exist\n\n";

// ============================================================================
// Test 4: Camera display name
// ============================================================================
echo "--- Test 4: get_camera_display_name() ---\n";

// Test with real camera
$name = get_camera_display_name('camera_1', $db);
echo "Camera 1 name: $name\n";
echo "Expected: A friendly name from database (e.g., 'Front Door')\n\n";

// Test with 'all'
$name_all = get_camera_display_name('all', $db);
echo "All cameras: $name_all\n";
echo "Expected: 'All Cameras'\n\n";

// Test with null
$name_null = get_camera_display_name(null, $db);
echo "Null camera: $name_null\n";
echo "Expected: 'All Cameras'\n\n";

// ============================================================================
// Test 5: Video processing check
// ============================================================================
echo "--- Test 5: is_video_processing() ---\n";

$h264_path = 'camera_1/videos/42_20251026_143022_video.h264';
$is_processing = is_video_processing($h264_path);
echo "H264 path: $h264_path\n";
echo "Is processing: " . ($is_processing ? "Yes" : "No") . "\n";
echo "Expected: No (unless .pending file exists on filesystem)\n\n";

// Test with empty path
$is_processing_empty = is_video_processing('');
echo "Empty path processing: " . ($is_processing_empty ? "Yes" : "No") . "\n";
echo "Expected: No\n\n";

// ============================================================================
// Test 6: Transfer status formatting
// ============================================================================
echo "--- Test 6: format_transfer_status() ---\n";

$test_event_status = array(
    'image_a_transferred' => 1,
    'image_b_transferred' => 1,
    'thumbnail_transferred' => 1,
    'video_transferred' => 0,
    'mp4_conversion_status' => 'complete'
);

$status = format_transfer_status($test_event_status);

echo "Transfer Status Results:\n";
echo "  Image A: " . ($status['image_a']['transferred'] ? "✓" : "✗") . " {$status['image_a']['label']}\n";
echo "  Image B: " . ($status['image_b']['transferred'] ? "✓" : "✗") . " {$status['image_b']['label']}\n";
echo "  Thumbnail: " . ($status['thumbnail']['transferred'] ? "✓" : "✗") . " {$status['thumbnail']['label']}\n";
echo "  Video H264: " . ($status['video']['transferred'] ? "✓" : "✗") . " {$status['video']['label']}\n";
echo "  MP4: {$status['mp4']['status']} - {$status['mp4']['label']}\n";

echo "\nExpected:\n";
echo "  Image A: ✓\n";
echo "  Image B: ✓\n";
echo "  Thumbnail: ✓\n";
echo "  Video H264: ✗\n";
echo "  MP4: complete\n\n";

// Test with all false
$test_event_none = array(
    'image_a_transferred' => 0,
    'image_b_transferred' => 0,
    'thumbnail_transferred' => 0,
    'video_transferred' => 0,
    'mp4_conversion_status' => 'pending'
);

$status_none = format_transfer_status($test_event_none);
echo "All pending test:\n";
foreach ($status_none as $key => $item) {
    if ($key === 'mp4') {
        echo "  $key: {$item['status']}\n";
    } else {
        echo "  $key: " . ($item['transferred'] ? "transferred" : "pending") . "\n";
    }
}

echo "\n=== All Tests Complete ===\n";
echo "\nNote: Some tests may show NULL if files don't exist on filesystem.\n";
echo "This is expected behavior - the functions check file existence.\n";

?>