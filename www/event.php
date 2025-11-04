<?php
/**
 * Event Detail Page
 * Displays full details of a single motion detection event including:
 * - Event metadata (timestamp, motion score, duration, files)
 * - Auto-playing video
 * - Two images (Picture A and Picture B)
 * - Previous/Next navigation
 */

require_once 'includes/db.php';
require_once 'includes/functions.php';

// Get and validate event ID
$event_id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

if ($event_id <= 0) {
    header("Location: index.php?error=invalid_event_id");
    exit;
}

// Initialize database
$db = new Database();

// Get event details
$event = $db->get_event_by_id($event_id);

if (!$event) {
    header("Location: index.php?error=event_not_found");
    exit;
}

// Get navigation (previous and next event IDs)
$prev_id = $db->get_previous_event_id($event_id);
$next_id = $db->get_next_event_id($event_id);

// Check if video is still processing - use mp4_conversion_status field
$video_processing = ($event['mp4_conversion_status'] !== 'complete');

// Get URLs for media files
$video_url = get_video_url($event);
$image_a_url = get_image_url($event['image_a_path']);
$image_b_url = get_image_url($event['image_b_path']);

// Get motion badge info
$badge = get_motion_badge($event['motion_score']);

// Page title
$page_title = "Event #" . $event_id;

// Include header
include 'includes/header.php';
?>

<div class="container">
    <!-- Event Details Card -->
    <div class="event-details-card">
        <div class="event-details-header">
            <div class="event-title-group">
                <h1 class="event-id">Event #<?php echo $event_id; ?></h1>
                <span class="event-camera-name">
                    <?php echo htmlspecialchars(get_camera_display_name($event['camera_id'], $db)); ?>
                </span>
            </div>
            
            <div class="event-navigation">
                <?php if ($prev_id): ?>
                    <a href="event.php?id=<?php echo $prev_id; ?>" class="btn btn-secondary">
                        ← Previous
                    </a>
                <?php else: ?>
                    <button class="btn btn-secondary" disabled>
                        ← Previous
                    </button>
                <?php endif; ?>
                
                <a href="index.php" class="btn btn-secondary">
                    Back to Events
                </a>
                
                <?php if ($next_id): ?>
                    <a href="event.php?id=<?php echo $next_id; ?>" class="btn btn-secondary">
                        Next →
                    </a>
                <?php else: ?>
                    <button class="btn btn-secondary" disabled>
                        Next →
                    </button>
                <?php endif; ?>
            </div>
        </div>
        
        <!-- Event Metadata -->
        <div class="detail-item">
            <span class="detail-label">Timestamp:</span>
            <span class="detail-value"><?php echo format_event_timestamp($event['timestamp']); ?></span>
        </div>
        
        <div class="detail-item">
            <span class="detail-label">Motion Score:</span>
            <span class="detail-value">
                <span class="badge badge-<?php echo $badge['color']; ?>">
                    <?php echo $badge['symbol']; ?> <?php echo $badge['label']; ?> (<?php echo $event['motion_score']; ?>)
                </span>
            </span>
        </div>
        
        <div class="detail-item">
            <span class="detail-label">Duration:</span>
            <span class="detail-value">
                <?php 
                // Check multiple possible field names and provide fallback
                if (isset($event['duration_seconds'])) {
                    echo intval($event['duration_seconds']);
                } elseif (isset($event['video_duration'])) {
                    echo intval($event['video_duration']);
                } elseif (isset($event['duration'])) {
                    echo intval($event['duration']);
                } else {
                    echo '60'; // Default fallback
                }
                ?> seconds
            </span>
        </div>
        
        <!-- Picture A -->
        <div class="detail-item">
            <span class="detail-label">Picture A:</span>
            <span class="detail-value">
                <?php if (!empty($event['image_a_path'])): ?>
                    <?php echo basename($event['image_a_path']); ?>
                    <?php if (!$event['image_a_transferred']): ?>
                        <span class="transfer-badge transfer-pending">⏳ Transfer Pending</span>
                    <?php endif; ?>
                <?php else: ?>
                    <span class="transfer-badge transfer-pending">⏳ Not Available</span>
                <?php endif; ?>
            </span>
        </div>

        <!-- Picture B -->
        <div class="detail-item">
            <span class="detail-label">Picture B:</span>
            <span class="detail-value">
                <?php if (!empty($event['image_b_path'])): ?>
                    <?php echo basename($event['image_b_path']); ?>
                    <?php if (!$event['image_b_transferred']): ?>
                        <span class="transfer-badge transfer-pending">⏳ Transfer Pending</span>
                    <?php endif; ?>
                <?php else: ?>
                    <span class="transfer-badge transfer-pending">⏳ Not Available</span>
                <?php endif; ?>
            </span>
        </div>

        <!-- Video -->
        <div class="detail-item">
            <span class="detail-label">Video:</span>
            <span class="detail-value">
                <?php if ($event['mp4_conversion_status'] === 'complete' && !empty($event['video_mp4_path'])): ?>
                    <?php echo basename($event['video_mp4_path']); ?>
                <?php elseif ($event['mp4_conversion_status'] === 'processing'): ?>
                    <span class="transfer-badge transfer-processing">⏳ Processing</span>
                <?php elseif ($event['mp4_conversion_status'] === 'failed'): ?>
                    <span class="transfer-badge transfer-failed">✗ Conversion Failed</span>
                <?php elseif (!$event['video_transferred']): ?>
                    <span class="transfer-badge transfer-pending">⏳ Transfer Pending</span>
                <?php else: ?>
                    <span class="transfer-badge transfer-pending">⏳ Pending Conversion</span>
                <?php endif; ?>
            </span>
        </div>
    </div>
    
    <!-- Video Player or Processing Status -->
    <?php if ($video_processing): ?>
        <div class="processing-status">
            <div class="processing-status-icon">⏳</div>
            <div class="processing-status-title">Video Processing</div>
            <div class="processing-status-message">
                This video is still being converted to MP4 format.<br>
                Please check back in a few moments.
            </div>
        </div>
    <?php elseif ($video_url): ?>
        <video 
            class="event-video" 
            controls 
            autoplay 
            preload="auto"
            src="<?php echo $video_url; ?>"
        >
            Your browser does not support the video tag.
        </video>
    <?php else: ?>
        <div class="processing-status">
            <div class="processing-status-icon">✗</div>
            <div class="processing-status-title">Video Not Available</div>
            <div class="processing-status-message">
                The video file for this event could not be found.
            </div>
        </div>
    <?php endif; ?>
    
    <!-- Event Images -->
    <div class="event-images">
        <!-- Picture A (Motion Detection) -->
        <div class="event-image-container">
            <h3 class="image-label">Picture A (Motion Detection)</h3>
            <?php if ($image_a_url): ?>
                <img 
                    src="<?php echo $image_a_url; ?>" 
                    alt="Picture A - Motion Detection"
                    class="event-image"
                    onclick="openLightbox('<?php echo $image_a_url; ?>')"
                >
            <?php else: ?>
                <div class="image-placeholder">Image not available</div>
            <?php endif; ?>
        </div>
        
        <!-- Picture B (T+4 seconds) -->
        <div class="event-image-container">
            <h3 class="image-label">Picture B (T+4 seconds)</h3>
            <?php if ($image_b_url): ?>
                <img 
                    src="<?php echo $image_b_url; ?>" 
                    alt="Picture B - T+4 seconds"
                    class="event-image"
                    onclick="openLightbox('<?php echo $image_b_url; ?>')"
                >
            <?php else: ?>
                <div class="image-placeholder">Image not available</div>
            <?php endif; ?>
        </div>
    </div>
    
    <!-- Bottom Navigation -->
    <div class="event-navigation">
        <?php if ($prev_id): ?>
            <a href="event.php?id=<?php echo $prev_id; ?>" class="btn btn-secondary">
                ← Previous Event
            </a>
        <?php else: ?>
            <button class="btn btn-secondary" disabled>
                ← Previous Event
            </button>
        <?php endif; ?>
        
        <a href="index.php" class="btn btn-secondary">
            Back to Events
        </a>
        
        <?php if ($next_id): ?>
            <a href="event.php?id=<?php echo $next_id; ?>" class="btn btn-secondary">
                Next Event →
            </a>
        <?php else: ?>
            <button class="btn btn-secondary" disabled>
                Next Event →
            </button>
        <?php endif; ?>
    </div>
</div>

<!-- Lightbox for full-screen images -->
<div id="lightbox" class="lightbox" onclick="closeLightbox()">
    <span class="lightbox-close" onclick="closeLightbox()">✕</span>
    <img id="lightbox-image" src="" alt="Full size image">
</div>

<?php include 'includes/footer.php'; ?>