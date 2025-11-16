<?php
/**
 * Logs Page - System Log Viewer
 * Terminal-style display with filtering and AJAX "Get Newer Logs" functionality
 */

require_once 'includes/session.php';
require_once 'includes/db.php';
require_once 'includes/functions.php';
require_once 'includes/camera_selector.php';

// Handle camera selection BEFORE any output
handle_camera_selection();

$db = new Database();

// Get selected camera for filtering logs
$camera_id = get_selected_camera();

// Map camera selection to log source filter
// 'all' means show all sources (including 'central')
// 'camera_1' means show only 'camera_1' logs
$source_filter = ($camera_id === 'all') ? null : $camera_id;

// Parse filter parameters from URL
$filter_info = isset($_GET['info']) ? 1 : 0;
$filter_warning = isset($_GET['warning']) ? 1 : 0;
$filter_error = isset($_GET['error']) ? 1 : 0;

// If no filters in URL, default to all checked
if (!isset($_GET['info']) && !isset($_GET['warning']) && !isset($_GET['error'])) {
    $filter_info = 1;
    $filter_warning = 1;
    $filter_error = 1;
}

// Build level filter array
$level_filter = [];
if ($filter_info) $level_filter[] = 'INFO';
if ($filter_warning) $level_filter[] = 'WARNING';
if ($filter_error) $level_filter[] = 'ERROR';

// Get last 1000 logs with current filter (ordered ASC - oldest to newest)
$logs = [];
$no_filters_selected = empty($level_filter);

if (!$no_filters_selected) {
    $logs = $db->get_logs(1000, $level_filter, $source_filter);
}

// Get the most recent log ID for "Get Newer Logs" functionality
$last_log_id = !empty($logs) ? $logs[count($logs) - 1]['id'] : 0;

// Page title
$page_title = 'System Logs';

// Include header
include 'includes/header.php';
?>

<div class="container">
    <h1 class="logs-title">System Logs</h1>
    
    <!-- Combined Filter Section (Camera + Level Filters) -->
    <div class="per-page-selector">
        <!-- Camera Selector (left side) - handles its own form submission -->
        <div class="camera-filter-section">
            <?php render_camera_selector('logs.php'); ?>
        </div>
        
        <!-- Level Checkboxes (right side) - separate form -->
        <form method="get" action="logs.php" class="level-filters-form">
            <div class="level-filters-section">
                <label class="filter-checkbox">
                    <input 
                        type="checkbox" 
                        name="info" 
                        value="1"
                        <?php echo $filter_info ? 'checked' : ''; ?>
                        onchange="this.form.submit()"
                    >
                    <span class="filter-label">INFO</span>
                </label>
                
                <label class="filter-checkbox">
                    <input 
                        type="checkbox" 
                        name="warning" 
                        value="1"
                        <?php echo $filter_warning ? 'checked' : ''; ?>
                        onchange="this.form.submit()"
                    >
                    <span class="filter-label">WARNING</span>
                </label>
                
                <label class="filter-checkbox">
                    <input 
                        type="checkbox" 
                        name="error" 
                        value="1"
                        <?php echo $filter_error ? 'checked' : ''; ?>
                        onchange="this.form.submit()"
                    >
                    <span class="filter-label">ERROR</span>
                </label>
            </div>
        </form>
    </div>
    
    <?php if ($no_filters_selected): ?>
        <!-- No Filters Selected Message -->
        <div class="logs-status" style="text-align: center; padding: var(--space-xl); color: var(--color-text-secondary);">
            Please select at least one filter level
        </div>
    <?php elseif (empty($logs)): ?>
        <!-- No Logs Found Message -->
        <div class="logs-status" style="text-align: center; padding: var(--space-xl); color: var(--color-text-secondary);">
            No logs found for selected filters
        </div>
    <?php else: ?>
        <!-- Logs Table -->
        <div class="logs-container">
            <table class="logs-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <?php if (is_all_cameras_selected()): ?>
                            <th>Source</th>
                        <?php endif; ?>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody id="logs-tbody">
                    <?php foreach ($logs as $log): ?>
                        <tr class="log-row log-<?php echo strtolower($log['level']); ?>">
                            <td class="log-id"><?php echo htmlspecialchars($log['id']); ?></td>
                            <?php if (is_all_cameras_selected()): ?>
                                <td class="log-source"><?php echo htmlspecialchars($log['source']); ?></td>
                            <?php endif; ?>
                            <td class="log-timestamp">
                                <?php echo format_log_timestamp($log['timestamp']); ?>
                            </td>
                            <td class="log-level">
                                <span class="level-badge level-<?php echo strtolower($log['level']); ?>">
                                    <?php echo htmlspecialchars($log['level']); ?>
                                </span>
                            </td>
                            <td class="log-message"><?php echo htmlspecialchars($log['message']); ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        
        <!-- Get Newer Logs Button and Status -->
        <div class="logs-actions">
            <button id="get-newer-btn" class="btn btn-primary" onclick="getNewerLogs()">
                Get Newer Logs
            </button>
            <span id="new-logs-badge" class="new-logs-badge" style="display: none;">
                +<span id="new-logs-count">0</span> new
            </span>
        </div>
        
        <div id="logs-status" class="logs-status">
            Showing <?php echo count($logs); ?> most recent logs
        </div>
        
        <!-- Hidden inputs for JavaScript -->
        <input type="hidden" id="last-log-id" value="<?php echo htmlspecialchars($last_log_id); ?>">
        <input type="hidden" id="filter-info" value="<?php echo $filter_info; ?>">
        <input type="hidden" id="filter-warning" value="<?php echo $filter_warning; ?>">
        <input type="hidden" id="filter-error" value="<?php echo $filter_error; ?>">
        <input type="hidden" id="filter-source" value="<?php echo htmlspecialchars($source_filter ?? ''); ?>">
        <input type="hidden" id="show-source-column" value="<?php echo is_all_cameras_selected() ? '1' : '0'; ?>">
    <?php endif; ?>
</div>

<script>
// Auto-scroll to bottom on page load (showing newest logs)
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.logs-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
});

/**
 * Fetch newer logs via AJAX and append to bottom of table
 */
function getNewerLogs() {
    const lastLogId = document.getElementById('last-log-id').value;
    const filterInfo = document.getElementById('filter-info').value;
    const filterWarning = document.getElementById('filter-warning').value;
    const filterError = document.getElementById('filter-error').value;
    const filterSource = document.getElementById('filter-source').value;
    const showSourceColumn = document.getElementById('show-source-column').value === '1';
    
    const button = document.getElementById('get-newer-btn');
    const badge = document.getElementById('new-logs-badge');
    const statusDiv = document.getElementById('logs-status');
    
    // Disable button during fetch
    button.disabled = true;
    button.textContent = 'Loading...';
    
    // Prepare form data
    const formData = new FormData();
    formData.append('last_log_id', lastLogId);
    formData.append('filter_info', filterInfo);
    formData.append('filter_warning', filterWarning);
    formData.append('filter_error', filterError);
    formData.append('source_filter', filterSource);
    
    // Fetch newer logs
    fetch('ajax/get_newer_logs.php', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const tbody = document.getElementById('logs-tbody');
            const currentRowCount = tbody.children.length;
            
            if (data.count > 0) {
                // Append new logs to bottom
                data.logs.forEach(log => {
                    const row = createLogRow(log, showSourceColumn);
                    tbody.appendChild(row);
                });
                
                // Update last log ID
                document.getElementById('last-log-id').value = data.new_last_id;
                
                // Show badge with count
                document.getElementById('new-logs-count').textContent = data.count;
                badge.style.display = 'inline-block';
                
                // Update status
                const newTotal = currentRowCount + data.count;
                statusDiv.textContent = `Showing ${newTotal} logs (+${data.count} new)`;
                
                // Hide badge after 3 seconds
                setTimeout(() => {
                    badge.style.display = 'none';
                }, 3000);
            } else {
                // No new logs
                statusDiv.textContent = `Showing ${currentRowCount} logs (no new logs)`;
            }
        } else {
            console.error('Error fetching logs:', data.error);
            statusDiv.textContent = 'Error loading logs';
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        statusDiv.textContent = 'Error loading logs';
    })
    .finally(() => {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Get Newer Logs';
    });
}

/**
 * Create a table row element for a log entry
 */
function createLogRow(log, showSourceColumn) {
    const row = document.createElement('tr');
    row.className = `log-row log-${log.level.toLowerCase()}`;
    
    // ID column
    const idCell = document.createElement('td');
    idCell.className = 'log-id';
    idCell.textContent = log.id;
    row.appendChild(idCell);
    
    // Source column (if showing all cameras)
    if (showSourceColumn) {
        const sourceCell = document.createElement('td');
        sourceCell.className = 'log-source';
        sourceCell.textContent = log.source;
        row.appendChild(sourceCell);
    }
    
    // Timestamp column
    const timestampCell = document.createElement('td');
    timestampCell.className = 'log-timestamp';
    timestampCell.textContent = formatLogTimestamp(log.timestamp);
    row.appendChild(timestampCell);
    
    // Level column
    const levelCell = document.createElement('td');
    levelCell.className = 'log-level';
    const levelBadge = document.createElement('span');
    levelBadge.className = `level-badge level-${log.level.toLowerCase()}`;
    levelBadge.textContent = log.level;
    levelCell.appendChild(levelBadge);
    row.appendChild(levelCell);
    
    // Message column
    const messageCell = document.createElement('td');
    messageCell.className = 'log-message';
    messageCell.textContent = log.message;
    row.appendChild(messageCell);
    
    return row;
}

/**
 * Format log timestamp for display
 * This should match your PHP format_log_timestamp() function
 */
function formatLogTimestamp(timestamp) {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}
</script>

<style>
/* Badge styling for new logs count */
.new-logs-badge {
    display: inline-block;
    margin-left: 10px;
    padding: 4px 12px;
    background-color: var(--color-success, #28a745);
    color: white;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: scale(0.8);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}
</style>

<?php
// Include footer
include 'includes/footer.php';
?>