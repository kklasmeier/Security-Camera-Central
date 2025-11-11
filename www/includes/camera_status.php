<?php
/**
 * Camera Status Helper Functions
 * Fetches and caches camera version and status information
 */

require_once __DIR__ . '/db.php';
require_once __DIR__ . '/session.php';

/**
 * Format uptime seconds into human-readable string
 * 
 * @param int $seconds Total uptime in seconds
 * @return string Formatted uptime (e.g., "Up 2d 5h" or "Up 3h")
 */
function format_uptime($seconds) {
    if ($seconds < 0) {
        return 'Unknown';
    }
    
    $days = floor($seconds / 86400);
    $hours = floor(($seconds % 86400) / 3600);
    
    if ($days > 0) {
        return "Up {$days}d {$hours}h";
    } else if ($hours > 0) {
        return "Up {$hours}h";
    } else {
        $minutes = floor($seconds / 60);
        return "Up {$minutes}m";
    }
}

/**
 * Fetch version and status from a single camera
 * 
 * @param array $camera Camera record from database (with ip_address)
 * @return array Status information
 */
function fetch_camera_status($camera) {
    // Check if camera has IP address (deployed)
    if (empty($camera['ip_address'])) {
        return [
            'camera_id' => $camera['camera_id'],
            'name' => $camera['name'],
            'location' => $camera['location'],
            'status' => 'not_deployed',
            'version' => 'N/A',
            'uptime' => 'N/A',
            'uptime_seconds' => 0,
            'ip_address' => null
        ];
    }
    
    // Try to reach camera API version endpoint
    $url = "http://{$camera['ip_address']}:5000/api/version";
    $context = stream_context_create([
        'http' => [
            'timeout' => 2,  // 2 second timeout
            'ignore_errors' => true
        ]
    ]);
    
    $response = @file_get_contents($url, false, $context);
    
    if ($response !== false) {
        $data = json_decode($response, true);
        
        if ($data && isset($data['success']) && $data['success']) {
            // Camera responded successfully
            return [
                'camera_id' => $camera['camera_id'],
                'name' => $data['camera_name'] ?? $camera['name'],
                'location' => $camera['location'],
                'status' => 'online',
                'version' => $data['version'] ?? 'Unknown',
                'uptime' => format_uptime($data['uptime_seconds'] ?? 0),
                'uptime_seconds' => $data['uptime_seconds'] ?? 0,
                'ip_address' => $camera['ip_address']
            ];
        } else {
            // API responded but with error
            return [
                'camera_id' => $camera['camera_id'],
                'name' => $camera['name'],
                'location' => $camera['location'],
                'status' => 'error',
                'version' => 'Unknown',
                'uptime' => 'Unknown',
                'uptime_seconds' => 0,
                'ip_address' => $camera['ip_address']
            ];
        }
    } else {
        // Camera unreachable
        return [
            'camera_id' => $camera['camera_id'],
            'name' => $camera['name'],
            'location' => $camera['location'],
            'status' => 'offline',
            'version' => 'Unknown',
            'uptime' => 'Unknown',
            'uptime_seconds' => 0,
            'ip_address' => $camera['ip_address']
        ];
    }
}

/**
 * Get status for all cameras (with 5-minute session cache)
 * 
 * @param bool $force_refresh Force fresh API calls (skip cache)
 * @return array Array of camera status information
 */
function get_all_camera_status($force_refresh = false) {
    // Cache duration: 5 minutes (300 seconds)
    $cache_duration = 300;
    
    // Check if session is available (might not be if headers already sent)
    $session_available = (session_status() === PHP_SESSION_ACTIVE);
    
    // Check if we have valid cached data (only if session available)
    if ($session_available && !$force_refresh && 
        isset($_SESSION['camera_status']) && 
        isset($_SESSION['camera_status_time']) &&
        is_array($_SESSION['camera_status']) &&
        (time() - $_SESSION['camera_status_time']) < $cache_duration) {
        return $_SESSION['camera_status'];
    }
    
    // Fetch fresh data
    $db = new Database();
    $cameras = $db->get_all_cameras();
    $status = [];
    
    foreach ($cameras as $camera) {
        // Only include cameras with IP addresses (deployed cameras)
        if (!empty($camera['ip_address'])) {
            $status[] = fetch_camera_status($camera);
        }
    }
    
    // Cache results in session (only if session available)
    if ($session_available) {
        $_SESSION['camera_status'] = $status;
        $_SESSION['camera_status_time'] = time();
    }
    
    return $status;
}

/**
 * Get cache age in seconds
 * 
 * @return int Seconds since last cache update, or 0 if no cache
 */
function get_cache_age() {
    // Check if session is available
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return 0;
    }
    
    if (isset($_SESSION['camera_status_time'])) {
        return time() - $_SESSION['camera_status_time'];
    }
    
    return 0;
}

/**
 * Clear camera status cache
 * Forces next call to get_all_camera_status() to fetch fresh data
 * 
 * @return void
 */
function clear_camera_status_cache() {
    // Check if session is available
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return;
    }
    
    unset($_SESSION['camera_status']);
    unset($_SESSION['camera_status_time']);
}
?>