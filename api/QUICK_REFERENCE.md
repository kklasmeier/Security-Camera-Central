# Session 1A-3 Quick Reference

## 🚀 Deploy (5 commands)

```bash
# 1. Copy to Pi
scp -r central_server pi@192.168.1.100:/home/pi/

# 2. SSH to Pi
ssh pi@192.168.1.100

# 3. Configure password
cd /home/pi/central_server
cp .env.example .env
nano .env  # Edit DATABASE_URL with real password

# 4. Start API
chmod +x run_api.sh test_api.py
./run_api.sh

# 5. Test (in new terminal)
curl http://localhost:8000/api/v1/health
```

---

## ✅ Verify (4 tests)

```bash
# Test 1: Health check
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy", "database_connected": true, ...}

# Test 2: From another device
curl http://192.168.1.100:8000/api/v1/health

# Test 3: API docs
# Open browser: http://192.168.1.100:8000/docs

# Test 4: Automated tests
python3 test_api.py
# Expected: "✓ All tests passed!"
```

---

## 📁 Files Created (14 total)

```
central_server/
├── api/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # DB connection
│   ├── models.py            # ORM models
│   ├── schemas.py           # Pydantic schemas
│   └── routes/
│       └── health.py        # Health endpoint
├── requirements.txt         # Dependencies
├── run_api.sh              # Start script ⭐
├── test_api.py             # Test script
├── .env.example            # Config template
├── README_api.md           # Full docs (400+ lines)
├── DEPLOYMENT.md           # Deploy guide
└── SESSION_1A-3_SUMMARY.md # Summary
```

---

## 🔧 Troubleshooting

### Cannot connect to database
```bash
sudo systemctl start mariadb
mysql -u securitycam -p security_cameras
# Check password in .env matches
```

### Port already in use
```bash
sudo lsof -i :8000
sudo kill <PID>
```

### Module not found
```bash
rm -rf venv
./run_api.sh
```

### Not accessible from network
```bash
# Check firewall
sudo ufw allow 8000
# Verify listening on all interfaces
netstat -tulpn | grep 8000  # Should show 0.0.0.0:8000
```

---

## 🌐 API Endpoints (Current)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## 📝 Configuration (.env)

```bash
# Required: Change the password!
DATABASE_URL=mysql+pymysql://securitycam:YOUR_PASSWORD@localhost/security_cameras

# Optional: Defaults are good
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost", "http://192.168.1.100"]
LOG_LEVEL=INFO
```

---

## 🏃 Running in Background

```bash
# Option 1: screen
screen -S api
./run_api.sh
# Ctrl+A, then D to detach
# screen -r api to reattach

# Option 2: tmux
tmux new -s api
./run_api.sh
# Ctrl+B, then D to detach
# tmux attach -t api to reattach

# Option 3: nohup
nohup ./run_api.sh > api.log 2>&1 &
tail -f api.log  # View logs
```

---

## 📊 Status

**Session 1A-3:** ✅ COMPLETE

**Next:** Session 1A-4 (Camera Registration Endpoint)

**What works:**
- ✅ API starts and runs
- ✅ Database connectivity
- ✅ Health check endpoint
- ✅ API documentation
- ✅ CORS for web UI

**What's missing (future sessions):**
- ⏳ Camera registration
- ⏳ Event creation
- ⏳ File updates
- ⏳ Log ingestion
- ⏳ Query endpoints

---

## 📚 Documentation

- **README_api.md** - Complete guide with troubleshooting
- **DEPLOYMENT.md** - Step-by-step deployment
- **SESSION_1A-3_SUMMARY.md** - Technical summary
- **This file** - Quick reference

---

## 🔗 URLs (After Deployment)

- API: `http://192.168.1.100:8000`
- Health: `http://192.168.1.100:8000/api/v1/health`
- Docs: `http://192.168.1.100:8000/docs`
- ReDoc: `http://192.168.1.100:8000/redoc`

*(Replace 192.168.1.100 with your Pi's actual IP)*

---

**Questions?** See README_api.md for detailed documentation.