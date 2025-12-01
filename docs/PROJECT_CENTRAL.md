# Security Camera Central Server - Project Documentation

## System Overview
Python FastAPI-based central server running on Raspberry Pi 4, serving as the coordination hub for a multi-camera distributed security system. Manages camera registration, event coordination, file tracking, centralized logging, and hosts the web UI. Coordinates with AI processing server (Pi 5) for event analysis.

**Architecture:** Camera agents (5x Pi Zero 2W) → Central Server (Pi 4 - API + DB + Web) → AI Server (Pi 5 - Ollama)

## Core Components

### API Layer (FastAPI)
- **api/main.py** - FastAPI application entry point. Configures CORS, unified logging, includes all routers under /api/v1 prefix, implements startup/shutdown lifecycle with database connection verification.
- **api/config.py** - Configuration management using pydantic-settings. Loads from environment variables, manages database URL, API host/port, CORS origins, connection pooling settings.
- **api/database.py** - SQLAlchemy connection management with pooling (pool_size, max_overflow), session factory, dependency injection helper (get_db()), connection health checks.

### Data Models & Schemas
- **api/models.py** - SQLAlchemy ORM models defining database schema:
  - Camera: camera_id, name, location, ip_address, status, last_seen, timestamps
  - Event: camera_id FK, timestamp, motion_score, confidence_score, status (processing/complete/interrupted/failed), file paths (image_a/b, thumbnail, video_h264/mp4), transfer flags, MP4 conversion status, AI analysis fields
  - Log: source, timestamp, level, message (centralized logging table)
- **api/schemas.py** (13.5KB) - Pydantic request/response validation schemas with field validators:
  - CameraRegisterRequest, CameraResponse
  - EventCreateRequest, EventResponse, EventListResponse, EventStatusUpdateRequest, FileUpdateRequest
  - LogEntry, LogIngestResponse, LogResponse, LogListResponse
  - HealthCheckResponse

### API Routes
- **api/routes/cameras.py** - Camera registration endpoint, camera management, status updates
- **api/routes/events.py** (15.0KB) - Event creation, event queries with pagination, event status updates, file transfer updates (image_a/b, thumbnail, video with duration), listing with filters
- **api/routes/health.py** - Health check endpoint, database connectivity verification
- **api/routes/logs.py** (6.5KB) - Centralized log ingestion (batch insert), log queries with pagination, filtering by source/level/time range
- **api/routes/stats.py** - Statistics endpoints (event counts, camera metrics, system summaries)

### Background Processing Scripts (scripts/)
- **scripts/ai_event_processor.py** (15.6KB) - AI analysis worker: claims unclaimed events from database, fetches images from NFS, processes with Ollama (moondream for vision, deepseek-r1 for descriptions), updates database with AI results. Runs continuously in background.
- **scripts/convert_pending_mp4.py** (25.1KB) - Video conversion worker: monitors events with mp4_conversion_status='pending', converts H.264 to MP4 using FFmpeg, updates database status to 'complete'. Progressive processing to avoid overwhelming system.
- **scripts/optimize_mp4.py** (7.4KB) - MP4 optimization worker: reduces file sizes of converted MP4s using FFmpeg re-encoding with optimized settings, updates file paths in database.
- **scripts/jobctl.sh** (6.3KB) - Background job controller: manages starting/stopping/status of background workers (AI processor, MP4 converter, optimizer).

### Health Monitoring & Diagnostics
- **health_checker.py** (12.1KB) - Comprehensive health monitoring: checks camera API responsiveness, database connectivity, NFS mount status, background worker health, generates health reports.
- **camera_health_check.py** (6.0KB) - Camera-specific health checker: pings camera APIs, verifies last_seen timestamps, detects stuck/offline cameras.
- **thread_monitor.py** (6.2KB) - Thread monitoring for background workers: detects hung threads, monitors resource usage.
- **emergency_diagnostic.py** (10.4KB) - Emergency diagnostic tool: comprehensive system state dump, database queries, file system checks, process status for troubleshooting critical issues.

### NFS Storage Management (camera_nfs_mounts/)
- **setup_nfs.sh** (8.0KB) - Initial NFS server setup: configures exports, creates directory structure, sets permissions
- **add_camera.sh** (5.8KB) - Adds new camera to NFS: creates camera-specific directories (pictures/, videos/, thumbs/), updates exports
- **verify_nfs.sh** (10.0KB) - Verifies NFS configuration: checks exports, permissions, mount status
- **test_nfs_mount.sh** (9.3KB) - Tests NFS mounts: creates test files, verifies read/write access
- **README.md** (19.3KB) - NFS setup documentation and troubleshooting

### Database Management (database/)
- **schema.sql** (6.7KB) - Initial database schema: creates cameras, events, logs tables with indexes
- **setup_database.sh** (5.5KB) - Database initialization script: creates database, applies schema, sets permissions
- **test_database.sql** (10.3KB) - Database test queries: validates schema, tests common queries
- **001_add_status_to_events.sql** - Migration: adds status field to events table
- **002_add_claim_tracking_to_events.sql** - Migration: adds AI claim tracking fields
- **003_add_ai_fields.sql** - Migration: adds AI analysis result fields
- **004_add_confidence_score.sql** - Migration: adds confidence_score field
- **migration_fix_mp4_status.sql** - Migration: fixes MP4 conversion status for existing events

### Web Interface (www/)
- **index.php** (9.5KB) - Main event gallery: displays events in grid/list view, pagination, filters
- **event.php** (18.1KB) - Event detail view: shows images, video player, AI analysis, event metadata
- **live.php** (3.8KB) - Live camera streaming interface: MJPEG stream viewer, camera selection
- **logs.php** (17.1KB) - Centralized log viewer: displays logs from all cameras and central server, filtering, search
- **includes/db.php** (17.5KB) - Database connection and query helpers for PHP
- **includes/functions.php** (13.5KB) - Shared PHP functions: file path helpers, thumbnail generation, date formatting
- **includes/session.php** (5.7KB) - Session-based camera selection: persists selected camera across page loads
- **includes/camera_selector.php** - Camera selection dropdown component
- **includes/camera_status.php** (5.4KB) - Camera status display: online/offline indicators, last seen timestamps
- **includes/header.php**, **includes/footer.php** - Common page layout components
- **assets/style.css** (53.7KB) - Main stylesheet
- **assets/script.js** (28.5KB) - JavaScript for dynamic updates, AJAX requests, gallery interactions
- **api/** - PHP API endpoints for web UI (set_streaming.php, refresh_camera_status.php, get_new_logs.php)
- **ajax/** - AJAX endpoints (get_newer_logs.php)

### Service Management & Utilities
- **central_server_controller.sh** (3.5KB) - Systemd service controller for central server components
- **run_api.sh** (2.2KB) - API server launcher: starts uvicorn with proper settings
- **gitsync.sh** (4.5KB) - Git synchronization utility
- **killpython.sh** (1.7KB) - Emergency Python process cleanup

### Testing (tests/)
- **test_api.py** - API endpoint tests
- **test_camera_registration.py** (9.1KB) - Camera registration flow tests
- **test_event_creation.py** (10.5KB) - Event creation and update tests
- **test_event_queries.py** (26.9KB) - Comprehensive event query tests (pagination, filtering, sorting)
- **test_file_updates.py** (14.1KB) - File transfer status update tests
- **test_log_ingestion.py** (10.8KB) - Log ingestion and query tests
- **test_logs_cameras_query.py** (22.1KB) - Log query with camera filtering tests
- **manual_test.sh** (2.6KB) - Manual testing script for quick validation

## Data Flow

1. **Camera Registration:** Camera agent → POST /api/v1/cameras/register → Database (cameras table) → Response with registration confirmation
2. **Event Creation:** Camera detects motion → POST /api/v1/events → Database (events table with status='processing') → Response with event_id
3. **File Transfer:** Camera transfers files to NFS → PATCH /api/v1/events/{id}/files → Database (update transfer flags) → Status confirmation
4. **Event Status:** Camera completes processing → PATCH /api/v1/events/{id}/status → Database (status='complete') → Confirmation
5. **MP4 Conversion:** convert_pending_mp4.py polls events → FFmpeg conversion → Database update (mp4_path, status='complete')
6. **MP4 Optimization:** optimize_mp4.py polls converted files → FFmpeg re-encode → Database update (optimized path)
7. **AI Processing:** ai_event_processor.py claims event → Ollama analysis (moondream + deepseek-r1) → Database update (AI fields)
8. **Web UI:** User browses → PHP queries database → Displays events with images/videos/AI descriptions

## Key Design Patterns

- **API-First Architecture:** All camera communication via REST API, no direct database access from agents
- **Status-Based Workflows:** Events progress through states (processing → complete/interrupted/failed), MP4 conversion tracked separately
- **Progressive File Availability:** Thumbnails appear immediately, images transfer quickly, videos process in background, AI analysis happens last
- **Claim-Based Processing:** AI processor claims events to prevent duplicate processing, uses database transactions for atomicity
- **Connection Pooling:** Database connections reused via SQLAlchemy pool (pool_size, max_overflow) for efficiency
- **Batch Operations:** Logs ingested in batches, reduces database load
- **Validation Layers:** Pydantic schemas validate all API inputs, prevent invalid data in database
- **Graceful Degradation:** API continues working if background workers are down, workers retry on failures

## File Organization Analysis

### Active Core Files (Keep These)
**API Layer:**
- api/main.py, config.py, database.py, models.py, schemas.py
- api/routes/*.py (all route modules)

**Background Workers:**
- scripts/ai_event_processor.py
- scripts/convert_pending_mp4.py
- scripts/optimize_mp4.py
- scripts/jobctl.sh

**Infrastructure:**
- camera_nfs_mounts/* (all NFS setup scripts)
- database/schema.sql, setup_database.sh
- database/*.sql (all migrations)

**Web Interface:**
- www/*.php (all pages)
- www/includes/*.php (all includes)
- www/assets/* (all assets)
- www/api/*.php (all API endpoints)
- www/ajax/*.php (all AJAX endpoints)

**Service Management:**
- central_server_controller.sh
- run_api.sh

**Testing:**
- tests/*.py (all test files)

### Potentially Obsolete Root Files (Consider Cleanup)
**Diagnostic Scripts (overlap with health_checker.py):**
- emergency_diagnostic.py - If functionality covered by health_checker.py
- camera_health_check.py - If functionality integrated into health_checker.py
- thread_monitor.py - If not actively used for monitoring

**Development/Debug Files:**
- check_db.py (199B) - Tiny script, likely one-off debug
- run_api.log (1.5MB) - Log file should be in logs/ directory, not root
- project_structure.txt (0B) - Inventory output, not needed in repo

**Documentation:**
- AI_INSTRUCTIONS.md - Useful context but could move to docs/
- README.md - Currently minimal, should be enhanced

### Recommended Cleanup Structure
```
Security-Camera-Central/
├── api/                    # Keep as-is
├── scripts/                # Keep as-is
├── camera_nfs_mounts/      # Keep as-is
├── database/               # Keep as-is
├── www/                    # Keep as-is
├── tests/                  # Keep as-is
├── docs/                   # NEW - move AI_INSTRUCTIONS.md here
├── logs/                   # NEW - move run_api.log here
├── monitoring/             # NEW - consolidate health_checker.py, camera_health_check.py, thread_monitor.py
├── requirements.txt        # Keep
├── README.md              # Keep (enhance)
├── central_server_controller.sh  # Keep
├── run_api.sh             # Keep
├── gitsync.sh             # Keep
└── killpython.sh          # Keep
```

**Files to Remove:**
- check_db.py (one-off debug)
- project_structure.txt (generated file)
- emergency_diagnostic.py (if redundant with health_checker.py)

**Files to Relocate:**
- run_api.log → logs/
- AI_INSTRUCTIONS.md → docs/
- health_checker.py, camera_health_check.py, thread_monitor.py → monitoring/

## Current State & Architecture

**Active Services:**
- FastAPI server on port 8000 (uvicorn)
- Nginx web server (serving www/)
- MariaDB database
- NFS server (exports to camera agents)
- Background workers: MP4 converter, optimizer, AI processor

**Database Schema:**
- 3 tables: cameras, events, logs
- 4 migrations applied (status, claim tracking, AI fields, confidence score)
- Indexes on: camera_id, timestamp, source, level for efficient queries

**NFS Structure:**
```
/mnt/security_footage/
├── camera_1/
│   ├── pictures/
│   ├── videos/
│   └── thumbs/
├── camera_2/
...
```

**API Endpoints:** 
- Health: GET /api/v1/health
- Cameras: POST /api/v1/cameras/register, GET /api/v1/cameras
- Events: POST /api/v1/events, GET /api/v1/events, PATCH /api/v1/events/{id}/status, PATCH /api/v1/events/{id}/files
- Logs: POST /api/v1/logs, GET /api/v1/logs
- Stats: GET /api/v1/stats/*

**Web Pages:**
- / (index.php) - Event gallery
- /event.php?id={id} - Event details
- /live.php - Live camera streams
- /logs.php - Centralized log viewer

## Dependencies
**Python (requirements.txt):**
- fastapi==0.104.1 - Web framework
- uvicorn[standard]==0.24.0 - ASGI server
- sqlalchemy==2.0.23 - ORM
- pymysql==1.1.0 - MySQL driver
- pydantic==2.5.0 - Data validation
- requests==2.31.0 - HTTP client

**AI Scripts (scripts/requirements.txt):**
- Additional dependencies for Ollama integration

**System:**
- MariaDB 10.x - Database
- FFmpeg - Video conversion/optimization
- Nginx - Web server
- NFS server - Shared storage

## Deployment
**Prerequisites:**
1. Raspberry Pi 4 with Raspberry Pi OS
2. MariaDB installed and running
3. NFS server configured
4. Python 3.11+

**Setup:**
1. Clone repo to /home/pi/Security-Camera-Central
2. Create .env file with database credentials
3. Run database/setup_database.sh
4. Run camera_nfs_mounts/setup_nfs.sh
5. Install Python dependencies: pip install -r requirements.txt
6. Start API: ./run_api.sh
7. Configure nginx for www/
8. Start background workers: scripts/jobctl.sh start

**Critical:** Keep .env file secure, never commit database credentials
