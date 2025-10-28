# Security Camera Central Server API

REST API for multi-camera security system. This API runs on the central Raspberry Pi 4 and provides endpoints for:
- Camera registration
- Event creation and management
- File transfer status tracking
- Centralized logging
- Web UI data retrieval

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Starting the API](#starting-the-api)
6. [Testing](#testing)
7. [API Documentation](#api-documentation)
8. [Project Structure](#project-structure)
9. [Adding New Endpoints](#adding-new-endpoints)
10. [Troubleshooting](#troubleshooting)

---

## Overview

**Technology Stack:**
- **Framework:** FastAPI (modern, fast, auto-documented)
- **Server:** Uvicorn (ASGI server)
- **Database:** MariaDB (via SQLAlchemy ORM)
- **Validation:** Pydantic (type validation)

**Features:**
- Auto-generated API documentation (Swagger UI, ReDoc)
- Type validation for all requests/responses
- Connection pooling for efficient database access
- CORS support for web UI
- Structured logging

**Current Status (Session 1A-3):**
- ✅ FastAPI application structure
- ✅ Database connection with SQLAlchemy
- ✅ ORM models (Camera, Event, Log)
- ✅ Health check endpoint
- ⏳ Camera/Event/Log endpoints (Sessions 1A-4 through 1A-9)

---

## Prerequisites

**Hardware:**
- Raspberry Pi 4 (central server)
- Network connection

**Software:**
- Python 3.9 or higher
- MariaDB server installed and running
- Database `security_cameras` created (Session 1A-1)

**Database Setup (must be complete):**
```bash
# Check MariaDB is running
sudo systemctl status mariadb

# Verify database exists
mysql -u securitycam -p -e "SHOW DATABASES;"
# Should see: security_cameras

# Verify tables exist
mysql -u securitycam -p security_cameras -e "SHOW TABLES;"
# Should see: cameras, events, logs
```

---

## Installation

### Step 1: Copy Files to Pi

Copy the entire `central_server` directory to the Raspberry Pi:

```bash
# On your development machine
scp -r central_server/ pi@192.168.1.100:/home/pi/

# Or use rsync
rsync -av central_server/ pi@192.168.1.100:/home/pi/central_server/
```

### Step 2: SSH to Pi

```bash
ssh pi@192.168.1.100
cd /home/pi/central_server
```

### Step 3: Run Setup Script

The `run_api.sh` script handles everything:
- Creates virtual environment
- Installs dependencies
- Checks database connection
- Starts the API

```bash
chmod +x run_api.sh
./run_api.sh
```

**Manual Installation (if needed):**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages
```

---

## Configuration

### Environment Variables

Configuration is managed through environment variables with sensible defaults.

**Create `.env` file:**

```bash
cp .env.example .env
nano .env
```

**Edit `.env` with your settings:**

```bash
# Database - CHANGE THE PASSWORD!
DATABASE_URL=mysql+pymysql://securitycam:YOUR_REAL_PASSWORD@localhost/security_cameras

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS - Add your Pi's IP address
CORS_ORIGINS=["http://localhost", "http://192.168.1.100"]

# Logging
LOG_LEVEL=INFO
```

**Default Configuration (if no .env file):**

See `api/config.py` for defaults:
- Database: `mysql+pymysql://securitycam:password@localhost/security_cameras`
- API Port: `8000`
- CORS: `["http://localhost", "http://192.168.1.100"]`

---

## Starting the API

### Development Mode (with auto-reload)

```bash
./run_api.sh
```

The API will start and display:
```
Starting API server...
API will be available at:
  - http://localhost:8000
  - http://192.168.1.100:8000

API Documentation:
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

Press Ctrl+C to stop the server
```

### Background Mode

```bash
# Using nohup
nohup ./run_api.sh > api.log 2>&1 &

# Or using screen/tmux
screen -S api
./run_api.sh
# Press Ctrl+A then D to detach
```

### Production Mode (Systemd Service)

This will be set up in Session 1E-2. Preview:

```bash
# Start service
sudo systemctl start central-api

# Enable on boot
sudo systemctl enable central-api

# Check status
sudo systemctl status central-api

# View logs
sudo journalctl -u central-api -f
```

---

## Testing

### Quick Test

Visit the health check endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2025-10-28T12:34:56.789",
  "version": "1.0.0"
}
```

### Comprehensive Test Suite

Run the automated test script:

```bash
python3 test_api.py
```

Tests include:
- Root endpoint
- Health check
- API documentation
- 404 error handling

### Manual Testing

**Root endpoint:**
```bash
curl http://localhost:8000/
```

**From another device on network:**
```bash
curl http://192.168.1.100:8000/api/v1/health
```

---

## API Documentation

FastAPI automatically generates interactive API documentation.

### Swagger UI (Interactive)

Open in browser: `http://192.168.1.100:8000/docs`

**Features:**
- List of all endpoints
- Try endpoints directly in browser
- See request/response schemas
- View example requests/responses

### ReDoc (Documentation)

Open in browser: `http://192.168.1.100:8000/redoc`

**Features:**
- Clean, readable documentation
- Detailed schema information
- Search functionality

### Current Endpoints (Session 1A-3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint - API info |
| GET | `/api/v1/health` | Health check - status & DB connectivity |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |

### Future Endpoints (Sessions 1A-4 through 1A-9)

Will be added in subsequent sessions:
- `POST /api/v1/cameras/register` - Camera registration
- `POST /api/v1/events` - Create event
- `PATCH /api/v1/events/{id}/files` - Update file status
- `GET /api/v1/events` - List events
- `GET /api/v1/events/{id}` - Get event details
- `POST /api/v1/logs` - Submit logs
- `GET /api/v1/logs` - Query logs
- `GET /api/v1/cameras` - List cameras

---

## Project Structure

```
central_server/
├── api/
│   ├── __init__.py              # Package marker
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration & settings
│   ├── database.py              # DB connection & session management
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic request/response models
│   └── routes/
│       ├── __init__.py          # Package marker
│       ├── health.py            # Health check endpoint
│       ├── cameras.py           # (Session 1A-4)
│       ├── events.py            # (Sessions 1A-5, 1A-6, 1A-8)
│       └── logs.py              # (Sessions 1A-7, 1A-9)
├── requirements.txt             # Python dependencies
├── run_api.sh                   # Startup script
├── test_api.py                  # Test suite
├── .env.example                 # Environment template
├── .env                         # Your config (create this)
└── README_api.md                # This file
```

---

## Adding New Endpoints

Future sessions will add more endpoints. Here's the pattern to follow:

### Step 1: Define Pydantic Schema

Edit `api/schemas.py`:

```python
class EventCreateRequest(BaseModel):
    camera_id: str
    motion_score: float

class EventCreateResponse(BaseModel):
    event_id: int
    timestamp: datetime
```

### Step 2: Create Route Handler

Create new file `api/routes/events.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Event
from api.schemas import EventCreateRequest, EventCreateResponse

router = APIRouter()

@router.post("/events", response_model=EventCreateResponse)
def create_event(
    request: EventCreateRequest,
    db: Session = Depends(get_db)
):
    # Create event in database
    event = Event(
        camera_id=request.camera_id,
        motion_score=request.motion_score
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return EventCreateResponse(
        event_id=event.id,
        timestamp=event.timestamp
    )
```

### Step 3: Register Router

Edit `api/main.py`:

```python
from api.routes import health, events  # Add import

# ... existing code ...

# Include the new router
app.include_router(events.router, prefix="/api/v1", tags=["Events"])
```

### Step 4: Test

Restart API and visit `/docs` to see new endpoint.

---

## Troubleshooting

### Error: Cannot connect to database

**Symptoms:**
```
ERROR: Cannot connect to database!
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server...")
```

**Solutions:**

1. **Check MariaDB is running:**
   ```bash
   sudo systemctl status mariadb
   sudo systemctl start mariadb
   ```

2. **Verify database exists:**
   ```bash
   mysql -u securitycam -p -e "SHOW DATABASES;"
   ```

3. **Check password in `.env`:**
   ```bash
   cat .env | grep DATABASE_URL
   ```

4. **Test connection manually:**
   ```bash
   mysql -u securitycam -p security_cameras
   ```

### Error: Port already in use

**Symptoms:**
```
ERROR: [Errno 98] Address already in use
```

**Solutions:**

1. **Find process using port 8000:**
   ```bash
   sudo lsof -i :8000
   ```

2. **Kill the process:**
   ```bash
   sudo kill <PID>
   ```

3. **Or use different port:**
   Edit `.env`:
   ```
   API_PORT=8001
   ```

### Error: Module not found

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

### Health check returns "unhealthy"

**Check:**

1. **Database tables exist:**
   ```bash
   mysql -u securitycam -p security_cameras -e "SHOW TABLES;"
   ```
   Should show: cameras, events, logs

2. **Database user has permissions:**
   ```bash
   mysql -u root -p -e "SHOW GRANTS FOR 'securitycam'@'localhost';"
   ```

3. **Check API logs:**
   Look for database connection errors in terminal output

### Cannot access API from another device

**Check:**

1. **API is listening on all interfaces:**
   ```bash
   cat .env | grep API_HOST
   # Should be: API_HOST=0.0.0.0
   ```

2. **Firewall allows port 8000:**
   ```bash
   sudo ufw status
   # If enabled, allow port:
   sudo ufw allow 8000
   ```

3. **Get Pi's IP address:**
   ```bash
   hostname -I
   ```
   Use this IP: `http://192.168.1.XXX:8000`

### API docs not loading

**Check:**

1. **API is running:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Access from correct URL:**
   - From Pi: `http://localhost:8000/docs`
   - From other device: `http://192.168.1.100:8000/docs`

3. **Browser cache:**
   Try hard refresh (Ctrl+Shift+R) or incognito mode

---

## Support

**Getting Help:**

1. Check this README first
2. Review error messages in terminal
3. Check API logs
4. Test database connection manually
5. Verify all prerequisites are met

**Useful Commands:**

```bash
# Check API is running
ps aux | grep uvicorn

# Check database connection
python3 -c "from api.database import check_database_connection; print(check_database_connection())"

# View recent logs (if using systemd)
sudo journalctl -u central-api -n 50

# Restart API (if using systemd)
sudo systemctl restart central-api
```

---

## Next Steps

After Session 1A-3 is complete and tested, proceed to:

- **Session 1A-4:** Camera Registration Endpoint
- **Session 1A-5:** Event Creation Endpoint
- **Session 1A-6:** File Update Endpoint
- **Session 1A-7:** Log Ingestion Endpoint
- **Session 1A-8:** Event Query Endpoints
- **Session 1A-9:** Log & Camera Query Endpoints

Each session will add new routes to the API.

---

**Session 1A-3 Complete** ✅

API foundation is ready. Health check endpoint is functional. Database connectivity verified.