# Database Schema - Security Camera System

MariaDB database schema for multi-camera security system with centralized event storage.

## Overview

This database supports **4+ cameras** sending motion detection events to a central server. The schema tracks:
- Camera registration and status
- Motion events with multiple image/video files
- File transfer progress from cameras to server
- MP4 conversion status
- Centralized logging from all components
- AI analysis results (Phase 2)

---

## Database Structure

### Tables

1. **cameras** - Camera registration and metadata
2. **events** - Motion detection events with file tracking
3. **logs** - Centralized logging from all components

### Key Features

- **Multi-camera support** via `camera_id` foreign key
- **Progressive file updates** with transfer status flags
- **MP4 conversion tracking** for background worker
- **Future-ready AI columns** (Phase 2)
- **Microsecond timestamp precision** for high-frequency events
- **Optimized indexes** for common query patterns

---

## Prerequisites

- **MariaDB 10.5+** installed and running
- Root access to MariaDB
- Bash shell for running setup script

**Check MariaDB status:**
```bash
sudo systemctl status mariadb
```

**If not running:**
```bash
sudo systemctl start mariadb
sudo systemctl enable mariadb  # Start on boot
```

---

## Installation

### Quick Setup (Recommended)

```bash
cd /home/pi/Security-Camera-Central/database

# Make setup script executable
chmod +x setup_database.sh

# Run the setup script
sudo ./setup_database.sh
```

The script will:
1. Prompt for MariaDB root password
2. Prompt for new `securitycam` user password
3. Create database and tables
4. Create database user with appropriate privileges
5. Save credentials to `../.env` file
6. Verify installation

### Manual Setup

If you prefer manual setup:

```bash
# Login to MariaDB as root
sudo mysql -u root -p

# Create user (replace PASSWORD with your choice)
CREATE USER 'securitycam'@'localhost' IDENTIFIED BY 'PASSWORD';
GRANT ALL PRIVILEGES ON security_cameras.* TO 'securitycam'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Run schema creation
mysql -u root -p < schema.sql
```

---

## Testing

After installation, run the test script to verify everything works:

```bash
mysql -u securitycam -p security_cameras < test_database.sql
```

**Expected output:**
- ✓ All 3 tables created
- ✓ All indexes exist
- ✓ Test data inserts/updates work
- ✓ Foreign key constraints enforced
- ✓ Query indexes used correctly
- ⚠️ TEST 9 should show an error (foreign key rejection) - this is correct!

---

## Connection Information

### For Python (FastAPI, Workers)

**SQLAlchemy:**
```python
from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://securitycam:PASSWORD@localhost/security_cameras"
engine = create_engine(DATABASE_URL)
```

**Direct MySQL:**
```python
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="securitycam",
    password="PASSWORD",
    database="security_cameras"
)
```

### For PHP (Web UI)

**PDO:**
```php
$pdo = new PDO(
    'mysql:host=localhost;dbname=security_cameras;charset=utf8mb4',
    'securitycam',
    'PASSWORD'
);
```

### Connection Details

- **Host:** localhost
- **Port:** 3306 (default)
- **Database:** security_cameras
- **User:** securitycam
- **Password:** (set during installation)

---

## Schema Details

### Table: cameras

Tracks registered cameras in the system.

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Auto-increment primary key |
| camera_id | VARCHAR(50) | User-defined identifier (e.g., "camera_1") |
| name | VARCHAR(100) | Human-readable name (e.g., "Front Door") |
| location | VARCHAR(200) | Physical location |
| ip_address | VARCHAR(45) | IP for MJPEG streaming |
| last_seen | DATETIME(6) | Last heartbeat (Phase 2) |
| status | VARCHAR(20) | online, offline, error |
| created_at | DATETIME(6) | First registration time |
| updated_at | DATETIME(6) | Last update time |

**Indexes:**
- `camera_id` (unique)
- `status`

---

### Table: events

Stores motion detection events with file tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Event ID (used in filenames) |
| camera_id | VARCHAR(50) | Which camera (FK to cameras) |
| timestamp | DATETIME(6) | When motion detected |
| motion_score | FLOAT | Changed pixel count |
| image_a_path | VARCHAR(500) | Picture A path |
| image_b_path | VARCHAR(500) | Picture B path |
| thumbnail_path | VARCHAR(500) | Thumbnail path |
| video_h264_path | VARCHAR(500) | Raw H.264 video path |
| video_mp4_path | VARCHAR(500) | Converted MP4 path |
| video_duration | FLOAT | Video length (seconds) |
| image_a_transferred | BOOLEAN | File on NFS? |
| image_b_transferred | BOOLEAN | File on NFS? |
| thumbnail_transferred | BOOLEAN | File on NFS? |
| video_transferred | BOOLEAN | File on NFS? |
| mp4_conversion_status | VARCHAR(20) | pending/processing/complete/failed |
| mp4_converted_at | DATETIME(6) | Conversion timestamp |
| ai_processed | BOOLEAN | AI analysis complete? (Phase 2) |
| ai_processed_at | DATETIME(6) | AI processing time (Phase 2) |
| ai_person_detected | BOOLEAN | Person found? (Phase 2) |
| ai_confidence | FLOAT | AI confidence (Phase 2) |
| ai_objects | JSON | Detected objects (Phase 2) |
| ai_description | TEXT | AI description (Phase 2) |
| created_at | DATETIME(6) | Record creation time |

**Indexes:**
- `(camera_id, timestamp DESC)` - Events by camera
- `timestamp DESC` - Recent events
- `mp4_conversion_status` - Conversion queue
- `ai_processed` - AI processing queue
- `ai_person_detected` - Person detection filter

---

### Table: logs

Centralized logging from all system components.

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Auto-increment primary key |
| source | VARCHAR(50) | Log source (camera_1, camera_2, central) |
| timestamp | DATETIME(6) | When logged |
| level | VARCHAR(20) | INFO, WARNING, ERROR |
| message | TEXT | Log content |

**Indexes:**
- `source` - Filter by source
- `timestamp DESC` - Recent logs
- `level` - Filter by severity
- `(source, timestamp DESC)` - Source-specific logs

---

## Common Queries

### Get recent events from all cameras
```sql
SELECT id, camera_id, timestamp, motion_score, 
       image_a_transferred, video_transferred, mp4_conversion_status
FROM events 
ORDER BY timestamp DESC 
LIMIT 25;
```

### Get events from specific camera
```sql
SELECT * FROM events 
WHERE camera_id = 'camera_1' 
ORDER BY timestamp DESC 
LIMIT 25;
```

### Find events needing MP4 conversion
```sql
SELECT id, camera_id, timestamp, video_h264_path, video_duration
FROM events 
WHERE mp4_conversion_status = 'pending' 
  AND video_transferred = TRUE
ORDER BY timestamp ASC;
```

### Get logs from specific camera
```sql
SELECT timestamp, level, message 
FROM logs 
WHERE source = 'camera_1' 
ORDER BY timestamp DESC 
LIMIT 100;
```

### Check camera status
```sql
SELECT camera_id, name, location, ip_address, status, last_seen
FROM cameras 
ORDER BY camera_id;
```

---

## Maintenance

### Backup Database

```bash
# Full backup
mysqldump -u securitycam -p security_cameras > backup_$(date +%Y%m%d).sql

# Backup specific table
mysqldump -u securitycam -p security_cameras events > events_backup.sql
```

### Restore Database

```bash
mysql -u securitycam -p security_cameras < backup_20251027.sql
```

### Clean Old Logs

```sql
-- Delete logs older than 30 days
DELETE FROM logs 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### Clean Old Events

```sql
-- Delete events older than 90 days (adjust as needed)
DELETE FROM events 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

---

## Troubleshooting

### Cannot connect to MariaDB

**Symptom:** Connection refused or timeout

**Solution:**
```bash
# Check if MariaDB is running
sudo systemctl status mariadb

# Start if not running
sudo systemctl start mariadb
```

---

### Access denied for user 'securitycam'

**Symptom:** ERROR 1045 (28000): Access denied

**Solution:**
```bash
# Verify user exists
sudo mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='securitycam';"

# If user missing, re-run setup script
sudo ./setup_database.sh
```

---

### Foreign key constraint fails

**Symptom:** Cannot add or update a child row

**Solution:** Ensure the camera exists in the `cameras` table before inserting events:
```sql
-- Check if camera exists
SELECT * FROM cameras WHERE camera_id = 'camera_1';

-- If not, insert it
INSERT INTO cameras (camera_id, name, status) 
VALUES ('camera_1', 'Camera 1', 'online');
```

---

### Slow queries

**Symptom:** Queries take too long

**Solution:** Check if indexes are being used:
```sql
EXPLAIN SELECT * FROM events WHERE camera_id = 'camera_1' ORDER BY timestamp DESC;
```

Look for "Using index" in the Extra column. If not, indexes may not be created:
```sql
SHOW INDEX FROM events;
```

---

## Next Steps

After database setup is complete:

1. ✅ **Session 1A-1 Complete** - Database schema ready
2. **Session 1A-2** - Set up NFS server for file sharing
3. **Session 1A-3** - Build FastAPI application
4. **Session 1A-4** - Create camera registration endpoint

---

## File Paths Convention

All file paths stored in the database are **relative to `/mnt/security_footage`**:

**Example paths:**
- Image A: `camera_1/pictures/42_20251026_143022_a.jpg`
- Image B: `camera_1/pictures/42_20251026_143022_b.jpg`
- Thumbnail: `camera_1/thumbs/42_20251026_143022_thumb.jpg`
- H.264 Video: `camera_1/videos/42_20251026_143022_video.h264`
- MP4 Video: `camera_1/videos/42_20251026_143022_video.mp4`

**Full path on filesystem:** `/mnt/security_footage/camera_1/pictures/42_20251026_143022_a.jpg`

---

## Security Notes

- Database user `securitycam` has privileges **only** on `security_cameras` database
- Password stored in `.env` file with 600 permissions (owner read/write only)
- MariaDB configured to listen on localhost only (default)
- For local network deployment only - additional hardening needed for internet exposure

---

**Session:** 1A-1  
**Status:** Complete  
**Next Session:** 1A-2 (NFS Server Setup)