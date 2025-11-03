<?php
/**
 * Debug script to check .env file loading
 */

echo "=== .env Debug Script ===\n\n";

// Check if .env file exists
$env_paths = [
    __DIR__ . '/../.env',
    __DIR__ . '/.env',
    '/home/pi/Security-Camera-Central/.env'
];

echo "Checking for .env file:\n";
foreach ($env_paths as $path) {
    echo "  - $path ... ";
    if (file_exists($path)) {
        echo "✓ EXISTS\n";
        echo "    File is readable: " . (is_readable($path) ? "YES" : "NO") . "\n";
        
        // Show first few lines (without passwords)
        echo "    Contents preview:\n";
        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        $preview_lines = array_slice($lines, 0, 5);
        foreach ($preview_lines as $line) {
            // Mask passwords
            if (strpos($line, 'PASSWORD') !== false || strpos($line, 'SECRET') !== false) {
                list($key, $val) = explode('=', $line, 2);
                echo "      $key=***MASKED***\n";
            } else {
                echo "      $line\n";
            }
        }
        echo "\n";
    } else {
        echo "✗ NOT FOUND\n";
    }
}

echo "\n=== Testing .env parsing ===\n";

// Try to load from parent directory
$env_file = __DIR__ . '/../.env';
if (file_exists($env_file)) {
    echo "Loading from: $env_file\n\n";
    
    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if (empty($line) || strpos($line, '#') === 0) {
            continue;
        }
        
        if (strpos($line, '=') !== false) {
            list($key, $value) = explode('=', $line, 2);
            $key = trim($key);
            $value = trim($value);
            
            // Remove surrounding quotes if present
            if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') ||
                (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
                $value = substr($value, 1, -1);
            }
            
            // Store in $_ENV
            $_ENV[$key] = $value;
            
            // Show what we parsed (mask sensitive values)
            if (strpos($key, 'PASSWORD') !== false || strpos($key, 'SECRET') !== false) {
                echo "  Parsed: $key = ***MASKED*** (length: " . strlen($value) . ")\n";
            } else {
                echo "  Parsed: $key = $value\n";
            }
        }
    }
}

echo "\n=== Checking \$_ENV contents ===\n";
$db_keys = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'];
foreach ($db_keys as $key) {
    echo "  \$_ENV['$key'] = ";
    if (isset($_ENV[$key])) {
        if (strpos($key, 'PASSWORD') !== false) {
            $len = strlen($_ENV[$key]);
            echo "***MASKED*** (length: $len)\n";
        } else {
            $val = $_ENV[$key];
            echo "$val\n";
        }
    } else {
        echo "NOT SET\n";
    }
}

echo "\n=== Test database connection ===\n";
if (!empty($_ENV['DB_PASSWORD'])) {
    echo "DB_PASSWORD is set, attempting connection...\n";
    try {
        $host = $_ENV['DB_HOST'];
        $port = $_ENV['DB_PORT'];
        $dbname = $_ENV['DB_NAME'];
        $user = $_ENV['DB_USER'];
        $pass = $_ENV['DB_PASSWORD'];
        
        $dsn = "mysql:host=$host;port=$port;dbname=$dbname;charset=utf8mb4";
        $pdo = new PDO($dsn, $user, $pass);
        echo "✓ Connection successful!\n";
    } catch (PDOException $e) {
        echo "✗ Connection failed: " . $e->getMessage() . "\n";
    }
} else {
    echo "✗ DB_PASSWORD not set, cannot test connection\n";
}

?>