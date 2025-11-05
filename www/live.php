<?php
require_once 'includes/session.php';
require_once 'includes/db.php';
require_once 'includes/functions.php';

// Handle camera selection
if (isset($_POST['camera'])) {
    $selected = $_POST['camera'];
    
    // Validate: must be a specific camera (not 'all')
    if (in_array($selected, ['camera_1', 'camera_2', 'camera_3', 'camera_4'])) {
        set_selected_camera($selected);
        // Redirect to prevent form resubmission
        header("Location: live.php");
        exit;
    }
}

// Get selected camera (default to camera_1 if 'all' is selected)
$camera_id = get_selected_camera();
if ($camera_id === 'all') {
    $camera_id = 'camera_1'; // Live view requires specific camera
    set_selected_camera($camera_id);
}

// Get camera details from database
$db = new Database();
$camera = $db->get_camera_by_id($camera_id);

// If camera not found, use first available camera
if (!$camera) {
    $cameras = $db->get_all_cameras();
    if (!empty($cameras)) {
        $camera = $cameras[0];
        $camera_id = $camera['camera_id'];
        set_selected_camera($camera_id);
    } else {
        die('<h1>Error: No cameras registered in database</h1>');
    }
}

$page_title = "Live View - " . htmlspecialchars($camera['name']);

require_once 'includes/header.php';
?>

<div class="container">
    <div class="live-header">
        <h1 class="live-title">Live Camera View</h1>
        
        <!-- Camera Selector (no "All Cameras" option) -->
        <form method="POST" action="live.php" class="camera-selector-form">
            <label for="camera-select">Camera:</label>
            <select name="camera" id="camera-select" onchange="this.form.submit()">
                <?php
                $all_cameras = $db->get_all_cameras();
                foreach ($all_cameras as $cam) {
                    $selected = ($camera_id === $cam['camera_id']) ? 'selected' : '';
                    echo '<option value="' . htmlspecialchars($cam['camera_id']) . '" ' . $selected . '>';
                    echo htmlspecialchars($cam['name']);
                    echo '</option>';
                }
                ?>
            </select>
        </form>
        
        <div class="stream-controls">
            <div class="stream-status">
                <div id="stream-status" class="status-indicator status-inactive"></div>
                <span id="stream-status-text" class="status-text">Stopped</span>
            </div>
            
            <button 
                id="stream-button" 
                class="btn btn-success"
                onclick="startStream()"
            >
                Start Stream
            </button>
        </div>
    </div>
    
    <div id="stream-container" class="stream-container" 
         data-camera-id="<?php echo htmlspecialchars($camera_id); ?>"
         data-camera-ip="<?php echo htmlspecialchars($camera['ip_address']); ?>"
         data-camera-name="<?php echo htmlspecialchars($camera['name']); ?>">
        
        <!-- Placeholder (shown when stopped) -->
        <div id="stream-placeholder" class="stream-placeholder" style="display: flex;">
            <div class="placeholder-content">
                <div class="placeholder-icon">📹</div>
                <div class="placeholder-text">Camera feed will appear here</div>
                <div class="placeholder-subtext">Click "Start Stream" to begin</div>
            </div>
        </div>
        
        <!-- Live stream (shown when streaming) -->
        <img 
            id="stream-image" 
            class="stream-image" 
            src=""
            alt="Live camera stream"
            style="display: none;"
        >
    </div>
    
    <div class="stream-info-container">
        <div id="stream-timer" class="stream-timer"></div>
        <div id="stream-info" class="stream-info"></div>
    </div>
</div>

<?php require_once 'includes/footer.php'; ?>