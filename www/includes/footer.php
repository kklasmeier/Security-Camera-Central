<?php
require_once __DIR__ . '/camera_status.php';
$camera_status = get_all_camera_status();
$cache_age = get_cache_age();
?>

</main>
    
    <footer class="site-footer">
        <div class="footer-content">
            <div class="footer-left">
                <p>Security Camera System &copy; <?php echo date('Y'); ?></p>
                <p class="footer-subtitle">Raspberry Pi Zero 2 W</p>
            </div>
            
            <div class="footer-right">
                <div class="camera-status-grid">
                    <?php if (empty($camera_status)): ?>
                        <div class="camera-status-item status-none">
                            <span class="camera-name">No cameras deployed</span>
                        </div>
                    <?php else: ?>
                        <?php foreach ($camera_status as $cam): ?>
                        <div class="camera-status-item status-<?php echo $cam['status']; ?>" 
                             data-camera='<?php echo htmlspecialchars(json_encode($cam), ENT_QUOTES, 'UTF-8'); ?>'
                             onclick="showCameraDetails(this)"
                             role="button"
                             tabindex="0"
                             title="Click for details">
                            <span class="camera-name"><?php echo htmlspecialchars($cam['name']); ?></span>
                            <span class="camera-indicator">●</span>
                            <span class="camera-version">v<?php echo htmlspecialchars($cam['version']); ?></span>
                        </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
                
                <?php if (!empty($camera_status)): ?>
                <button id="refresh-status" 
                        class="btn-refresh" 
                        title="Refresh camera status (last updated <?php echo $cache_age; ?>s ago)"
                        aria-label="Refresh camera status">
                    ↻
                </button>
                <?php endif; ?>
            </div>
        </div>
    </footer>
    
    <!-- Camera Details Modal -->
    <div id="camera-details-modal" class="modal" role="dialog" aria-labelledby="modal-title" aria-hidden="true">
        <div class="modal-overlay" onclick="closeCameraDetails()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modal-title">Camera Details</h3>
                <button class="modal-close" onclick="closeCameraDetails()" aria-label="Close modal">&times;</button>
            </div>
            <div class="modal-body" id="camera-details-body">
                <!-- Details populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script src="/assets/script.js"></script>
</body>
</html>