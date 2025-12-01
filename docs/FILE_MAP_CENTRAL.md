# Security Camera Central Server - File Map

## Directory Structure
```
Security-Camera-Central/
├── API Layer (FastAPI Python)
│   ├── api/
│   │   ├── __init__.py              Module initialization
│   │   ├── main.py                  [ENTRY] FastAPI app, CORS, routers
│   │   ├── config.py                Configuration from env vars
│   │   ├── database.py              SQLAlchemy engine, session factory
│   │   ├── models.py                ORM models (Camera, Event, Log)
│   │   ├── schemas.py               Pydantic validation schemas
│   │   └── routes/
│   │       ├── __init__.py          Route module initialization
│   │       ├── health.py            GET /health
│   │       ├── cameras.py           POST /cameras/register, GET /cameras
│   │       ├── events.py            POST /events, GET /events, PATCH /events/{id}
│   │       ├── logs.py              POST /logs, GET /logs
│   │       └── stats.py             GET /stats/* (system statistics)
│   │
│   ├── Background Processing Workers
│   │   └── scripts/
│   │       ├── ai_event_processor.py    [WORKER] Ollama AI analysis
│   │       ├── convert_pending_mp4.py   [WORKER] H.264 → MP4 conversion
│   │       ├── optimize_mp4.py          [WORKER] MP4 file optimization
│   │       ├── jobctl.sh                Worker management script
│   │       ├── requirements.txt         AI worker dependencies
│   │       └── AI_NOTES.md              AI processing notes
│   │
│   ├── Database Schema & Migrations
│   │   └── database/
│   │       ├── schema.sql                       Initial schema (cameras, events, logs)
│   │       ├── setup_database.sh                Database initialization
│   │       ├── test_database.sql                Test queries
│   │       ├── 001_add_status_to_events.sql     Migration: event status
│   │       ├── 002_add_claim_tracking_to_events.sql  Migration: AI claiming
│   │       ├── 003_add_ai_fields.sql            Migration: AI results
│   │       ├── 004_add_confidence_score.sql     Migration: confidence field
│   │       └── migration_fix_mp4_status.sql     Fix: MP4 status cleanup
│   │
│   ├── NFS Storage Management
│   │   └── camera_nfs_mounts/
│   │       ├── setup_nfs.sh             NFS server initial setup
│   │       ├── add_camera.sh            Add camera to NFS exports
│   │       ├── verify_nfs.sh            Verify NFS configuration
│   │       ├── test_nfs_mount.sh        Test NFS mount operations
│   │       └── README.md                NFS documentation (19.3KB)
│   │
│   ├── Web Interface (PHP + Nginx)
│   │   └── www/
│   │       ├── Pages
│   │       │   ├── index.php            Main event gallery
│   │       │   ├── event.php            Event detail view
│   │       │   ├── live.php             Live camera streaming
│   │       │   └── logs.php             Centralized log viewer
│   │       │
│   │       ├── Includes (Shared Components)
│   │       │   ├── config.php           PHP configuration
│   │       │   ├── db.php               Database helpers (17.5KB)
│   │       │   ├── functions.php        Shared functions (13.5KB)
│   │       │   ├── session.php          Session management (5.7KB)
│   │       │   ├── camera_selector.php  Camera dropdown
│   │       │   ├── camera_status.php    Status indicators (5.4KB)
│   │       │   ├── header.php           Page header
│   │       │   ├── footer.php           Page footer
│   │       │   ├── debug_env.php        Debug helpers
│   │       │   └── test_db.php          DB test page
│   │       │
│   │       ├── API Endpoints (PHP)
│   │       │   └── api/
│   │       │       ├── get_new_logs.php         Log polling
│   │       │       ├── refresh_camera_status.php Camera status updates
│   │       │       └── set_streaming.php        Stream control (3.3KB)
│   │       │
│   │       ├── AJAX Endpoints
│   │       │   └── ajax/
│   │       │       └── get_newer_logs.php       Live log updates
│   │       │
│   │       └── Assets
│   │           └── assets/
│   │               ├── style.css            Main stylesheet (53.7KB)
│   │               ├── script.js            JavaScript (28.5KB)
│   │               ├── camera-logo.png      Logo images
│   │               ├── camera-logo-small.png
│   │               ├── camera.jpg           Background image
│   │               └── favicon.*            Favicon files
│   │
│   ├── Health Monitoring & Diagnostics
│   │   ├── health_checker.py            [MONITOR] Comprehensive health checks
│   │   ├── camera_health_check.py       [MONITOR] Camera API checks
│   │   ├── thread_monitor.py            [MONITOR] Worker thread monitoring
│   │   └── emergency_diagnostic.py      [DEBUG] Emergency diagnostics
│   │
│   ├── Testing
│   │   └── tests/
│   │       ├── test_api.py                      Basic API tests
│   │       ├── test_camera_registration.py      Camera registration flow
│   │       ├── test_event_creation.py           Event creation tests
│   │       ├── test_event_queries.py            Query pagination/filtering (26.9KB)
│   │       ├── test_file_updates.py             File transfer tests
│   │       ├── test_log_ingestion.py            Log ingestion tests
│   │       ├── test_logs_cameras_query.py       Log query tests (22.1KB)
│   │       └── manual_test.sh                   Manual testing script
│   │
│   ├── Service Management
│   │   ├── central_server_controller.sh  Systemd service controller
│   │   ├── run_api.sh                    API server launcher
│   │   ├── gitsync.sh                    Git sync utility
│   │   └── killpython.sh                 Emergency cleanup
│   │
│   ├── Development Tools
│   │   ├── check_db.py                   [CLEANUP?] Quick DB check
│   │   └── project_inventory.py          Inventory generator
│   │
│   ├── Documentation
│   │   ├── README.md                     Project overview
│   │   ├── AI_INSTRUCTIONS.md            AI context & workflow
│   │   ├── PROJECT_CENTRAL.md            [NEW] Project docs
│   │   └── FILE_MAP_CENTRAL.md           [NEW] This file
│   │
│   └── Configuration & Dependencies
│       ├── requirements.txt              Python dependencies
│       └── .gitignore                    Git ignore rules
```

## Component Interaction Map

```
┌──────────────────────────────────────────────────────────────────────┐
│                     CAMERA AGENTS (5x Pi Zero 2W)                    │
│  Motion Detection → Event Creation → File Transfer → Status Updates  │
└────────────────┬─────────────────────────────────────────────────────┘
                 │
                 │ REST API (HTTP)
                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│              CENTRAL SERVER (Pi 4) - api/main.py                     │
│                      FastAPI on port 8000                             │
└─────┬────────────────────────────────────────────────────────────────┘
      │
      ├──> api/routes/cameras.py
      │    └─ POST /api/v1/cameras/register
      │       └─> database.py → models.Camera → MariaDB
      │
      ├──> api/routes/events.py
      │    ├─ POST /api/v1/events
      │    │  └─> models.Event → MariaDB (status='processing')
      │    ├─ PATCH /api/v1/events/{id}/files
      │    │  └─> Update transfer flags in MariaDB
      │    └─ PATCH /api/v1/events/{id}/status
      │       └─> Update status (complete/interrupted/failed)
      │
      ├──> api/routes/logs.py
      │    ├─ POST /api/v1/logs (batch insert)
      │    │  └─> models.Log → MariaDB
      │    └─ GET /api/v1/logs (query with filters)
      │
      └──> api/routes/health.py
           └─ GET /api/v1/health
              └─> database.check_database_connection()

┌──────────────────────────────────────────────────────────────────────┐
│                    NFS SHARED STORAGE                                │
│          /mnt/security_footage/ (exported to cameras)                │
│  camera_1/pictures/  camera_1/videos/  camera_1/thumbs/             │
│  camera_2/pictures/  camera_2/videos/  camera_2/thumbs/             │
└────────┬─────────────────────────────────────────────────────────────┘
         │
         │ Read/Write Access
         ↓
┌──────────────────────────────────────────────────────────────────────┐
│                  BACKGROUND WORKERS (Python)                         │
└──────────────────────────────────────────────────────────────────────┘

WORKER 1: scripts/convert_pending_mp4.py
  ├─ Poll MariaDB for mp4_conversion_status='pending'
  ├─ Read H.264 from NFS: /mnt/security_footage/camera_X/videos/*.h264
  ├─ FFmpeg: H.264 → MP4
  ├─ Write MP4 to NFS: /mnt/security_footage/camera_X/videos/*.mp4
  └─ Update MariaDB: mp4_conversion_status='complete', mp4_path

WORKER 2: scripts/optimize_mp4.py
  ├─ Poll MariaDB for unoptimized MP4s
  ├─ Read MP4 from NFS
  ├─ FFmpeg: Re-encode with optimization
  ├─ Write optimized MP4 to NFS
  └─ Update MariaDB: video_mp4_path (optimized)

WORKER 3: scripts/ai_event_processor.py
  ├─ Poll MariaDB for ai_processed=false
  ├─ Claim event (set processing flag)
  ├─ Read images from NFS: /mnt/security_footage/camera_X/pictures/*.jpg
  ├─ Send to AI Server (Pi 5):
  │  ├─ Ollama API: moondream (vision analysis)
  │  └─ Ollama API: deepseek-r1 (description generation)
  └─ Update MariaDB: ai_processed=true, ai_description, ai_objects, etc.

┌──────────────────────────────────────────────────────────────────────┐
│                 AI SERVER (Pi 5 - 16GB RAM)                          │
│                    Ollama Service                                     │
│  Models: moondream:latest, deepseek-r1:8b                           │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    WEB INTERFACE (PHP + Nginx)                       │
│              www/ served on port 80/443                              │
└──────────────────────────────────────────────────────────────────────┘

  USER BROWSER
    ↓
  www/index.php (event gallery)
    ├─> includes/db.php → MariaDB query events
    ├─> Display thumbnails from NFS
    └─> includes/session.php (camera selection)

  www/event.php?id=123 (event details)
    ├─> includes/db.php → MariaDB get event by ID
    ├─> Display images from NFS
    ├─> Video player (MP4 from NFS)
    └─> Show AI analysis results

  www/live.php (live streaming)
    └─> MJPEG stream from camera agents

  www/logs.php (log viewer)
    └─> includes/db.php → MariaDB query logs
```

## Database Schema Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        CAMERAS TABLE                           │
├────────────────────────────────────────────────────────────────┤
│ id (PK)           INT AUTO_INCREMENT                           │
│ camera_id (UQ)    VARCHAR(50) - indexed                        │
│ name              VARCHAR(100)                                 │
│ location          VARCHAR(200)                                 │
│ ip_address        VARCHAR(45)                                  │
│ status            VARCHAR(20) - 'online'/'offline'             │
│ last_seen         DATETIME                                     │
│ created_at        DATETIME                                     │
│ updated_at        DATETIME                                     │
└──────────┬─────────────────────────────────────────────────────┘
           │ 1:N relationship
           ↓
┌────────────────────────────────────────────────────────────────┐
│                        EVENTS TABLE                            │
├────────────────────────────────────────────────────────────────┤
│ id (PK)                   INT AUTO_INCREMENT                   │
│ camera_id (FK)            VARCHAR(50) → cameras.camera_id      │
│ timestamp                 DATETIME - indexed                   │
│ motion_score              FLOAT                                │
│ confidence_score          FLOAT                                │
│ status                    VARCHAR(20) - processing/complete/...│
│                                                                 │
│ [File Paths - relative to /mnt/security_footage]              │
│ image_a_path              VARCHAR(500)                         │
│ image_b_path              VARCHAR(500)                         │
│ thumbnail_path            VARCHAR(500)                         │
│ video_h264_path           VARCHAR(500)                         │
│ video_mp4_path            VARCHAR(500)                         │
│ video_duration            FLOAT (seconds)                      │
│                                                                 │
│ [Transfer Flags]                                               │
│ image_a_transferred       BOOLEAN                              │
│ image_b_transferred       BOOLEAN                              │
│ thumbnail_transferred     BOOLEAN                              │
│ video_transferred         BOOLEAN                              │
│                                                                 │
│ [MP4 Conversion]                                               │
│ mp4_conversion_status     VARCHAR(20) - pending/complete/...   │
│ mp4_converted_at          DATETIME                             │
│                                                                 │
│ [AI Analysis - Phase 2]                                        │
│ ai_processed              BOOLEAN                              │
│ ai_processed_at           DATETIME                             │
│ ai_person_detected        BOOLEAN                              │
│ ai_confidence             FLOAT                                │
│ ai_objects                TEXT (JSON)                          │
│ ai_description            TEXT                                 │
│                                                                 │
│ created_at                DATETIME                             │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                         LOGS TABLE                             │
├────────────────────────────────────────────────────────────────┤
│ id (PK)           INT AUTO_INCREMENT                           │
│ source            VARCHAR(50) - indexed (camera_id or 'central')│
│ timestamp         DATETIME - indexed                           │
│ level             VARCHAR(20) - indexed (INFO/WARNING/ERROR)   │
│ message           TEXT                                         │
└────────────────────────────────────────────────────────────────┘
```

## API Endpoints Reference

```
HEALTH CHECK
  GET    /api/v1/health                    Check API and database health

CAMERA MANAGEMENT
  POST   /api/v1/cameras/register          Register new camera
         Body: {camera_id, name, location, ip_address}
  GET    /api/v1/cameras                   List all cameras
  GET    /api/v1/cameras/{camera_id}       Get camera details

EVENT MANAGEMENT
  POST   /api/v1/events                    Create new event
         Body: {camera_id, timestamp, motion_score, confidence_score}
  GET    /api/v1/events                    List events (paginated)
         Query: limit, offset, camera_id, start_date, end_date
  GET    /api/v1/events/{id}               Get event by ID
  PATCH  /api/v1/events/{id}/status        Update event status
         Body: {status: 'complete'|'interrupted'|'failed'}
  PATCH  /api/v1/events/{id}/files         Update file transfer status
         Body: {file_type, file_path, transferred, video_duration?}

LOG MANAGEMENT
  POST   /api/v1/logs                      Batch insert logs
         Body: [{source, timestamp, level, message}, ...]
  GET    /api/v1/logs                      Query logs (paginated)
         Query: limit, offset, source, level, start_date, end_date

STATISTICS
  GET    /api/v1/stats/*                   Various system statistics
```

## File Naming Conventions

```
Events on NFS (/mnt/security_footage/):
  Pictures:    {camera_id}/pictures/{event_id}_{timestamp}_picA.jpg
               {camera_id}/pictures/{event_id}_{timestamp}_picB.jpg
  Thumbnail:   {camera_id}/thumbs/{event_id}_{timestamp}_thumb.jpg
  Video H264:  {camera_id}/videos/{event_id}_{timestamp}_video.h264
  Video MP4:   {camera_id}/videos/{event_id}_{timestamp}_video.mp4

Examples:
  camera_1/pictures/123_20251126_143022_picA.jpg
  camera_1/pictures/123_20251126_143022_picB.jpg
  camera_1/thumbs/123_20251126_143022_thumb.jpg
  camera_1/videos/123_20251126_143022_video.h264
  camera_1/videos/123_20251126_143022_video.mp4

Logs:
  run_api.log                    FastAPI/Uvicorn logs
  scripts/*.log                  Background worker logs
```

## Configuration Files

```
Environment Variables (.env - not in repo):
  DATABASE_URL=mysql+pymysql://user:pass@localhost/security_cameras
  API_HOST=0.0.0.0
  API_PORT=8000
  CORS_ORIGINS=http://localhost,http://192.168.1.26
  LOG_LEVEL=INFO
  DATABASE_POOL_SIZE=5
  DATABASE_MAX_OVERFLOW=10

Nginx Configuration (system):
  /etc/nginx/sites-available/security-camera
  Document root: /home/pi/Security-Camera-Central/www

MariaDB Configuration (system):
  /etc/mysql/mariadb.conf.d/50-server.cnf
  Database: security_cameras

NFS Exports (/etc/exports):
  /mnt/security_footage 192.168.1.0/24(rw,sync,no_subtree_check)
```

## Cleanup Recommendations

### Files to Keep (Core System)
✓ All files in api/, scripts/, database/, camera_nfs_mounts/, www/, tests/
✓ requirements.txt, .gitignore
✓ central_server_controller.sh, run_api.sh, gitsync.sh, killpython.sh
✓ README.md, AI_INSTRUCTIONS.md

### Files Needing Review
⚠ health_checker.py - Keep if actively used for monitoring
⚠ camera_health_check.py - Consolidate with health_checker.py?
⚠ thread_monitor.py - Consolidate with health_checker.py?
⚠ emergency_diagnostic.py - Keep for troubleshooting

### Files to Remove
✗ check_db.py (199B) - One-off debug script
✗ project_structure.txt (0B) - Generated file
✗ run_api.log (1.5MB) - Should be in logs/ directory

### Recommended File Moves
📁 Create monitoring/ directory:
   - Move: health_checker.py, camera_health_check.py, thread_monitor.py
   - Add: monitoring/README.md explaining monitoring strategy

📁 Create logs/ directory:
   - Move: run_api.log
   - Add: .gitignore rule to ignore *.log in logs/

📁 Create docs/ directory:
   - Move: AI_INSTRUCTIONS.md
   - Add: PROJECT_CENTRAL.md, FILE_MAP_CENTRAL.md

## Quick Reference

**Start Services:**
```bash
# API Server
./run_api.sh

# Background Workers
cd scripts
./jobctl.sh start all

# View status
./jobctl.sh status
```

**Database:**
```bash
# Connect to database
mysql -u pi -p security_cameras

# Run migrations
mysql -u pi -p security_cameras < database/003_add_ai_fields.sql
```

**NFS:**
```bash
# Add new camera
cd camera_nfs_mounts
sudo ./add_camera.sh camera_6 "Garage" "Garage Door"

# Verify NFS
sudo ./verify_nfs.sh
```

**Monitoring:**
```bash
# Check system health
python3 health_checker.py

# Check camera health
python3 camera_health_check.py
```

**Project Size:** 2.28MB (tracked files)
**Python Files:** 28
**PHP Files:** 22
**Total Files:** 87
**Directories:** 12
