<?php
/**
 * Session Management for Multi-Camera Security System
 * Handles camera selection persistence across pages
 * 
 * Valid camera selections:
 * - 'all': Show all cameras (default)
 * - Any camera_id that exists in the database (e.g., 'camera_1', 'camera_2', etc.)
 * 
 * Usage:
 *   require_once 'includes/session.php';  // Auto-initializes session
 *   $camera = get_selected_camera();      // Get current selection
 *   set_selected_camera('camera_2');      // Update selection
 *   if (is_all_cameras_selected()) {...}  // Check if viewing all
 */

// Cache valid camera IDs to avoid repeated database queries
$_valid_cameras_cache = null;

/**
 * Get valid camera IDs from database
 * Results are cached to avoid repeated queries within the same request
 * 
 * @return array Array of valid camera_id strings (e.g., ['camera_1', 'camera_2', ...])
 */
function get_valid_camera_ids() {
    global $_valid_cameras_cache;
    
    // Return cached results if available
    if ($_valid_cameras_cache !== null) {
        return $_valid_cameras_cache;
    }
    
    // Query database for all cameras
    require_once __DIR__ . '/db.php';
    $db = new Database();
    $cameras = $db->get_all_cameras();
    
    // Extract camera_id values
    $camera_ids = [];
    foreach ($cameras as $camera) {
        if (isset($camera['camera_id'])) {
            $camera_ids[] = $camera['camera_id'];
        }
    }
    
    // Cache the results
    $_valid_cameras_cache = $camera_ids;
    
    return $camera_ids;
}

/**
 * Check if a camera ID is valid
 * Valid IDs are: 'all' or any camera_id that exists in the database
 * 
 * @param string $camera_id Camera ID to validate
 * @return bool True if valid, false otherwise
 */
function is_valid_camera_id($camera_id) {
    // 'all' is always valid
    if ($camera_id === 'all') {
        return true;
    }
    
    // Check against database cameras
    $valid_ids = get_valid_camera_ids();
    return in_array($camera_id, $valid_ids, true);
}

/**
 * Start PHP session if not already started
 * Safe to call multiple times - prevents "session already started" errors
 * Handles "headers already sent" gracefully
 * 
 * @return void
 */
function session_start_if_needed() {
    // Check if session is already active
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    
    // Check if headers have already been sent
    if (headers_sent($file, $line)) {
        // Headers already sent - cannot start session
        // This is not fatal for read-only operations
        // Log the issue for debugging
        error_log("Cannot start session - headers already sent in $file on line $line");
        return;
    }
    
    // Safe to start session
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
}

/**
 * Get currently selected camera from session
 * 
 * @return string Camera ID ('all' or valid camera_id from database)
 * 
 * Returns 'all' if:
 * - No selection exists in session
 * - Session value is null or empty
 * - Session value is invalid/not in database
 * - Session couldn't be started (headers already sent)
 */
function get_selected_camera() {
    session_start_if_needed();
    
    // Check if session is active and variable exists
    if (session_status() === PHP_SESSION_ACTIVE && 
        isset($_SESSION['selected_camera']) && 
        is_valid_camera_id($_SESSION['selected_camera'])) {
        return $_SESSION['selected_camera'];
    }
    
    // Default to 'all' for any invalid or missing value
    return 'all';
}

/**
 * Set selected camera in session
 * Validates input against database and defaults to 'all' for any invalid value
 * 
 * @param string $camera_id Camera to select ('all' or valid camera_id from database)
 * @return void
 * 
 * Special case handling:
 * - null → 'all'
 * - empty string → 'all'
 * - non-string → 'all'
 * - invalid camera ID (not in database) → 'all'
 * - session not started → silently fail
 */
function set_selected_camera($camera_id) {
    session_start_if_needed();
    
    // Only proceed if session is active
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return;
    }
    
    // Handle special cases BEFORE setting session variable
    if ($camera_id === null || $camera_id === '' || !is_string($camera_id)) {
        $camera_id = 'all';
    }
    
    // Validate against database cameras
    if (!is_valid_camera_id($camera_id)) {
        $camera_id = 'all';
    }
    
    // Set validated value in session
    $_SESSION['selected_camera'] = $camera_id;
}

/**
 * Check if "All Cameras" is currently selected
 * Helper function for cleaner conditional logic in pages
 * 
 * @return bool True if 'all' is selected, false otherwise
 * 
 * Usage example:
 *   if (is_all_cameras_selected()) {
 *       // Query all cameras
 *   } else {
 *       // Query specific camera
 *   }
 */
function is_all_cameras_selected() {
    return get_selected_camera() === 'all';
}

/**
 * Initialize session with default values
 * Called automatically when this file is included
 * 
 * @return void
 * 
 * Ensures:
 * - Session is started (if headers not sent)
 * - selected_camera is set to valid value
 * - Corrupted or deleted camera IDs are reset to 'all'
 */
function initialize_session() {
    session_start_if_needed();
    
    // Only proceed if session is active
    if (session_status() !== PHP_SESSION_ACTIVE) {
        return;
    }
    
    // Initialize selected_camera if not set
    if (!isset($_SESSION['selected_camera'])) {
        $_SESSION['selected_camera'] = 'all';
    }
    
    // Validate existing value - reset if camera no longer exists in database
    if (!is_valid_camera_id($_SESSION['selected_camera'])) {
        $_SESSION['selected_camera'] = 'all';
    }
}

// ========================================
// LOGS FILTER SESSION FUNCTIONS
// ========================================

/**
 * Valid result limit options for logs
 */
function get_valid_log_limits() {
    return [500, 1000, 2500, 5000, 10000, 25000];
}

/**
 * Get logs filter expanded state
 * @return bool
 */
function get_logs_filters_expanded() {
    session_start_if_needed();
    return isset($_SESSION['logs_filters_expanded']) ? (bool)$_SESSION['logs_filters_expanded'] : false;
}

/**
 * Set logs filter expanded state
 * @param bool $expanded
 */
function set_logs_filters_expanded($expanded) {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $_SESSION['logs_filters_expanded'] = (bool)$expanded;
    }
}

/**
 * Get logs result limit
 * @return int
 */
function get_logs_result_limit() {
    session_start_if_needed();
    $valid = get_valid_log_limits();
    if (isset($_SESSION['logs_result_limit']) && in_array((int)$_SESSION['logs_result_limit'], $valid)) {
        return (int)$_SESSION['logs_result_limit'];
    }
    return 1000; // default
}

/**
 * Set logs result limit
 * @param int $limit
 */
function set_logs_result_limit($limit) {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $valid = get_valid_log_limits();
        $limit = (int)$limit;
        if (in_array($limit, $valid)) {
            $_SESSION['logs_result_limit'] = $limit;
        }
    }
}

/**
 * Get logs date from filter
 * @return string|null Date in Y-m-d format or null
 */
function get_logs_date_from() {
    session_start_if_needed();
    return isset($_SESSION['logs_date_from']) && $_SESSION['logs_date_from'] !== '' 
        ? $_SESSION['logs_date_from'] : null;
}

/**
 * Set logs date from filter
 * @param string|null $date
 */
function set_logs_date_from($date) {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $_SESSION['logs_date_from'] = $date !== '' ? $date : null;
    }
}

/**
 * Get logs time from filter (hour)
 * @return int Hour 0-23
 */
function get_logs_time_from() {
    session_start_if_needed();
    if (isset($_SESSION['logs_time_from'])) {
        $hour = (int)$_SESSION['logs_time_from'];
        if ($hour >= 0 && $hour <= 23) {
            return $hour;
        }
    }
    return 0; // default midnight
}

/**
 * Set logs time from filter (hour)
 * @param int $hour
 */
function set_logs_time_from($hour) {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $hour = (int)$hour;
        if ($hour >= 0 && $hour <= 23) {
            $_SESSION['logs_time_from'] = $hour;
        }
    }
}

/**
 * Get logs date to filter
 * @return string|null Date in Y-m-d format or null
 */
function get_logs_date_to() {
    session_start_if_needed();
    return isset($_SESSION['logs_date_to']) && $_SESSION['logs_date_to'] !== '' 
        ? $_SESSION['logs_date_to'] : null;
}

/**
 * Set logs date to filter
 * @param string|null $date
 */
function set_logs_date_to($date) {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $_SESSION['logs_date_to'] = $date !== '' ? $date : null;
    }
}

/**
 * Get logs time to filter (hour)
 * @return int Hour 0-23
 */
function get_logs_time_to() {
    session_start_if_needed();
    if (isset($_SESSION['logs_time_to'])) {
        $hour = (int)$_SESSION['logs_time_to'];
        if ($hour >= 0 && $hour <= 23) {
            return $hour;
        }
    }
    return 23; // default end of day
}

/**
 * Set logs time to filter (hour)
 * @param int $hour
 */
function set_logs_time_to($hour) {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $hour = (int)$hour;
        if ($hour >= 0 && $hour <= 23) {
            $_SESSION['logs_time_to'] = $hour;
        }
    }
}

/**
 * Check if date filters are active
 * @return bool
 */
function has_logs_date_filter() {
    return get_logs_date_from() !== null || get_logs_date_to() !== null;
}

/**
 * Clear logs date filters
 */
function clear_logs_date_filters() {
    session_start_if_needed();
    if (session_status() === PHP_SESSION_ACTIVE) {
        $_SESSION['logs_date_from'] = null;
        $_SESSION['logs_date_to'] = null;
        $_SESSION['logs_time_from'] = 0;
        $_SESSION['logs_time_to'] = 23;
    }
}

// Auto-initialize session when file is included
initialize_session();

?>