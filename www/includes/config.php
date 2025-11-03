<?php
/**
 * Configuration File
 * Loads settings from .env file in parent directory
 * Used by database class and helper functions
 */

// Load environment variables from ../.env
function load_env($file_path) {
    if (!file_exists($file_path)) {
        error_log("WARNING: .env file not found at: $file_path");
        return false;
    }
    
    $lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        // Skip comments and empty lines
        $line = trim($line);
        if (empty($line) || strpos($line, '#') === 0) {
            continue;
        }
        
        // Parse KEY=VALUE
        if (strpos($line, '=') !== false) {
            list($key, $value) = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);
            
            // Remove surrounding quotes if present
            if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') ||
                (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
                $value = substr($value, 1, -1);
            }
            
            // Store in $_ENV and putenv
            $_ENV[$key] = $value;
            putenv("$key=$value");
        }
    }
    
    return true;
}

// Try to load from Security-Camera-Central/.env (two levels up from includes/)
$env_file = __DIR__ . '/../../.env';
if (!load_env($env_file)) {
    // Fallback: try www/.env (one level up)
    $env_file = __DIR__ . '/../.env';
    if (!load_env($env_file)) {
        // Last fallback: try includes/.env (same directory)
        $env_file = __DIR__ . '/.env';
        if (!load_env($env_file)) {
            error_log("CRITICAL: Could not load .env file from any location");
        }
    }
}

// Database Configuration
define('DB_HOST', !empty($_ENV['DB_HOST']) ? $_ENV['DB_HOST'] : 'localhost');
define('DB_PORT', !empty($_ENV['DB_PORT']) ? $_ENV['DB_PORT'] : '3306');
define('DB_NAME', !empty($_ENV['DB_NAME']) ? $_ENV['DB_NAME'] : 'security_cameras');
define('DB_USER', !empty($_ENV['DB_USER']) ? $_ENV['DB_USER'] : 'securitycam');
define('DB_PASS', !empty($_ENV['DB_PASSWORD']) ? $_ENV['DB_PASSWORD'] : '');

// Media Storage Configuration
define('MEDIA_ROOT', '/mnt/sdcard/security_camera/security_footage/');
define('MEDIA_URL_PREFIX', '/footage/');

// Validate critical settings
if (empty(DB_PASS)) {
    error_log("CRITICAL: DB_PASSWORD not set in .env file");
}

?>