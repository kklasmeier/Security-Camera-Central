<?php
/**
 * Database Class - MariaDB Version
 * Centralized database for multi-camera security system
 * Maintains backward compatibility with SQLite version method signatures
 */

require_once __DIR__ . '/config.php';

class Database {
    private $pdo;
    private $host;
    private $database;
    private $username;
    private $password;
    private $port;
    
    public function __construct() {
        $this->host = DB_HOST;
        $this->database = DB_NAME;
        $this->username = DB_USER;
        $this->password = DB_PASS;
        $this->port = DB_PORT;
        
        $this->connect();
    }
    
    /**
     * Connect to MariaDB database
     */
    private function connect() {
        try {
            $dsn = "mysql:host={$this->host};port={$this->port};dbname={$this->database};charset=utf8mb4";
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ];
            
            $this->pdo = new PDO($dsn, $this->username, $this->password, $options);
        } catch (PDOException $e) {
            error_log("Database connection error: " . $e->getMessage());
            $this->pdo = null;
        }
    }
    
    /**
     * Check if database is connected
     * @return bool
     */
    public function isConnected() {
        return $this->pdo !== null;
    }
    
    // ========================================
    // EVENTS METHODS
    // ========================================
    
    /**
     * Get recent events with pagination and optional camera filtering
     * @param int $limit Number of events to return
     * @param int $offset Starting position
     * @param string|null $camera_id Optional camera filter (e.g., 'camera_1' or 'all' or null)
     * @return array Array of event records
     */
    public function get_recent_events($limit = 12, $offset = 0, $camera_id = null) {
        if (!$this->isConnected()) return [];
        
        try {
            $sql = "SELECT * FROM events";
            
            // Add camera filter if specified
            if ($camera_id !== null && $camera_id !== 'all') {
                $sql .= " WHERE camera_id = :camera_id";
            }
            
            $sql .= " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset";
            
            $stmt = $this->pdo->prepare($sql);
            
            if ($camera_id !== null && $camera_id !== 'all') {
                $stmt->bindValue(':camera_id', $camera_id, PDO::PARAM_STR);
            }
            
            $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
            $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            error_log("Error fetching recent events: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get single event by ID
     * @param int $id Event ID
     * @return array|null Event record or null if not found
     */
    public function get_event_by_id($id) {
        if (!$this->isConnected()) return null;
        
        try {
            $stmt = $this->pdo->prepare("
                SELECT * FROM events 
                WHERE id = :id
            ");
            $stmt->bindValue(':id', $id, PDO::PARAM_INT);
            $stmt->execute();
            
            $result = $stmt->fetch();
            return $result !== false ? $result : null;
        } catch (PDOException $e) {
            error_log("Error fetching event by ID: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Get total count of events with optional camera filtering
     * @param string|null $camera_id Optional camera filter (e.g., 'camera_1' or 'all' or null)
     * @return int Total number of events
     */
    public function get_event_count($camera_id = null) {
        if (!$this->isConnected()) return 0;
        
        try {
            $sql = "SELECT COUNT(*) as count FROM events";
            
            // Add camera filter if specified
            if ($camera_id !== null && $camera_id !== 'all') {
                $sql .= " WHERE camera_id = :camera_id";
            }
            
            $stmt = $this->pdo->prepare($sql);
            
            if ($camera_id !== null && $camera_id !== 'all') {
                $stmt->bindValue(':camera_id', $camera_id, PDO::PARAM_STR);
            }
            
            $stmt->execute();
            $result = $stmt->fetch();
            return (int)$result['count'];
        } catch (PDOException $e) {
            error_log("Error getting event count: " . $e->getMessage());
            return 0;
        }
    }
    
    /**
     * Get next event ID (for navigation)
     * @param int $current_id Current event ID
     * @return int|null Next event ID or null if none
     */
    public function get_next_event_id($current_id) {
        if (!$this->isConnected()) return null;
        
        try {
            $stmt = $this->pdo->prepare("
                SELECT id FROM events 
                WHERE id > :current_id 
                ORDER BY id ASC 
                LIMIT 1
            ");
            $stmt->bindValue(':current_id', $current_id, PDO::PARAM_INT);
            $stmt->execute();
            
            $result = $stmt->fetch();
            return $result ? (int)$result['id'] : null;
        } catch (PDOException $e) {
            error_log("Error getting next event ID: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Get previous event ID (for navigation)
     * @param int $current_id Current event ID
     * @return int|null Previous event ID or null if none
     */
    public function get_previous_event_id($current_id) {
        if (!$this->isConnected()) return null;
        
        try {
            $stmt = $this->pdo->prepare("
                SELECT id FROM events 
                WHERE id < :current_id 
                ORDER BY id DESC 
                LIMIT 1
            ");
            $stmt->bindValue(':current_id', $current_id, PDO::PARAM_INT);
            $stmt->execute();
            
            $result = $stmt->fetch();
            return $result ? (int)$result['id'] : null;
        } catch (PDOException $e) {
            error_log("Error getting previous event ID: " . $e->getMessage());
            return null;
        }
    }
    
    // ========================================
    // LOGS METHODS
    // ========================================
    
    /**
     * Get the most recent logs with optional filtering
     * Uses subquery to get last N logs, then orders them ASC for terminal-style display
     * 
     * @param int $limit Number of logs to return
     * @param array|null $level_filter Array of log levels to filter (e.g., ['INFO', 'WARNING'])
     * @param string|null $source_filter Optional source/camera filter (e.g., 'camera_1' or 'all')
     * @return array Array of log records ordered by id ASC (oldest to newest)
     */
    public function get_logs($limit = 1000, $level_filter = null, $source_filter = null) {
        if (!$this->isConnected()) return [];
        
        try {
            // Build WHERE clause for filters
            $where_conditions = [];
            $where_sql = "";
            
            // Handle array of level filters
            if ($level_filter && is_array($level_filter) && !empty($level_filter)) {
                $placeholders = [];
                foreach ($level_filter as $index => $level) {
                    $placeholders[] = ":level{$index}";
                }
                $where_conditions[] = "level IN (" . implode(',', $placeholders) . ")";
            }
            
            // Handle source filter (camera_id)
            if ($source_filter !== null && $source_filter !== 'all') {
                $where_conditions[] = "source = :source";
            }
            
            if (!empty($where_conditions)) {
                $where_sql = "WHERE " . implode(' AND ', $where_conditions);
            }
            
            // Subquery approach: Get most recent N logs (DESC), then flip to ASC
            $sql = "SELECT * FROM (
                        SELECT * FROM logs 
                        {$where_sql}
                        ORDER BY id DESC 
                        LIMIT :limit
                    ) AS recent_logs
                    ORDER BY id ASC";
            
            $stmt = $this->pdo->prepare($sql);
            
            // Bind level filter values
            if ($level_filter && is_array($level_filter) && !empty($level_filter)) {
                foreach ($level_filter as $index => $level) {
                    $stmt->bindValue(":level{$index}", $level, PDO::PARAM_STR);
                }
            }
            
            // Bind source filter
            if ($source_filter !== null && $source_filter !== 'all') {
                $stmt->bindValue(':source', $source_filter, PDO::PARAM_STR);
            }
            
            $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            error_log("Error fetching logs: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get count of logs with optional filtering
     * @param array|null $level_filter Array of log levels to filter
     * @param string|null $source_filter Optional source/camera filter
     * @return int Total number of logs
     */
    public function get_log_count($level_filter = null, $source_filter = null) {
        if (!$this->isConnected()) return 0;
        
        try {
            $sql = "SELECT COUNT(*) as count FROM logs WHERE 1=1";
            
            // Handle array of level filters
            if ($level_filter && is_array($level_filter) && !empty($level_filter)) {
                $placeholders = [];
                foreach ($level_filter as $index => $level) {
                    $placeholders[] = ":level{$index}";
                }
                $sql .= " AND level IN (" . implode(',', $placeholders) . ")";
            }
            
            // Handle source filter
            if ($source_filter !== null && $source_filter !== 'all') {
                $sql .= " AND source = :source";
            }
            
            $stmt = $this->pdo->prepare($sql);
            
            // Bind level filter values
            if ($level_filter && is_array($level_filter) && !empty($level_filter)) {
                foreach ($level_filter as $index => $level) {
                    $stmt->bindValue(":level{$index}", $level, PDO::PARAM_STR);
                }
            }
            
            // Bind source filter
            if ($source_filter !== null && $source_filter !== 'all') {
                $stmt->bindValue(':source', $source_filter, PDO::PARAM_STR);
            }
            
            $stmt->execute();
            $result = $stmt->fetch();
            return (int)$result['count'];
        } catch (PDOException $e) {
            error_log("Error getting log count: " . $e->getMessage());
            return 0;
        }
    }
    
    /**
     * Get logs after a specific log ID (for "Get Newer Logs" functionality)
     * Returns logs in ASC order (oldest to newest) to append to bottom of display
     * 
     * @param int $last_log_id The ID of the most recent log currently displayed
     * @param int $limit Number of logs to return (default 1000)
     * @param array|null $level_filter Array of log levels to filter
     * @param string|null $source_filter Optional source/camera filter
     * @return array Array of log records ordered by id ASC
     */
    public function get_logs_after($last_log_id, $limit = 1000, $level_filter = null, $source_filter = null) {
        if (!$this->isConnected()) return [];
        
        try {
            $sql = "SELECT * FROM logs WHERE id > :last_log_id";
            
            // Handle array of level filters
            if ($level_filter && is_array($level_filter) && !empty($level_filter)) {
                $placeholders = [];
                foreach ($level_filter as $index => $level) {
                    $placeholders[] = ":level{$index}";
                }
                $sql .= " AND level IN (" . implode(',', $placeholders) . ")";
            }
            
            // Handle source filter
            if ($source_filter !== null && $source_filter !== 'all') {
                $sql .= " AND source = :source";
            }
            
            $sql .= " ORDER BY id ASC LIMIT :limit";
            
            $stmt = $this->pdo->prepare($sql);
            $stmt->bindValue(':last_log_id', $last_log_id, PDO::PARAM_INT);
            
            // Bind level filter values
            if ($level_filter && is_array($level_filter) && !empty($level_filter)) {
                foreach ($level_filter as $index => $level) {
                    $stmt->bindValue(":level{$index}", $level, PDO::PARAM_STR);
                }
            }
            
            // Bind source filter
            if ($source_filter !== null && $source_filter !== 'all') {
                $stmt->bindValue(':source', $source_filter, PDO::PARAM_STR);
            }
            
            $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            error_log("Error fetching logs after ID: " . $e->getMessage());
            return [];
        }
    }
    
    // ========================================
    // CAMERA METHODS (NEW)
    // ========================================
    
    /**
     * Get all registered cameras
     * @return array Array of camera records
     */
    public function get_all_cameras() {
        if (!$this->isConnected()) return [];
        
        try {
            $stmt = $this->pdo->query("
                SELECT id, camera_id, name, location, ip_address, status, last_seen
                FROM cameras 
                ORDER BY camera_id ASC
            ");
            
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            error_log("Error fetching cameras: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get single camera by camera_id
     * @param string $camera_id Camera identifier (e.g., 'camera_1')
     * @return array|null Camera record or null if not found
     */
    public function get_camera_by_id($camera_id) {
        if (!$this->isConnected()) return null;
        
        try {
            $stmt = $this->pdo->prepare("
                SELECT id, camera_id, name, location, ip_address, status, last_seen
                FROM cameras 
                WHERE camera_id = :camera_id
            ");
            $stmt->bindValue(':camera_id', $camera_id, PDO::PARAM_STR);
            $stmt->execute();
            
            $result = $stmt->fetch();
            return $result !== false ? $result : null;
        } catch (PDOException $e) {
            error_log("Error fetching camera by ID: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Get friendly name for a camera
     * @param string $camera_id Camera identifier (e.g., 'camera_1')
     * @return string Camera name or camera_id if not found
     */
    public function get_camera_name($camera_id) {
        if (!$this->isConnected()) return $camera_id;
        
        $camera = $this->get_camera_by_id($camera_id);
        
        if ($camera && !empty($camera['name'])) {
            return $camera['name'];
        }
        
        return $camera_id;
    }
    
    // ========================================
    // SYSTEM CONTROL METHODS
    // ========================================
    
    /**
     * Get streaming flag status (placeholder for Session 10)
     * @param string|null $camera_id Optional camera identifier
     * @return int 0 (streaming disabled)
     */
    public function get_streaming_flag($camera_id = null) {
        // Placeholder implementation
        // Will be fully implemented in Session 10 when streaming control is added
        return 0;
    }
    
    /**
     * Set streaming flag status (placeholder for Session 10)
     * @param int $value 0 or 1
     * @param string|null $camera_id Optional camera identifier
     * @return bool Success status
     */
    public function set_streaming_flag($value, $camera_id = null) {
        // Placeholder implementation
        // Will be fully implemented in Session 10 when streaming control is added
        return true;
    }
}
?>