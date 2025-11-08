<?php
/**
 * Refresh Camera Status API
 * Forces fresh camera status check and returns updated data
 */

require_once '../includes/session.php';
require_once '../includes/camera_status.php';

header('Content-Type: application/json');

try {
    // Force refresh camera status (bypass cache)
    $status = get_all_camera_status($force_refresh = true);
    
    // Return success with updated camera data
    echo json_encode([
        'success' => true,
        'cameras' => $status,
        'timestamp' => date('c'),
        'cache_age' => 0
    ]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Failed to refresh camera status: ' . $e->getMessage()
    ]);
}
?>