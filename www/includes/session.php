<?php
/**
 * Session Management for Multi-Camera Security System
 * Handles camera selection persistence across pages
 * 
 * Valid camera selections:
 * - 'all': Show all cameras (default)
 * - 'camera_1' through 'camera_4': Specific camera
 * 
 * Usage:
 *   require_once 'includes/session.php';  // Auto-initializes session
 *   $camera = get_selected_camera();      // Get current selection
 *   set_selected_camera('camera_2');      // Update selection
 *   if (is_all_cameras_selected()) {...}  // Check if viewing all
 */

// Valid camera IDs
define('VALID_CAMERAS', array('all', 'camera_1', 'camera_2', 'camera_3', 'camera_4'));

/**
 * Start PHP session if not already started
 * Safe to call multiple times - prevents "session already started" errors
 * 
 * @return void
 */
function session_start_if_needed() {
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
}

/**
 * Get currently selected camera from session
 * 
 * @return string Camera ID ('all', 'camera_1', 'camera_2', 'camera_3', or 'camera_4')
 * 
 * Returns 'all' if:
 * - No selection exists in session
 * - Session value is null or empty
 * - Session value is invalid/corrupted
 */
function get_selected_camera() {
    session_start_if_needed();
    
    // Check if session variable exists and is valid
    if (isset($_SESSION['selected_camera']) && in_array($_SESSION['selected_camera'], VALID_CAMERAS)) {
        return $_SESSION['selected_camera'];
    }
    
    // Default to 'all' for any invalid or missing value
    return 'all';
}

/**
 * Set selected camera in session
 * Validates input and defaults to 'all' for any invalid value
 * 
 * @param string $camera_id Camera to select ('all', 'camera_1', etc.)
 * @return void
 * 
 * Special case handling:
 * - null → 'all'
 * - empty string → 'all'
 * - non-string → 'all'
 * - invalid camera ID → 'all'
 */
function set_selected_camera($camera_id) {
    session_start_if_needed();
    
    // Handle special cases BEFORE setting session variable
    if ($camera_id === null || $camera_id === '' || !is_string($camera_id)) {
        $camera_id = 'all';
    }
    
    // Validate against allowed values
    if (!in_array($camera_id, VALID_CAMERAS)) {
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
 * - Session is started
 * - selected_camera is set to valid value
 * - Corrupted session values are reset to 'all'
 */
function initialize_session() {
    session_start_if_needed();
    
    // Initialize selected_camera if not set
    if (!isset($_SESSION['selected_camera'])) {
        $_SESSION['selected_camera'] = 'all';
    }
    
    // Validate existing value - reset if corrupted
    if (!in_array($_SESSION['selected_camera'], VALID_CAMERAS)) {
        $_SESSION['selected_camera'] = 'all';
    }
}

// Auto-initialize session when file is included
initialize_session();

?>