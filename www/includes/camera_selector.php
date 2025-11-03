<?php
/**
 * Camera Selector Component
 * Reusable dropdown for filtering content by camera
 */

require_once 'db.php';
require_once 'session.php';

/**
 * Handle camera selection form submission
 * Call this at the top of pages that use the selector
 */
function handle_camera_selection() {
    if (isset($_POST['camera'])) {
        set_selected_camera($_POST['camera']);
        
        // Redirect to prevent form resubmission
        header("Location: " . $_SERVER['PHP_SELF'] . ($_SERVER['QUERY_STRING'] ? '?' . $_SERVER['QUERY_STRING'] : ''));
        exit;
    }
}

/**
 * Render camera selector dropdown
 * @param string $current_page Current page filename (e.g., 'index.php')
 */
function render_camera_selector($current_page) {
    $db = new Database();
    $cameras = $db->get_all_cameras();
    $selected_camera = get_selected_camera();
    
    echo '<form method="POST" action="' . htmlspecialchars($current_page) . '" class="camera-selector-form">';
    echo '    <label for="camera-select">Camera:</label>';
    echo '    <select name="camera" id="camera-select" onchange="this.form.submit()">';
    
    // "All Cameras" option
    $is_all_selected = ($selected_camera === 'all') ? 'selected' : '';
    echo '        <option value="all" ' . $is_all_selected . '>All Cameras</option>';
    
    // Individual cameras
    foreach ($cameras as $camera) {
        $camera_id = htmlspecialchars($camera['camera_id']);
        $camera_name = htmlspecialchars($camera['name']);
        $is_selected = ($selected_camera === $camera['camera_id']) ? 'selected' : '';
        
        echo '        <option value="' . $camera_id . '" ' . $is_selected . '>' . $camera_name . '</option>';
    }
    
    echo '    </select>';
    echo '</form>';
}
?>