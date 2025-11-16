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
// Accept both 'complete' (just converted) and 'optimized' (compressed) as ready states
$video_processing = !in_array($event['mp4_conversion_status'], ['complete', 'optimized']);

// Get URLs for media files
$video_url = get_video_url($event);
$image_a_url = get_image_url($event['image_a_path']);
$image_b_url = get_image_url($event['image_b_path']);

// Get motion badge info based on confidence score
$badge = get_motion_badge($event['confidence_score'] ?? 0);

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
                <h1 class="event-id">
                    Event #<?php echo $event_id; ?>
                    <?php if (!empty($event['ai_phrase'])): ?>
                        <span class="event-ai-phrase"> • <?php echo htmlspecialchars($event['ai_phrase']); ?></span>
                    <?php endif; ?>
                </h1>
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
        
        <!-- Event Status -->
        <div class="detail-item">
            <span class="detail-label">Status:</span>
            <span class="detail-value">
                <?php 
                $status_badge = get_event_status_badge($event['status'] ?? 'complete');
                ?>
                <span class="badge badge-status-<?php echo $status_badge['color']; ?>">
                    <?php echo $status_badge['symbol']; ?> <?php echo $status_badge['label']; ?>
                </span>
            </span>
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
                <?php if (in_array($event['mp4_conversion_status'], ['complete', 'optimized']) && !empty($event['video_mp4_path'])): ?>
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
        
        <!-- AI Description -->
        <div class="detail-item">
            <span class="detail-label">Description:</span>
            <span class="detail-value">
                <?php if (!empty($event['ai_description'])): ?>
                    <div class="ai-description-container">
                        <div class="ai-description-text collapsed" id="ai-description-text">
                            <?php echo htmlspecialchars($event['ai_description']); ?>
                        </div>
                        <button class="ai-description-toggle" id="ai-description-toggle" onclick="toggleDescription()">
                            <span class="toggle-icon">▼</span> Show more
                        </button>
                    </div>
                <?php else: ?>
                    <span class="transfer-badge transfer-pending">⏳ AI analysis pending...</span>
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
            id="event-video"
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
                    data-lightbox-index="0"
                    data-lightbox-src="<?php echo $image_a_url; ?>"
                    data-lightbox-title="Picture A (Motion Detection)"
                    onclick="openLightbox(0)"
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
                    data-lightbox-index="1"
                    data-lightbox-src="<?php echo $image_b_url; ?>"
                    data-lightbox-title="Picture B (T+4 seconds)"
                    onclick="openLightbox(1)"
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
    <button class="lightbox-nav lightbox-prev" onclick="event.stopPropagation(); navigateLightbox(-1)">‹</button>
    <button class="lightbox-nav lightbox-next" onclick="event.stopPropagation(); navigateLightbox(1)">›</button>
    <div class="lightbox-title" id="lightbox-title"></div>
    <img id="lightbox-image" src="" alt="Full size image" onclick="event.stopPropagation()">
</div>

<script>
// Lightbox state
let currentLightboxIndex = 0;
let lightboxImages = [];

// Initialize lightbox images array
function initializeLightboxImages() {
    if (lightboxImages.length === 0) {
        const images = document.querySelectorAll('[data-lightbox-index]');
        console.log('Found images:', images.length); // Debug
        images.forEach(img => {
            const index = parseInt(img.dataset.lightboxIndex);
            const src = img.dataset.lightboxSrc;
            const title = img.dataset.lightboxTitle;
            console.log('Adding image:', index, src, title); // Debug
            lightboxImages[index] = {
                src: src,
                title: title
            };
        });
        console.log('Initialized lightboxImages:', lightboxImages); // Debug
    }
}

function openLightbox(index) {
    console.log('Opening lightbox with index:', index); // Debug
    initializeLightboxImages(); // Ensure images are loaded
    currentLightboxIndex = index;
    updateLightboxImage();
    document.getElementById('lightbox').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    document.getElementById('lightbox').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function navigateLightbox(direction) {
    currentLightboxIndex = (currentLightboxIndex + direction + lightboxImages.length) % lightboxImages.length;
    console.log('Navigating to index:', currentLightboxIndex); // Debug
    updateLightboxImage();
}

function updateLightboxImage() {
    const imageData = lightboxImages[currentLightboxIndex];
    console.log('Updating image with data:', imageData); // Debug
    if (imageData && imageData.src) {
        document.getElementById('lightbox-image').src = imageData.src;
        document.getElementById('lightbox-title').textContent = imageData.title;
    } else {
        console.error('No image data found for index:', currentLightboxIndex);
    }
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    const lightbox = document.getElementById('lightbox');
    if (lightbox.style.display === 'flex') {
        if (e.key === 'ArrowLeft') {
            navigateLightbox(-1);
        } else if (e.key === 'ArrowRight') {
            navigateLightbox(1);
        } else if (e.key === 'Escape') {
            closeLightbox();
        }
    }
});

// Touch/swipe support
let touchStartX = 0;
let touchEndX = 0;

document.getElementById('lightbox')?.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
}, false);

document.getElementById('lightbox')?.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}, false);

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swiped left - go to next image
            navigateLightbox(1);
        } else {
            // Swiped right - go to previous image
            navigateLightbox(-1);
        }
    }
}

// Toggle AI Description expansion
function toggleDescription() {
    const textElement = document.getElementById('ai-description-text');
    const toggleButton = document.getElementById('ai-description-toggle');
    const toggleIcon = toggleButton.querySelector('.toggle-icon');
    
    if (textElement.classList.contains('collapsed')) {
        textElement.classList.remove('collapsed');
        textElement.classList.add('expanded');
        toggleIcon.textContent = '▲';
        toggleButton.innerHTML = '<span class="toggle-icon">▲</span> Show less';
        // Save expanded state to localStorage
        localStorage.setItem('aiDescriptionExpanded', 'true');
    } else {
        textElement.classList.remove('expanded');
        textElement.classList.add('collapsed');
        toggleIcon.textContent = '▼';
        toggleButton.innerHTML = '<span class="toggle-icon">▼</span> Show more';
        // Save collapsed state to localStorage
        localStorage.setItem('aiDescriptionExpanded', 'false');
    }
}

// Initialize description state from localStorage on page load
document.addEventListener('DOMContentLoaded', function() {
    const textElement = document.getElementById('ai-description-text');
    const toggleButton = document.getElementById('ai-description-toggle');
    
    // Only apply if description exists on the page
    if (textElement && toggleButton) {
        const isExpanded = localStorage.getItem('aiDescriptionExpanded') === 'true';
        
        if (isExpanded) {
            // Apply expanded state
            textElement.classList.remove('collapsed');
            textElement.classList.add('expanded');
            toggleButton.innerHTML = '<span class="toggle-icon">▲</span> Show less';
        }
        // If not expanded or no preference saved, it stays in default collapsed state
    }
    
    // Video autoplay and speed control
    const video = document.getElementById('event-video');
    if (video) {
        // Set playback speed to 2x
        video.playbackRate = 2.0;
        
        // Ensure video plays (browsers may block autoplay without user interaction)
        video.play().catch(function(error) {
            console.log('Autoplay was prevented:', error);
            // Autoplay blocked - video will wait for user interaction
            // The controls are visible so user can click play
        });
        
        // Preserve playback speed if user changes it
        video.addEventListener('ratechange', function() {
            // Optional: Save user's preferred speed to localStorage
            // localStorage.setItem('videoPlaybackRate', video.playbackRate);
        });
    }
});
</script>

<?php include 'includes/footer.php'; ?>