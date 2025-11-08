// ========================================
// HAMBURGER MENU TOGGLE
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking a link (mobile)
        const navLinks = navMenu.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 768) {
                    hamburger.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });
        });
        
        // Close menu when clicking outside (mobile)
        document.addEventListener('click', function(event) {
            if (window.innerWidth < 768) {
                const isClickInsideNav = navMenu.contains(event.target);
                const isClickOnHamburger = hamburger.contains(event.target);
                
                if (!isClickInsideNav && !isClickOnHamburger && navMenu.classList.contains('active')) {
                    hamburger.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            }
        });
    }
});

// ============================================
// LIGHTBOX WITH SWIPE NAVIGATION
// ============================================

// Lightbox state
let currentLightboxIndex = 0;
let lightboxImages = [];

// Initialize lightbox images array
function initializeLightboxImages() {
    if (lightboxImages.length === 0) {
        const images = document.querySelectorAll('[data-lightbox-index]');
        images.forEach(img => {
            const index = parseInt(img.dataset.lightboxIndex);
            lightboxImages[index] = {
                src: img.dataset.lightboxSrc,
                title: img.dataset.lightboxTitle
            };
        });
    }
}

// Open lightbox with specific image index
function openLightbox(index) {
    initializeLightboxImages();
    currentLightboxIndex = index;
    updateLightboxImage();
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

// Close lightbox
function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Navigate between images (direction: -1 for previous, 1 for next)
function navigateLightbox(direction) {
    currentLightboxIndex = (currentLightboxIndex + direction + lightboxImages.length) % lightboxImages.length;
    updateLightboxImage();
}

// Update the displayed image and title
function updateLightboxImage() {
    const imageData = lightboxImages[currentLightboxIndex];
    if (imageData && imageData.src) {
        const lightboxImage = document.getElementById('lightbox-image');
        const lightboxTitle = document.getElementById('lightbox-title');
        
        if (lightboxImage) {
            lightboxImage.src = imageData.src;
        }
        if (lightboxTitle) {
            lightboxTitle.textContent = imageData.title;
        }
    }
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    const lightbox = document.getElementById('lightbox');
    if (lightbox && lightbox.style.display === 'flex') {
        if (e.key === 'ArrowLeft') {
            navigateLightbox(-1);
        } else if (e.key === 'ArrowRight') {
            navigateLightbox(1);
        } else if (e.key === 'Escape') {
            closeLightbox();
        }
    }
});

// Touch/swipe support for mobile
let touchStartX = 0;
let touchEndX = 0;

// Wait for DOM to be ready before adding touch listeners
document.addEventListener('DOMContentLoaded', function() {
    const lightbox = document.getElementById('lightbox');
    
    if (lightbox) {
        lightbox.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
        }, false);
        
        lightbox.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, false);
    }
});

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


/* ========================================
   LOGS PAGE - AJAX FUNCTIONALITY
   ======================================== */

/**
 * Get More Logs - AJAX function
 * Fetches new logs since last loaded timestamp
 */
function getMoreLogs() {
    const btn = document.getElementById('get-more-btn');
    const tbody = document.getElementById('logs-tbody');
    const lastTimestamp = document.getElementById('last-timestamp').value;
    const status = document.getElementById('logs-status');
    
    // Get filter state
    const filterInfo = document.getElementById('filter-info').value;
    const filterWarning = document.getElementById('filter-warning').value;
    const filterError = document.getElementById('filter-error').value;
    const filterSource = document.getElementById('filter-source').value;
    
    // Disable button and show loading
    btn.disabled = true;
    btn.textContent = 'Loading...';
    
    // Build query string
    const params = new URLSearchParams({
        since: lastTimestamp,
        info: filterInfo,
        warning: filterWarning,
        error: filterError
    });
    
    // Add source parameter if set
    if (filterSource) {
        params.append('source', filterSource);
    }
    
    // Fetch new logs
    fetch(`api/get_new_logs.php?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.logs.length > 0) {
                // Append new logs to table
                data.logs.forEach(log => {
                    const row = createLogRow(log);
                    tbody.appendChild(row);
                });
                
                // Update last timestamp
                document.getElementById('last-timestamp').value = data.logs[0].timestamp;
                
                // Update status
                status.textContent = `Showing logs (${data.logs.length} new logs loaded)`;
                
                // Scroll to bottom
                const container = document.querySelector('.logs-container');
                container.scrollTop = container.scrollHeight;
            } else {
                status.textContent = 'No new logs';
            }
            
            // Re-enable button
            btn.disabled = false;
            btn.textContent = 'Get More Logs';
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            status.textContent = 'Error loading logs';
            btn.disabled = false;
            btn.textContent = 'Get More Logs';
        });
}

/**
 * Helper function to create log row element
 * @param {Object} log - Log object with id, timestamp, level, message, source
 * @returns {HTMLElement} Table row element
 */
function createLogRow(log) {
    const tr = document.createElement('tr');
    tr.className = `log-row log-${log.level.toLowerCase()}`;
    
    // Check if we're showing all cameras (source column visible)
    const showSource = document.querySelector('.log-source') !== null;
    
    const sourceCell = showSource ? `<td class="log-source">${escapeHtml(log.source)}</td>` : '';
    
    tr.innerHTML = `
        <td class="log-id">${log.id}</td>
        ${sourceCell}
        <td class="log-timestamp">${formatLogTimestamp(log.timestamp)}</td>
        <td class="log-level">
            <span class="level-badge level-${log.level.toLowerCase()}">
                ${log.level}
            </span>
        </td>
        <td class="log-message">${escapeHtml(log.message)}</td>
    `;
    
    return tr;
}

/**
 * Helper to format timestamp in JavaScript
 * Format: Oct 19, 2025 8:43:15 PM
 * @param {string} timestamp - ISO format timestamp
 * @returns {string} Formatted timestamp
 */
function formatLogTimestamp(timestamp) {
    const date = new Date(timestamp);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: 'numeric', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: true 
    };
    return date.toLocaleString('en-US', options);
}

/**
 * Helper to escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* ========================================
   LIVE STREAMING CONTROL WITH HEARTBEAT
   ======================================== */

let streamInterval = null;
let streamStartTime = null;
let heartbeatInterval = null;
const HEARTBEAT_INTERVAL_MS = 10000; // 10 seconds

async function startStream() {
    const statusIndicator = document.getElementById('stream-status');
    const statusText = document.getElementById('stream-status-text');
    const streamButton = document.getElementById('stream-button');
    const streamImage = document.getElementById('stream-image');
    const streamPlaceholder = document.getElementById('stream-placeholder');
    const streamInfo = document.getElementById('stream-info');
    const streamContainer = document.getElementById('stream-container');
    
    // Get camera details from data attributes
    const cameraId = streamContainer.dataset.cameraId;
    const cameraIp = streamContainer.dataset.cameraIp;
    const cameraName = streamContainer.dataset.cameraName;
    
    try {
        // Disable button and show loading
        streamButton.disabled = true;
        streamButton.textContent = 'Starting...';
        statusText.textContent = 'Starting';
        
        // Call central server API (which calls camera API)
        const response = await fetch('api/set_streaming.php?action=start&camera=' + cameraId);
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Failed to start stream');
        }
        
        // Wait 2 seconds for MJPEG server to fully start
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Show stream
        streamPlaceholder.style.display = 'none';
        streamImage.style.display = 'block';
        streamImage.src = 'http://' + cameraIp + ':8080/stream.mjpg?t=' + Date.now();
        
        // Update status
        statusIndicator.classList.add('status-active');
        statusIndicator.classList.remove('status-inactive');
        statusText.textContent = 'Streaming';
        
        // Update button
        streamButton.textContent = 'Stop Stream';
        streamButton.disabled = false;
        streamButton.classList.remove('btn-success');
        streamButton.classList.add('btn-error');
        streamButton.onclick = stopStream;
        
        // Start timer
        streamStartTime = Date.now();
        startStreamTimer();
        
        // Start heartbeat
        startHeartbeat(cameraId);
        
        // Show stream info with camera name
        streamInfo.innerHTML = '<strong>' + escapeHtml(cameraName) + '</strong> - Motion detection paused while streaming';
        
    } catch (error) {
        console.error('Error starting stream:', error);
        statusText.textContent = 'Error';
        streamButton.textContent = 'Retry';
        streamButton.disabled = false;
        
        // Show user-friendly error message
        if (error.message.includes('unreachable')) {
            alert('Camera is currently offline or unreachable.\n\nCamera: ' + cameraName + '\n\nPlease check the camera and try again.');
        } else {
            alert('Failed to start stream: ' + error.message);
        }
    }
}

async function stopStream() {
    const statusIndicator = document.getElementById('stream-status');
    const statusText = document.getElementById('stream-status-text');
    const streamButton = document.getElementById('stream-button');
    const streamImage = document.getElementById('stream-image');
    const streamPlaceholder = document.getElementById('stream-placeholder');
    const streamInfo = document.getElementById('stream-info');
    const streamContainer = document.getElementById('stream-container');
    
    // Get camera ID from data attribute
    const cameraId = streamContainer.dataset.cameraId;
    const cameraName = streamContainer.dataset.cameraName;
    
    try {
        // Disable button
        streamButton.disabled = true;
        streamButton.textContent = 'Stopping...';
        
        // Stop heartbeat FIRST
        stopHeartbeat();
        
        // Stop timer
        stopStreamTimer();
        
        // Call central server API to stop camera stream
        const response = await fetch('api/set_streaming.php?action=stop&camera=' + cameraId);
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Failed to stop stream');
        }
        
        // Hide stream
        streamImage.style.display = 'none';
        streamImage.src = '';
        streamPlaceholder.style.display = 'flex';
        
        // Update status
        statusIndicator.classList.remove('status-active');
        statusIndicator.classList.add('status-inactive');
        statusText.textContent = 'Stopped';
        
        // Update button
        streamButton.textContent = 'Start Stream';
        streamButton.disabled = false;
        streamButton.classList.remove('btn-error');
        streamButton.classList.add('btn-success');
        streamButton.onclick = startStream;
        
        // Clear info
        streamInfo.textContent = '';
        
    } catch (error) {
        console.error('Error stopping stream:', error);
        streamButton.textContent = 'Stop Stream';
        streamButton.disabled = false;
        
        // Show error but still clean up UI
        streamImage.style.display = 'none';
        streamImage.src = '';
        streamPlaceholder.style.display = 'flex';
        
        alert('Error stopping stream: ' + error.message + '\n\nThe stream may have already been stopped.');
    }
}

function startHeartbeat(cameraId) {
    // Clear any existing heartbeat
    stopHeartbeat();
    
    // Send heartbeat every 10 seconds
    heartbeatInterval = setInterval(async () => {
        try {
            const response = await fetch('api/set_streaming.php?action=heartbeat&camera=' + cameraId);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                // Heartbeat failed - stream may have timed out or hit max duration
                console.warn('Heartbeat failed:', data.message);
                
                // Check if max duration exceeded
                if (data.max_duration_exceeded) {
                    console.log('Stream exceeded maximum duration, cleaning up UI');
                    // Stop heartbeat and clean up UI
                    stopHeartbeat();
                    await handleStreamStopped('Maximum stream duration (30 minutes) reached. Stream automatically stopped.');
                } else {
                    // Other error - log but keep trying
                    console.error('Heartbeat error:', data.message);
                }
            } else {
                // Heartbeat successful - optionally log elapsed time
                if (data.elapsed_seconds && data.elapsed_seconds % 60 === 0) {
                    console.log('Stream running for ' + Math.floor(data.elapsed_seconds / 60) + ' minutes');
                }
            }
        } catch (error) {
            console.error('Error sending heartbeat:', error);
            // Network error - camera might be down, but keep trying
        }
    }, HEARTBEAT_INTERVAL_MS);
    
    console.log('Heartbeat started (every ' + (HEARTBEAT_INTERVAL_MS / 1000) + ' seconds)');
}

function stopHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
        console.log('Heartbeat stopped');
    }
}

async function handleStreamStopped(message) {
    // Update UI to reflect that stream has stopped
    const statusIndicator = document.getElementById('stream-status');
    const statusText = document.getElementById('stream-status-text');
    const streamButton = document.getElementById('stream-button');
    const streamImage = document.getElementById('stream-image');
    const streamPlaceholder = document.getElementById('stream-placeholder');
    const streamInfo = document.getElementById('stream-info');
    
    // Stop timer
    stopStreamTimer();
    
    // Hide stream
    streamImage.style.display = 'none';
    streamImage.src = '';
    streamPlaceholder.style.display = 'flex';
    
    // Update status
    statusIndicator.classList.remove('status-active');
    statusIndicator.classList.add('status-inactive');
    statusText.textContent = 'Stopped';
    
    // Update button
    streamButton.textContent = 'Start Stream';
    streamButton.disabled = false;
    streamButton.classList.remove('btn-error');
    streamButton.classList.add('btn-success');
    streamButton.onclick = startStream;
    
    // Clear info
    streamInfo.textContent = '';
    
    // Notify user
    if (message) {
        alert(message);
    }
}

function startStreamTimer() {
    stopStreamTimer(); // Clear any existing timer
    
    streamInterval = setInterval(() => {
        if (!streamStartTime) return;
        
        const elapsed = Date.now() - streamStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        const timerElement = document.getElementById('stream-timer');
        if (timerElement) {
            timerElement.textContent = `Stream running for: ${minutes}m ${seconds}s`;
        }
    }, 1000);
}

function stopStreamTimer() {
    if (streamInterval) {
        clearInterval(streamInterval);
        streamInterval = null;
    }
    streamStartTime = null;
    
    const timerElement = document.getElementById('stream-timer');
    if (timerElement) {
        timerElement.textContent = '';
    }
}

// Cleanup on page unload - use sendBeacon for more reliable cleanup
window.addEventListener('beforeunload', function(e) {
    const streamImage = document.getElementById('stream-image');
    const streamContainer = document.getElementById('stream-container');
    
    // Check if stream is active
    if (streamImage && streamImage.style.display !== 'none' && streamContainer) {
        const cameraId = streamContainer.dataset.cameraId;
        
        // Stop heartbeat immediately
        stopHeartbeat();
        
        // Use sendBeacon for more reliable cleanup (non-blocking)
        const url = 'api/set_streaming.php?action=stop&camera=' + cameraId;
        
        // Try sendBeacon first (preferred for page unload)
        if (navigator.sendBeacon) {
            // sendBeacon only supports POST with specific content types
            // Our PHP script expects GET parameters, so we need to send as POST with URL params
            navigator.sendBeacon(url);
        } else {
            // Fallback to synchronous XHR (deprecated but more reliable than async on unload)
            try {
                const xhr = new XMLHttpRequest();
                xhr.open('GET', url, false); // false = synchronous
                xhr.send();
            } catch (error) {
                console.error('Error in cleanup:', error);
            }
        }
    }
});

// Handle camera selector change - stop stream before switching
document.addEventListener('DOMContentLoaded', function() {
    const cameraSelect = document.getElementById('camera-select');
    
    if (cameraSelect) {
        // Intercept form submission to stop stream first
        cameraSelect.form.addEventListener('submit', async function(e) {
            const streamImage = document.getElementById('stream-image');
            const streamContainer = document.getElementById('stream-container');
            
            // Check if stream is active
            if (streamImage && streamImage.style.display !== 'none' && streamContainer) {
                e.preventDefault(); // Prevent immediate form submission
                
                const cameraId = streamContainer.dataset.cameraId;
                
                // Stop heartbeat
                stopHeartbeat();
                
                // Stop stream via AJAX
                try {
                    const response = await fetch('api/set_streaming.php?action=stop&camera=' + cameraId);
                    await response.json(); // Wait for response but don't check - best effort
                } catch (error) {
                    console.error('Error stopping stream during camera switch:', error);
                }
                
                // Now submit the form
                this.submit();
            }
            // If stream not active, allow normal form submission
        });
    }
    
    // Auto-start stream on page load
    if (document.getElementById('stream-container')) {
        startStream();
    }
});


/* ========================================
   FOOTER CAMERA STATUS - JavaScript
   ======================================== */

/**
 * Show camera details modal
 * @param {HTMLElement} element - The clicked camera status item
 */
function showCameraDetails(element) {
    try {
        // Get camera data from data attribute
        const cameraData = JSON.parse(element.getAttribute('data-camera'));
        
        // Build modal content
        const modalBody = document.getElementById('camera-details-body');
        const modalTitle = document.getElementById('modal-title');
        
        modalTitle.textContent = cameraData.name;
        
        // Status badge HTML
        let statusBadge = '';
        if (cameraData.status === 'online') {
            statusBadge = '<span class="status-badge online"><span class="indicator">●</span> Online</span>';
        } else if (cameraData.status === 'offline') {
            statusBadge = '<span class="status-badge offline"><span class="indicator">●</span> Offline</span>';
        } else if (cameraData.status === 'error') {
            statusBadge = '<span class="status-badge error"><span class="indicator">●</span> Error</span>';
        }
        
        // Build details HTML
        modalBody.innerHTML = `
            <div class="detail-row">
                <span class="detail-label">Status</span>
                <span class="detail-value">${statusBadge}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Camera ID</span>
                <span class="detail-value">${escapeHtml(cameraData.camera_id)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Location</span>
                <span class="detail-value">${escapeHtml(cameraData.location)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">IP Address</span>
                <span class="detail-value">${escapeHtml(cameraData.ip_address)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Version</span>
                <span class="detail-value">${escapeHtml(cameraData.version)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Uptime</span>
                <span class="detail-value">${escapeHtml(cameraData.uptime)}</span>
            </div>
        `;
        
        // Show modal
        const modal = document.getElementById('camera-details-modal');
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus management for accessibility
        modal.querySelector('.modal-close').focus();
        
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
        
    } catch (error) {
        console.error('Error showing camera details:', error);
    }
}

/**
 * Close camera details modal
 */
function closeCameraDetails() {
    const modal = document.getElementById('camera-details-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    
    // Restore body scroll
    document.body.style.overflow = '';
}

/**
 * Refresh camera status via AJAX
 */
async function refreshCameraStatus() {
    const refreshBtn = document.getElementById('refresh-status');
    
    if (!refreshBtn) return;
    
    try {
        // Disable button and show loading state
        refreshBtn.disabled = true;
        refreshBtn.classList.add('refreshing');
        
        // Call refresh API
        const response = await fetch('/api/refresh_camera_status.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Update camera status in footer
            updateCameraStatusDisplay(data.cameras);
            
            // Update button title with new cache time
            refreshBtn.setAttribute('title', 'Refresh camera status (last updated 0s ago)');
        } else {
            throw new Error(data.message || 'Failed to refresh camera status');
        }
        
    } catch (error) {
        console.error('Error refreshing camera status:', error);
        alert('Failed to refresh camera status. Please try again.');
    } finally {
        // Re-enable button and remove loading state
        refreshBtn.disabled = false;
        refreshBtn.classList.remove('refreshing');
    }
}

/**
 * Update camera status display with fresh data
 * @param {Array} cameras - Array of camera status objects
 */
function updateCameraStatusDisplay(cameras) {
    const statusGrid = document.querySelector('.camera-status-grid');
    
    if (!statusGrid) return;
    
    // Clear existing items
    statusGrid.innerHTML = '';
    
    if (!cameras || cameras.length === 0) {
        statusGrid.innerHTML = '<div class="camera-status-item status-none"><span class="camera-name">No cameras deployed</span></div>';
        return;
    }
    
    // Add updated camera status items
    cameras.forEach(cam => {
        const item = document.createElement('div');
        item.className = `camera-status-item status-${cam.status}`;
        item.setAttribute('data-camera', JSON.stringify(cam));
        item.setAttribute('onclick', 'showCameraDetails(this)');
        item.setAttribute('role', 'button');
        item.setAttribute('tabindex', '0');
        item.setAttribute('title', 'Click for details');
        
        item.innerHTML = `
            <span class="camera-name">${escapeHtml(cam.name)}</span>
            <span class="camera-indicator">●</span>
            <span class="camera-version">v${escapeHtml(cam.version)}</span>
        `;
        
        statusGrid.appendChild(item);
    });
}

/**
 * Initialize footer camera status functionality
 */
function initFooterCameraStatus() {
    // Attach refresh button handler
    const refreshBtn = document.getElementById('refresh-status');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshCameraStatus);
    }
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('camera-details-modal');
            if (modal && modal.classList.contains('active')) {
                closeCameraDetails();
            }
        }
    });
    
    // Make camera status items keyboard accessible
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            const target = e.target;
            if (target && target.classList.contains('camera-status-item') && target.hasAttribute('data-camera')) {
                e.preventDefault();
                showCameraDetails(target);
            }
        }
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initFooterCameraStatus();
});