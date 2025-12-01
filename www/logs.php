<?php
/**
 * Logs Page - System Log Viewer
 * Terminal-style display with filtering, search, and AJAX "Get Newer Logs" functionality
 */

require_once 'includes/session.php';
require_once 'includes/db.php';
require_once 'includes/functions.php';
require_once 'includes/camera_selector.php';

// Handle camera selection BEFORE any output
handle_camera_selection();

$db = new Database();

// Build camera_id -> name lookup for source column display
$cameras = $db->get_all_cameras();
$camera_names = [];
foreach ($cameras as $camera) {
    $camera_names[$camera['camera_id']] = $camera['name'];
}

// Get selected camera for filtering logs
$camera_id = get_selected_camera();

// Map camera selection to log source filter
$source_filter = ($camera_id === 'all') ? null : $camera_id;

// Handle advanced filter form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['apply_filters'])) {
    // Save expanded state
    set_logs_filters_expanded(true);
    
    // Save result limit
    if (isset($_POST['result_limit'])) {
        set_logs_result_limit((int)$_POST['result_limit']);
    }
    
    // Save date filters
    set_logs_date_from($_POST['date_from'] ?? null);
    set_logs_date_to($_POST['date_to'] ?? null);
    set_logs_time_from(isset($_POST['time_from']) ? (int)$_POST['time_from'] : 0);
    set_logs_time_to(isset($_POST['time_to']) ? (int)$_POST['time_to'] : 23);
    
    // Redirect to prevent form resubmission
    header('Location: logs.php?' . http_build_query($_GET));
    exit;
}

// Handle clear dates
if (isset($_GET['clear_dates'])) {
    clear_logs_date_filters();
    // Remove clear_dates from URL and redirect
    $params = $_GET;
    unset($params['clear_dates']);
    header('Location: logs.php?' . http_build_query($params));
    exit;
}

// Handle toggle expanded state via AJAX or GET
if (isset($_GET['toggle_expanded'])) {
    set_logs_filters_expanded(!get_logs_filters_expanded());
    $params = $_GET;
    unset($params['toggle_expanded']);
    header('Location: logs.php?' . http_build_query($params));
    exit;
}

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

// Get session-stored advanced filter values
$filters_expanded = get_logs_filters_expanded();
$result_limit = get_logs_result_limit();
$date_from = get_logs_date_from();
$date_to = get_logs_date_to();
$time_from = get_logs_time_from();
$time_to = get_logs_time_to();

// Build datetime strings for query
$start_datetime = null;
$end_datetime = null;

if ($date_from) {
    $start_datetime = $date_from . ' ' . sprintf('%02d', $time_from) . ':00:00';
}
if ($date_to) {
    $end_datetime = $date_to . ' ' . sprintf('%02d', $time_to) . ':59:59';
}

// Check if date filters are active (for UI indicator)
$has_date_filter = has_logs_date_filter();

// Get logs with current filters
$logs = [];
$no_filters_selected = empty($level_filter);

if (!$no_filters_selected) {
    $logs = $db->get_logs($result_limit, $level_filter, $source_filter, $start_datetime, $end_datetime);
}

// Check if we hit the limit
$hit_limit = count($logs) >= $result_limit;

// Get the most recent log ID for "Get Newer Logs" functionality
$last_log_id = !empty($logs) ? $logs[count($logs) - 1]['id'] : 0;

// Page title
$page_title = 'System Logs';

// Include header
include 'includes/header.php';
?>

<div class="container">
    <h1 class="logs-title">System Logs</h1>
    
    <!-- Combined Filter Section (Camera + Search + Level Filters) -->
    <div class="per-page-selector">
        <!-- Camera Selector (left side) - handles its own form submission -->
        <div class="camera-filter-section">
            <?php render_camera_selector('logs.php'); ?>
        </div>
        
        <!-- Search Box (middle) -->
        <div class="search-filter-section">
            <div class="search-box-wrapper">
                <input 
                    type="text" 
                    id="log-search-input" 
                    class="log-search-input" 
                    placeholder="Search logs..."
                    autocomplete="off"
                >
                <button 
                    id="clear-search-btn" 
                    class="clear-search-btn" 
                    style="display: none;"
                    onclick="clearSearch()"
                    title="Clear search"
                >
                    ×
                </button>
            </div>
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
        
        <!-- Advanced Filters Toggle -->
        <a href="?<?php echo http_build_query(array_merge($_GET, ['toggle_expanded' => 1])); ?>" 
           class="advanced-filters-toggle <?php echo $has_date_filter ? 'has-active-filters' : ''; ?>"
           title="Advanced Filters">
            <span class="gear-icon">⚙</span>
            <?php if ($has_date_filter): ?>
                <span class="filter-indicator"></span>
            <?php endif; ?>
        </a>
    </div>
    
    <!-- Advanced Filters Panel (Collapsible) -->
    <?php if ($filters_expanded): ?>
    <div class="advanced-filters-panel">
        <form method="post" action="logs.php?<?php echo http_build_query($_GET); ?>" class="advanced-filters-form">
            <div class="advanced-filters-header">
                <span>Advanced Filters</span>
            </div>
            
            <div class="advanced-filters-content">
                <!-- Row 1: Results Limit + Quick Presets -->
                <div class="filter-row">
                    <div class="filter-group">
                        <label for="result_limit">Results:</label>
                        <select name="result_limit" id="result_limit" class="filter-select">
                            <?php foreach (get_valid_log_limits() as $limit_option): ?>
                                <option value="<?php echo $limit_option; ?>" <?php echo $result_limit == $limit_option ? 'selected' : ''; ?>>
                                    <?php echo number_format($limit_option); ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    
                    <div class="filter-group presets-group">
                        <button type="button" class="preset-btn" onclick="setPreset('today')">Today</button>
                        <button type="button" class="preset-btn" onclick="setPreset('yesterday')">Yesterday</button>
                        <button type="button" class="preset-btn" onclick="setPreset('last7')">Last 7 Days</button>
                        <button type="button" class="preset-btn" onclick="setPreset('last30')">Last 30 Days</button>
                    </div>
                </div>
                
                <!-- Row 2: Date Range -->
                <div class="filter-row">
                    <div class="filter-group date-range-group">
                        <div class="date-input-group">
                            <label for="date_from">From:</label>
                            <input type="date" name="date_from" id="date_from" 
                                   value="<?php echo htmlspecialchars($date_from ?? ''); ?>" 
                                   class="filter-input">
                            <select name="time_from" id="time_from" class="filter-select time-select">
                                <?php for ($h = 0; $h < 24; $h++): ?>
                                    <option value="<?php echo $h; ?>" <?php echo $time_from == $h ? 'selected' : ''; ?>>
                                        <?php echo sprintf('%02d:00', $h); ?>
                                    </option>
                                <?php endfor; ?>
                            </select>
                        </div>
                        
                        <div class="date-input-group">
                            <label for="date_to">To:</label>
                            <input type="date" name="date_to" id="date_to" 
                                   value="<?php echo htmlspecialchars($date_to ?? ''); ?>" 
                                   class="filter-input">
                            <select name="time_to" id="time_to" class="filter-select time-select">
                                <?php for ($h = 0; $h < 24; $h++): ?>
                                    <option value="<?php echo $h; ?>" <?php echo $time_to == $h ? 'selected' : ''; ?>>
                                        <?php echo sprintf('%02d:59', $h); ?>
                                    </option>
                                <?php endfor; ?>
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- Row 3: Action Buttons -->
                <div class="filter-row">
                    <div class="filter-group actions-group">
                        <button type="submit" name="apply_filters" value="1" class="btn btn-primary">Apply Filters</button>
                        <a href="?<?php echo http_build_query(array_merge($_GET, ['clear_dates' => 1])); ?>" class="btn btn-secondary">Clear Dates</a>
                    </div>
                </div>
            </div>
        </form>
    </div>
    <?php endif; ?>
    
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
                        <tr class="log-row log-<?php echo strtolower($log['level']); ?>" data-log-id="<?php echo htmlspecialchars($log['id']); ?>">
                            <td class="log-id"><?php echo htmlspecialchars($log['id']); ?></td>
                            <?php if (is_all_cameras_selected()): ?>
                                <td class="log-source"><?php 
                                    $source_id = $log['source'];
                                    $source_display = isset($camera_names[$source_id]) ? $camera_names[$source_id] : $source_id;
                                    echo htmlspecialchars($source_display); 
                                ?></td>
                            <?php endif; ?>
                            <td class="log-timestamp">
                                <?php 
                                $ts = strtotime($log['timestamp']);
                                $date_part = date('M j, Y', $ts);
                                $time_part = date('g:i:s A', $ts);
                                ?>
                                <span class="ts-date"><?php echo $date_part; ?></span>
                                <span class="ts-time"><?php echo $time_part; ?></span>
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
            <?php
            if ($has_date_filter) {
                $from_display = $date_from ? date('M j', strtotime($date_from)) . ' ' . sprintf('%02d:00', $time_from) : 'beginning';
                $to_display = $date_to ? date('M j', strtotime($date_to)) . ' ' . sprintf('%02d:59', $time_to) : 'now';
                echo 'Showing ' . number_format(count($logs)) . ' logs from ' . $from_display . ' to ' . $to_display;
                if ($hit_limit) {
                    echo ' (limit reached)';
                }
            } else {
                echo 'Showing ' . number_format(count($logs)) . ' most recent logs';
            }
            ?>
        </div>
        
        <!-- Hidden inputs for JavaScript -->
        <input type="hidden" id="last-log-id" value="<?php echo htmlspecialchars($last_log_id); ?>">
        <input type="hidden" id="filter-info" value="<?php echo $filter_info; ?>">
        <input type="hidden" id="filter-warning" value="<?php echo $filter_warning; ?>">
        <input type="hidden" id="filter-error" value="<?php echo $filter_error; ?>">
        <input type="hidden" id="filter-source" value="<?php echo htmlspecialchars($source_filter ?? ''); ?>">
        <input type="hidden" id="show-source-column" value="<?php echo is_all_cameras_selected() ? '1' : '0'; ?>">
        <input type="hidden" id="result-limit" value="<?php echo $result_limit; ?>">
        <input type="hidden" id="camera-names" value="<?php echo htmlspecialchars(json_encode($camera_names)); ?>">
    <?php endif; ?>
</div>

<script>
// Global state
let searchDebounceTimer = null;

// Auto-scroll to bottom on page load (showing newest logs)
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.logs-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
    
    // Set up search input listener
    const searchInput = document.getElementById('log-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // Show/hide clear button
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) {
                clearBtn.style.display = this.value ? 'flex' : 'none';
            }
            
            // Debounced search
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(function() {
                filterLogsBySearch();
            }, 300);
        });
        
        // Allow Enter key to trigger immediate search
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(searchDebounceTimer);
                filterLogsBySearch();
            }
        });
    }
});

/**
 * Clear search input and show all logs
 */
function clearSearch() {
    const searchInput = document.getElementById('log-search-input');
    const clearBtn = document.getElementById('clear-search-btn');
    
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    
    filterLogsBySearch();
}

/**
 * Filter visible log rows based on search input
 */
function filterLogsBySearch() {
    const searchInput = document.getElementById('log-search-input');
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const tbody = document.getElementById('logs-tbody');
    
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('.log-row');
    let visibleCount = 0;
    const totalCount = rows.length;
    
    rows.forEach(row => {
        if (searchTerm === '') {
            row.style.display = '';
            visibleCount++;
        } else {
            const rowText = row.textContent.toLowerCase();
            const matches = rowText.includes(searchTerm);
            row.style.display = matches ? '' : 'none';
            if (matches) visibleCount++;
        }
    });
    
    updateLogsStatus(visibleCount, totalCount, searchTerm !== '');
}

/**
 * Update the logs status message
 */
function updateLogsStatus(visibleCount, totalCount, hasSearch) {
    const statusDiv = document.getElementById('logs-status');
    if (!statusDiv) return;
    
    if (hasSearch) {
        if (visibleCount === totalCount) {
            statusDiv.textContent = `Showing ${totalCount.toLocaleString()} logs (all match search)`;
        } else {
            statusDiv.textContent = `Showing ${visibleCount.toLocaleString()} of ${totalCount.toLocaleString()} logs (${visibleCount.toLocaleString()} matching search)`;
        }
    } else {
        statusDiv.textContent = `Showing ${totalCount.toLocaleString()} logs`;
    }
}

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
    const resultLimit = document.getElementById('result-limit').value;
    
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
    formData.append('result_limit', resultLimit);
    
    // Fetch newer logs
    fetch('ajax/get_newer_logs.php', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const tbody = document.getElementById('logs-tbody');
            const currentRowCount = tbody.querySelectorAll('.log-row').length;
            
            if (data.count > 0) {
                const searchInput = document.getElementById('log-search-input');
                const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
                const cameraNames = JSON.parse(document.getElementById('camera-names').value || '{}');
                
                let addedCount = 0;
                data.logs.forEach(log => {
                    const row = createLogRow(log, showSourceColumn, cameraNames);
                    tbody.appendChild(row);
                    addedCount++;
                });
                
                document.getElementById('last-log-id').value = data.new_last_id;
                
                if (searchTerm) {
                    filterLogsBySearch();
                } else {
                    const newTotal = currentRowCount + addedCount;
                    statusDiv.textContent = `Showing ${newTotal.toLocaleString()} logs (+${addedCount.toLocaleString()} new)`;
                }
                
                document.getElementById('new-logs-count').textContent = data.count;
                badge.style.display = 'inline-block';
                
                setTimeout(() => {
                    badge.style.display = 'none';
                }, 3000);
            } else {
                const allRows = tbody.querySelectorAll('.log-row');
                const visibleRows = Array.from(allRows).filter(row => row.style.display !== 'none');
                
                if (visibleRows.length !== allRows.length) {
                    statusDiv.textContent = `Showing ${visibleRows.length.toLocaleString()} of ${allRows.length.toLocaleString()} logs (no new logs)`;
                } else {
                    statusDiv.textContent = `Showing ${allRows.length.toLocaleString()} logs (no new logs)`;
                }
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
        button.disabled = false;
        button.textContent = 'Get Newer Logs';
    });
}

/**
 * Create a table row element for a log entry
 */
function createLogRow(log, showSourceColumn, cameraNames) {
    const row = document.createElement('tr');
    row.className = `log-row log-${log.level.toLowerCase()}`;
    row.setAttribute('data-log-id', log.id);
    
    const idCell = document.createElement('td');
    idCell.className = 'log-id';
    idCell.textContent = log.id;
    row.appendChild(idCell);
    
    if (showSourceColumn) {
        const sourceCell = document.createElement('td');
        sourceCell.className = 'log-source';
        // Use camera name if available, otherwise fall back to source ID
        sourceCell.textContent = cameraNames[log.source] || log.source;
        row.appendChild(sourceCell);
    }
    
    const timestampCell = document.createElement('td');
    timestampCell.className = 'log-timestamp';
    const ts = formatLogTimestamp(log.timestamp);
    const dateSpan = document.createElement('span');
    dateSpan.className = 'ts-date';
    dateSpan.textContent = ts.date;
    const timeSpan = document.createElement('span');
    timeSpan.className = 'ts-time';
    timeSpan.textContent = ts.time;
    timestampCell.appendChild(dateSpan);
    timestampCell.appendChild(document.createTextNode(' '));
    timestampCell.appendChild(timeSpan);
    row.appendChild(timestampCell);
    
    const levelCell = document.createElement('td');
    levelCell.className = 'log-level';
    const levelBadge = document.createElement('span');
    levelBadge.className = `level-badge level-${log.level.toLowerCase()}`;
    levelBadge.textContent = log.level;
    levelCell.appendChild(levelBadge);
    row.appendChild(levelCell);
    
    const messageCell = document.createElement('td');
    messageCell.className = 'log-message';
    messageCell.textContent = log.message;
    row.appendChild(messageCell);
    
    return row;
}

/**
 * Format log timestamp for display - returns object with date and time parts
 */
function formatLogTimestamp(timestamp) {
    const date = new Date(timestamp);
    
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const day = date.getDate();
    const year = date.getFullYear();
    
    let hours = date.getHours();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return {
        date: `${month} ${day}, ${year}`,
        time: `${hours}:${minutes}:${seconds} ${ampm}`
    };
}

/**
 * Set date preset values
 */
function setPreset(preset) {
    const dateFrom = document.getElementById('date_from');
    const dateTo = document.getElementById('date_to');
    const timeFrom = document.getElementById('time_from');
    const timeTo = document.getElementById('time_to');
    
    const today = new Date();
    const formatDate = (d) => d.toISOString().split('T')[0];
    
    switch (preset) {
        case 'today':
            dateFrom.value = formatDate(today);
            dateTo.value = formatDate(today);
            timeFrom.value = '0';
            timeTo.value = '23';
            break;
        case 'yesterday':
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            dateFrom.value = formatDate(yesterday);
            dateTo.value = formatDate(yesterday);
            timeFrom.value = '0';
            timeTo.value = '23';
            break;
        case 'last7':
            const last7 = new Date(today);
            last7.setDate(last7.getDate() - 6);
            dateFrom.value = formatDate(last7);
            dateTo.value = formatDate(today);
            timeFrom.value = '0';
            timeTo.value = '23';
            break;
        case 'last30':
            const last30 = new Date(today);
            last30.setDate(last30.getDate() - 29);
            dateFrom.value = formatDate(last30);
            dateTo.value = formatDate(today);
            timeFrom.value = '0';
            timeTo.value = '23';
            break;
    }
}
</script>

<?php
include 'includes/footer.php';
?>