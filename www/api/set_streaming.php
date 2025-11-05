<?php
/**
 * Central Streaming Control API
 * Proxies streaming commands to individual camera control APIs
 */

require_once '../includes/db.php';
require_once '../includes/session.php';

header('Content-Type: application/json');

// Get parameters
$action = $_GET['action'] ?? '';
$camera_id = $_GET['camera'] ?? get_selected_camera();

// Validate action
if (!in_array($action, ['start', 'stop'])) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'Invalid action. Use start or stop.'
    ]);
    exit;
}

// Validate camera_id
if (empty($camera_id) || $camera_id === 'all') {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'Invalid camera ID. Live view requires specific camera.'
    ]);
    exit;
}

try {
    // Get camera details from database
    $db = new Database();
    $camera = $db->get_camera_by_id($camera_id);
    
    if (!$camera) {
        http_response_code(404);
        echo json_encode([
            'success' => false,
            'message' => "Camera not found: $camera_id"
        ]);
        exit;
    }
    
    $camera_ip = $camera['ip_address'];
    $camera_name = $camera['name'];
    
    if (empty($camera_ip)) {
        http_response_code(500);
        echo json_encode([
            'success' => false,
            'message' => "Camera IP address not configured for $camera_name"
        ]);
        exit;
    }
    
    // Build camera API URL
    $camera_api_url = "http://{$camera_ip}:5000/api/stream?action={$action}";
    
    // Create HTTP context with timeout
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'timeout' => 5,  // 5 second timeout
            'ignore_errors' => true  // Allow reading error responses
        ]
    ]);
    
    // Call camera API
    $response = @file_get_contents($camera_api_url, false, $context);
    
    // Check if request failed
    if ($response === false) {
        http_response_code(503);
        echo json_encode([
            'success' => false,
            'message' => "Camera unreachable: $camera_name ($camera_ip)",
            'camera_id' => $camera_id,
            'camera_name' => $camera_name,
            'camera_ip' => $camera_ip
        ]);
        exit;
    }
    
    // Parse camera response
    $camera_response = json_decode($response, true);
    
    // Check if camera returned error
    if (!$camera_response || !isset($camera_response['success'])) {
        http_response_code(500);
        echo json_encode([
            'success' => false,
            'message' => "Invalid response from camera: $camera_name",
            'camera_id' => $camera_id,
            'camera_name' => $camera_name
        ]);
        exit;
    }
    
    // If camera returned error, pass it through
    if (!$camera_response['success']) {
        http_response_code(400);
        echo json_encode($camera_response);
        exit;
    }
    
    // Success - pass camera response through to frontend
    // Add central server context
    $camera_response['central_server'] = true;
    $camera_response['camera_ip'] = $camera_ip;
    
    echo json_encode($camera_response);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Server error: ' . $e->getMessage()
    ]);
}
?>