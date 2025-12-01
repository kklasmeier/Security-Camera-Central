<?php
/**
 * AJAX endpoint for fetching newer logs
 * Save this as: ajax/get_newer_logs.php
 */

require_once '../includes/session.php';
require_once '../includes/db.php';

header('Content-Type: application/json');

// Get parameters from POST
$last_log_id = isset($_POST['last_log_id']) ? (int)$_POST['last_log_id'] : 0;
$filter_info = isset($_POST['filter_info']) ? (int)$_POST['filter_info'] : 0;
$filter_warning = isset($_POST['filter_warning']) ? (int)$_POST['filter_warning'] : 0;
$filter_error = isset($_POST['filter_error']) ? (int)$_POST['filter_error'] : 0;
$source_filter = isset($_POST['source_filter']) ? $_POST['source_filter'] : null;
$result_limit = isset($_POST['result_limit']) ? (int)$_POST['result_limit'] : 1000;

// Convert empty string to null for source_filter
if ($source_filter === '' || $source_filter === 'all') {
    $source_filter = null;
}

// Validate result limit
$valid_limits = get_valid_log_limits();
if (!in_array($result_limit, $valid_limits)) {
    $result_limit = 1000;
}

// Build level filter array
$level_filter = [];
if ($filter_info) $level_filter[] = 'INFO';
if ($filter_warning) $level_filter[] = 'WARNING';
if ($filter_error) $level_filter[] = 'ERROR';

// Validate we have at least one filter
if (empty($level_filter)) {
    echo json_encode([
        'success' => false,
        'error' => 'No log levels selected'
    ]);
    exit;
}

// Validate last_log_id
if ($last_log_id <= 0) {
    echo json_encode([
        'success' => false,
        'error' => 'Invalid last log ID'
    ]);
    exit;
}

// Get newer logs (no end_datetime constraint - get all new logs)
$db = new Database();
$logs = $db->get_logs_after($last_log_id, $result_limit, $level_filter, $source_filter, null);

// Return response
echo json_encode([
    'success' => true,
    'logs' => $logs,
    'count' => count($logs),
    'new_last_id' => !empty($logs) ? $logs[count($logs) - 1]['id'] : $last_log_id
]);
?>