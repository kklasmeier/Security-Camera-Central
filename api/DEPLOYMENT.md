# Session 1A-3 Deployment Guide

Quick reference for deploying the FastAPI application to your Raspberry Pi.

## Files Created

```
central_server/
├── api/
│   ├── __init__.py              ✅ Package marker
│   ├── main.py                  ✅ FastAPI app (395 lines)
│   ├── config.py                ✅ Configuration (36 lines)
│   ├── database.py              ✅ DB connection (66 lines)
│   ├── models.py                ✅ ORM models (72 lines)
│   ├── schemas.py               ✅ Pydantic schemas (22 lines)
│   └── routes/
│       ├── __init__.py          ✅ Package marker
│       └── health.py            ✅ Health endpoint (51 lines)
├── requirements.txt             ✅ Dependencies
├── run_api.sh                   ✅ Startup script (executable)
├── test_api.py                  ✅ Test suite (executable)
├── .env.example                 ✅ Environment template
├── README_api.md                ✅ Full documentation
└── DEPLOYMENT.md                ✅ This file
```

**Total: 13 files created**

---

## Prerequisites Checklist

Before deploying, ensure:

- ✅ Session 1A-1 complete (database schema created)
- ✅ MariaDB running: `sudo systemctl status mariadb`
- ✅ Database exists: `security_cameras`
- ✅ Tables exist: `cameras`, `events`, `logs`
- ✅ User exists: `securitycam` with password

---

## Deployment Steps

### 1. Copy Files to Raspberry Pi

From your development machine:

```bash
# Option A: Using SCP
scp -r /path/to/central_server pi@192.168.1.100:/home/pi/

# Option B: Using rsync (recommended)
rsync -av /path/to/central_server/ pi@192.168.1.100:/home/pi/central_server/
```

### 2. SSH to Raspberry Pi

```bash
ssh pi@192.168.1.100
cd /home/pi/central_server
```

### 3. Configure Database Password

```bash
# Copy environment template
cp .env.example .env

# Edit with your real database password
nano .env
```

Change this line:
```
DATABASE_URL=mysql+pymysql://securitycam:YOUR_PASSWORD_HERE@localhost/security_cameras
```

Also update the CORS origins with your Pi's actual IP:
```
CORS_ORIGINS=["http://localhost", "http://192.168.1.100"]
```

### 4. Make Scripts Executable

```bash
chmod +x run_api.sh
chmod +x test_api.py
```

### 5. Start the API

```bash
./run_api.sh
```

**Expected output:**
```
===================================================
Security Camera Central Server API
===================================================
Working directory: /home/pi/central_server
Creating virtual environment...
Activating virtual environment...
Installing dependencies...
Checking database connection...
Database connection successful

Starting API server...
API will be available at:
  - http://localhost:8000
  - http://192.168.1.100:8000

API Documentation:
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

Press Ctrl+C to stop the server

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Verification Steps

### Test 1: Health Check (on Pi)

```bash
# In a new terminal/SSH session
curl http://localhost:8000/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2025-10-28T12:34:56.789",
  "version": "1.0.0"
}
```

### Test 2: Health Check (from another device)

```bash
# From your laptop/another device on the network
curl http://192.168.1.100:8000/api/v1/health
```

Should return the same response.

### Test 3: API Documentation

Open in browser:
- Swagger UI: `http://192.168.1.100:8000/docs`
- ReDoc: `http://192.168.1.100:8000/redoc`

You should see the health check endpoint listed.

### Test 4: Run Test Suite

```bash
# In a new terminal (while API is running)
python3 test_api.py
```

**Expected output:**
```
============================================================
Security Camera Central Server API - Test Suite
============================================================
Testing API at: http://localhost:8000

=== Testing Root Endpoint ===
✓ Root endpoint returned: {...}

=== Testing Health Check Endpoint ===
Status: healthy
Database Connected: True
...
✓ Health check passed

=== Testing API Documentation ===
✓ Swagger UI accessible at http://localhost:8000/docs

=== Testing 404 Error Handling ===
✓ 404 error handled correctly

============================================================
TEST SUMMARY
============================================================
✓ PASS: Root Endpoint
✓ PASS: Health Check
✓ PASS: API Documentation
✓ PASS: 404 Handling

Total: 4/4 tests passed

✓ All tests passed! API is working correctly.
```

---

## Troubleshooting

### Error: Cannot connect to database

```bash
# Check MariaDB is running
sudo systemctl status mariadb
sudo systemctl start mariadb

# Test database connection manually
mysql -u securitycam -p security_cameras

# Verify password in .env matches database
cat .env | grep DATABASE_URL
```

### Error: Port already in use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill it
sudo kill <PID>
```

### Error: Module not found

```bash
# Make sure you're in the right directory
cd /home/pi/central_server

# Delete venv and reinstall
rm -rf venv
./run_api.sh
```

### API not accessible from other devices

```bash
# Check firewall
sudo ufw status

# Allow port 8000 if needed
sudo ufw allow 8000

# Verify API is listening on all interfaces
netstat -tulpn | grep 8000
# Should show: 0.0.0.0:8000
```

---

## Running in Background

### Option A: Using screen

```bash
# Start screen session
screen -S api

# Run API
./run_api.sh

# Detach: Press Ctrl+A, then D
# Reattach: screen -r api
# Kill: screen -X -S api quit
```

### Option B: Using tmux

```bash
# Start tmux session
tmux new -s api

# Run API
./run_api.sh

# Detach: Press Ctrl+B, then D
# Reattach: tmux attach -t api
# Kill: tmux kill-session -t api
```

### Option C: Using nohup

```bash
nohup ./run_api.sh > api.log 2>&1 &

# Check logs
tail -f api.log

# Find process
ps aux | grep uvicorn

# Stop
kill <PID>
```

---

## Next Steps

Once the API is verified working:

1. **Keep API running** (use screen/tmux/nohup)
2. **Proceed to Session 1A-4** (Camera Registration Endpoint)
3. **Note your database password** - you'll need it for future sessions

---

## Session Complete ✅

**Deliverables:**
- ✅ FastAPI application structure
- ✅ Database connection with SQLAlchemy ORM
- ✅ Health check endpoint
- ✅ Configuration management
- ✅ Startup and test scripts
- ✅ Documentation

**What works:**
- API starts successfully
- Health check returns "healthy"
- Database connectivity verified
- API documentation accessible
- CORS configured for web UI

**Ready for:**
- Session 1A-4: Camera Registration Endpoint
- Session 1A-5: Event Creation Endpoint
- Subsequent endpoint development

---

**Questions?** See README_api.md for detailed documentation.