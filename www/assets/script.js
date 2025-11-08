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
   LIVE STREAMING CONTROL
   ======================================== */

let streamInterval = null;
let streamStartTime = null;

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

// Cleanup on page unload
window.addEventListener('beforeunload', function(e) {
    // Stop stream if active
    const streamImage = document.getElementById('stream-image');
    const streamContainer = document.getElementById('stream-container');
    
    if (streamImage && streamImage.style.display !== 'none' && streamContainer) {
        const cameraId = streamContainer.dataset.cameraId;
        
        // Use synchronous request for cleanup
        const xhr = new XMLHttpRequest();
        xhr.open('GET', 'api/set_streaming.php?action=stop&camera=' + cameraId, false); // false = synchronous
        xhr.send();
    }
});

// Auto-start stream on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the live view page
    if (document.getElementById('stream-container')) {
        startStream();
    }
});