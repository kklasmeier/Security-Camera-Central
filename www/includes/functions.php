<?php
/**
 * Helper Functions for Security Camera Web Interface
 * Multi-camera version with updated path handling
 */

require_once __DIR__ . '/config.php';

date_default_timezone_set('America/New_York');

/**
 * Format event timestamp with smart relative dates
 * 
 * @param string $timestamp MySQL datetime string (e.g., "2025-10-19 14:30:45")
 * @return string Formatted timestamp
 * 
 * Returns:
 * - "2:34 PM" for today
 * - "Yesterday 2:34 PM" for yesterday
 * - "Tuesday 2:34 PM" for 2-7 days ago
 * - "Oct 12, 2025 2:34 PM" for 8+ days ago
 */
function format_event_timestamp($timestamp) {
    // Convert ISO format timestamp to Unix timestamp
    $event_time = strtotime($timestamp);
    
    // If strtotime failed, return the original timestamp
    if ($event_time === false) {
        return $timestamp;
    }
    
    $now = time();
    
    // Compare dates (not times) to determine which day
    $event_date = date('Y-m-d', $event_time);
    $today_date = date('Y-m-d', $now);
    $yesterday_date = date('Y-m-d', strtotime('-1 day', $now));
    
    // Today
    if ($event_date === $today_date) {
        return 'Today ' . date('g:i A', $event_time);
    }
    
    // Yesterday
    if ($event_date === $yesterday_date) {
        return 'Yesterday ' . date('g:i A', $event_time);
    }
    
    // Within last 7 days - show day of week
    $days_ago = floor(($now - $event_time) / 86400);
    if ($days_ago >= 2 && $days_ago <= 7) {
        return date('l g:i A', $event_time); // "Tuesday 2:34 PM"
    }
    
    // Older - show full date
    return date('M j, Y g:i A', $event_time); // "Oct 12, 2025 2:34 PM"
}

/**
 * Get motion score badge information
 * 
 * @param int $score Motion detection score (0-999+)
 * @return array ['color' => string, 'label' => string, 'symbol' => string]
 * 
 * Color coding:
 * - Low (0-149): Red - common, minor motion
 * - Medium (150-249): Yellow - moderate motion
 * - High (250+): Green - significant motion/activity
 */
function get_motion_badge($score) {
    if ($score >= 250) {
        return [
            'color' => 'high',    // CSS class: .badge-high
            'label' => 'High',
            'symbol' => '●'       // Solid circle (will be colored by CSS)
        ];
    } elseif ($score >= 150) {
        return [
            'color' => 'medium',  // CSS class: .badge-medium
            'label' => 'Medium',
            'symbol' => '●'       // Solid circle (will be colored by CSS)
        ];
    } else {
        return [
            'color' => 'low',     // CSS class: .badge-low
            'label' => 'Low',
            'symbol' => '●'       // Solid circle (will be colored by CSS)
        ];
    }
}

/**
 * Get event status badge information
 * 
 * @param string $status Event processing status from database
 * @return array ['color' => string, 'label' => string, 'symbol' => string]
 * 
 * Status types:
 * - complete: Event fully processed (green)
 * - interrupted: Event aborted for live streaming (yellow)
 * - processing: Event currently being processed (blue)
 * - failed: Event processing failed (red)
 */
function get_event_status_badge($status) {
    switch (strtolower($status)) {
        case 'complete':
            return [
                'color' => 'complete',      // CSS class: .badge-status-complete
                'label' => 'Complete',
                'symbol' => '✓'             // Checkmark
            ];
        
        case 'interrupted':
            return [
                'color' => 'interrupted',   // CSS class: .badge-status-interrupted
                'label' => 'Interrupted',
                'symbol' => '⚠'             // Warning symbol
            ];
        
        case 'processing':
            return [
                'color' => 'processing',    // CSS class: .badge-status-processing
                'label' => 'Processing',
                'symbol' => '⏳'            // Hourglass
            ];
        
        case 'failed':
            return [
                'color' => 'failed',        // CSS class: .badge-status-failed
                'label' => 'Failed',
                'symbol' => '✗'             // X mark
            ];
        
        default:
            return [
                'color' => 'unknown',       // CSS class: .badge-status-unknown
                'label' => 'Unknown',
                'symbol' => '?'
            ];
    }
}

/**
 * Check if video is still being processed/converted
 * 
 * @param string $video_h264_path Relative H.264 path from database (e.g., "camera_1/videos/file.h264")
 * @return bool True if .pending marker file exists (still processing), false otherwise
 * 
 * The conversion system creates a .pending marker file while converting .h264 to .mp4
 * This function receives the video_h264_path field directly from the event record
 */
function is_video_processing($video_h264_path) {
    // Don't process if video_h264_path is empty or null
    if (empty($video_h264_path)) {
        return false;
    }
    
    // Convert relative path to absolute filesystem path
    $full_path = MEDIA_ROOT . $video_h264_path;
    
    // Check for .pending marker file
    $pending_marker = $full_path . '.pending';
    
    return file_exists($pending_marker);
}

/**
 * Get web-accessible URL for event thumbnail
 * 
 * @param array $event Event record from database with 'thumbnail_path' key
 * @return string Web-accessible URL path (e.g., "/footage/camera_1/thumbs/file.jpg")
 * 
 * Converts relative database path to web URL
 * Returns placeholder if thumbnail doesn't exist
 */
function get_thumbnail_url($event) {
    // Check if thumbnail_path exists
    if (!empty($event['thumbnail_path'])) {
        // Database stores relative path: camera_1/thumbs/file.jpg
        // Convert to filesystem path
        $full_path = MEDIA_ROOT . $event['thumbnail_path'];
        
        // Check if file exists
        if (file_exists($full_path)) {
            // Return web URL: /footage/camera_1/thumbs/file.jpg
            return MEDIA_URL_PREFIX . $event['thumbnail_path'];
        }
    }
    
    // Fallback: return inline SVG placeholder (matches dark theme)
    return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="320" height="180"%3E%3Crect fill="%231a1a1a" width="320" height="180"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="system-ui" font-size="48" fill="%23666"%3E📷%3C/text%3E%3Ctext x="50%25" y="65%25" dominant-baseline="middle" text-anchor="middle" font-family="system-ui" font-size="14" fill="%23666"%3ENo Image%3C/text%3E%3C/svg%3E';
}

/**
 * Convert video file path to web URL
 * 
 * @param array $event Event record with 'video_mp4_path' or 'video_h264_path' key
 * @return string|null Web URL or null if not available
 */
function get_video_url($event) {
    // Prefer MP4 over H264
    $video_path = null;
    
    if (!empty($event['video_mp4_path'])) {
        $video_path = $event['video_mp4_path'];
    } elseif (!empty($event['video_h264_path'])) {
        $video_path = $event['video_h264_path'];
    }
    
    if (empty($video_path)) {
        return null;
    }
    
    // Convert to filesystem path and check existence
    $full_path = MEDIA_ROOT . $video_path;
    
    if (!file_exists($full_path)) {
        return null;
    }
    
    // Return web URL
    return MEDIA_URL_PREFIX . $video_path;
}

/**
 * Convert image file path to web URL
 * 
 * @param string $path Relative database path (e.g., "camera_1/pictures/file.jpg")
 * @return string|null Web URL or null if not available
 */
function get_image_url($path) {
    if (empty($path)) {
        return null;
    }
    
    // Convert to filesystem path
    $full_path = MEDIA_ROOT . $path;
    
    if (!file_exists($full_path)) {
        return null;
    }
    
    // Return web URL
    return MEDIA_URL_PREFIX . $path;
}

/**
 * Get formatted file size from file path
 * 
 * @param string $path Relative database path
 * @return string Formatted size (e.g., "2.3 MB") or "N/A"
 */
function get_file_size($path) {
    if (empty($path)) {
        return 'N/A';
    }
    
    // Convert to filesystem path
    $full_path = MEDIA_ROOT . $path;
    
    if (!file_exists($full_path)) {
        return 'N/A';
    }
    
    $bytes = filesize($full_path);
    
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' bytes';
    }
}

/**
 * Sanitize and validate page number
 * 
 * @param mixed $page Raw page parameter from $_GET
 * @return int Valid page number (>= 1)
 */
function sanitize_page($page) {
    $page = (int)$page;
    return ($page < 1) ? 1 : $page;
}

/**
 * Sanitize and validate per_page parameter
 * 
 * @param mixed $per_page Raw per_page parameter from $_GET
 * @return int Valid per_page value (12, 24, 48, or 100)
 */
function sanitize_per_page($per_page) {
    $per_page = (int)$per_page;
    $allowed = [12, 24, 48, 100];
    
    return in_array($per_page, $allowed) ? $per_page : 12;
}

/**
 * Build pagination URL preserving current parameters
 * 
 * @param int $page Target page number
 * @param int $per_page Current per_page setting
 * @param string|null $camera_id Optional camera filter
 * @return string URL with query parameters
 */
function build_pagination_url($page, $per_page, $camera_id = null) {
    $params = [];
    
    if ($page > 1) {
        $params[] = 'page=' . $page;
    }
    
    if ($per_page != 12) {
        $params[] = 'per_page=' . $per_page;
    }
    
    if ($camera_id !== null && $camera_id !== 'all') {
        $params[] = 'camera=' . urlencode($camera_id);
    }
    
    return 'index.php' . (count($params) > 0 ? '?' . implode('&', $params) : '');
}

/**
 * Format file size for display
 * 
 * @param int $bytes File size in bytes
 * @return string Formatted size (e.g., "2.5 MB")
 */
function format_file_size($bytes) {
    if ($bytes == 0) return '0 B';
    
    $units = ['B', 'KB', 'MB', 'GB'];
    $factor = floor((strlen($bytes) - 1) / 3);
    
    return sprintf("%.1f %s", $bytes / pow(1024, $factor), $units[$factor]);
}

/**
 * Format duration in seconds to readable format
 * 
 * @param int $seconds Duration in seconds
 * @return string Formatted duration (e.g., "30s", "1m 45s", "1h 2m")
 */
function format_duration($seconds) {
    if ($seconds < 60) {
        return $seconds . 's';
    } elseif ($seconds < 3600) {
        $minutes = floor($seconds / 60);
        $secs = $seconds % 60;
        return $secs > 0 ? "{$minutes}m {$secs}s" : "{$minutes}m";
    } else {
        $hours = floor($seconds / 3600);
        $minutes = floor(($seconds % 3600) / 60);
        return $minutes > 0 ? "{$hours}h {$minutes}m" : "{$hours}h";
    }
}

/**
 * Format log timestamp for display
 * Logs always show full timestamp for diagnostic purposes
 * Format: Oct 19, 2025 8:43:15 PM
 * 
 * @param string $timestamp ISO format timestamp from database
 * @return string Formatted timestamp
 */
function format_log_timestamp($timestamp) {
    $time = strtotime($timestamp);
    return date('M j, Y g:i:s A', $time);
}

/**
 * Get camera name from camera_id
 * 
 * @param string|null $camera_id Camera identifier (e.g., 'camera_1') or 'all' or null
 * @param Database $db Database instance
 * @return string Camera friendly name, 'All Cameras' for null/'all', or camera_id if not found
 */
function get_camera_display_name($camera_id, $db) {
    // Handle special cases
    if ($camera_id === null || $camera_id === 'all' || $camera_id === '') {
        return 'All Cameras';
    }
    
    // Check database connection
    if (!$db || !$db->isConnected()) {
        return $camera_id;
    }
    
    // Get name from database
    return $db->get_camera_name($camera_id);
}

/**
 * Format transfer status for event detail display
 * 
 * @param array $event Event record with transfer status fields
 * @return array Status items with 'transferred' boolean and 'label' string for each file type
 * 
 * Returns array with status for:
 * - image_a: Picture A transfer status
 * - image_b: Picture B transfer status
 * - thumbnail: Thumbnail transfer status
 * - video: H.264 video transfer status
 * - mp4: MP4 conversion status (special handling)
 */
function format_transfer_status($event) {
    $status = array();
    
    // Image A
    $status['image_a'] = array(
        'transferred' => !empty($event['image_a_transferred']) ? (bool)$event['image_a_transferred'] : false,
        'label' => 'Picture A'
    );
    
    // Image B
    $status['image_b'] = array(
        'transferred' => !empty($event['image_b_transferred']) ? (bool)$event['image_b_transferred'] : false,
        'label' => 'Picture B'
    );
    
    // Thumbnail
    $status['thumbnail'] = array(
        'transferred' => !empty($event['thumbnail_transferred']) ? (bool)$event['thumbnail_transferred'] : false,
        'label' => 'Thumbnail'
    );
    
    // Video (H.264)
    $status['video'] = array(
        'transferred' => !empty($event['video_transferred']) ? (bool)$event['video_transferred'] : false,
        'label' => 'Video (H.264)'
    );
    
    // MP4 - uses conversion status instead of boolean
    $mp4_status = !empty($event['mp4_conversion_status']) ? $event['mp4_conversion_status'] : 'pending';
    $status['mp4'] = array(
        'status' => $mp4_status,
        'label' => 'Video (MP4)'
    );
    
    return $status;
}

?>