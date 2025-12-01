# Security Camera Central Server - Cleanup Recommendations

## Current Root Directory Issues

Your root directory contains **12 files** that should either be removed, relocated, or need review:

```
/home/pi/Security-Camera-Central/
├── health_checker.py              12.1KB  [REVIEW - consolidate?]
├── camera_health_check.py         6.0KB   [REVIEW - consolidate?]
├── thread_monitor.py              6.2KB   [REVIEW - consolidate?]
├── emergency_diagnostic.py        10.4KB  [KEEP - troubleshooting tool]
├── check_db.py                    199B    [DELETE - one-off debug]
├── project_structure.txt          0B      [DELETE - generated file]
├── run_api.log                    1.5MB   [MOVE to logs/]
├── AI_INSTRUCTIONS.md             1.4KB   [MOVE to docs/]
├── README.md                      424B    [KEEP - enhance content]
├── requirements.txt               300B    [KEEP]
├── .gitignore                     1.6KB   [KEEP]
└── project_inventory.py           6.7KB   [KEEP - utility script]
```

## Recommended Directory Reorganization

### Phase 1: Quick Wins (Safe to do immediately)

**1. Delete obsolete files:**
```bash
cd /home/pi/Security-Camera-Central
rm check_db.py                    # One-off debug script
rm project_structure.txt          # Generated inventory file
```

**2. Create logs directory and move log file:**
```bash
mkdir -p logs
mv run_api.log logs/
echo "*.log" >> .gitignore        # Ignore future log files
```

**3. Create docs directory and move documentation:**
```bash
mkdir -p docs
mv AI_INSTRUCTIONS.md docs/
# Copy new documentation
cp PROJECT_CENTRAL.md docs/
cp FILE_MAP_CENTRAL.md docs/
```

### Phase 2: Consolidate Monitoring (Requires review)

**Analyze monitoring overlap:**

Your root contains 4 monitoring scripts:
- `health_checker.py` (12.1KB) - Comprehensive health checks
- `camera_health_check.py` (6.0KB) - Camera-specific checks
- `thread_monitor.py` (6.2KB) - Worker thread monitoring
- `emergency_diagnostic.py` (10.4KB) - Emergency diagnostics

**Recommended action:**
```bash
mkdir -p monitoring
```

**Option A - Keep all, just reorganize:**
```bash
mv health_checker.py monitoring/
mv camera_health_check.py monitoring/
mv thread_monitor.py monitoring/
mv emergency_diagnostic.py monitoring/
```

**Option B - Consolidate redundancy (more work):**
1. Review if `camera_health_check.py` functionality is in `health_checker.py`
2. Review if `thread_monitor.py` functionality is in `health_checker.py`
3. If yes, delete duplicates and enhance `health_checker.py`
4. Keep `emergency_diagnostic.py` separate (different use case)

### Phase 3: Enhance Documentation

**Update README.md** to include:
```markdown
# Security Camera Central Server

Central coordination server for multi-camera security system.

## Quick Start
- API Server: `./run_api.sh`
- Background Workers: `cd scripts && ./jobctl.sh start all`
- Web UI: http://192.168.1.26

## Documentation
- [Project Overview](docs/PROJECT_CENTRAL.md)
- [File Map](docs/FILE_MAP_CENTRAL.md)
- [AI Instructions](docs/AI_INSTRUCTIONS.md)

## Components
- FastAPI REST API (port 8000)
- MariaDB database
- NFS shared storage
- Background workers (MP4 conversion, optimization, AI processing)
- PHP web interface (nginx)

See docs/ for detailed documentation.
```

## Proposed Final Structure

```
Security-Camera-Central/
├── Core Directories (No changes needed)
│   ├── api/                          FastAPI application
│   ├── scripts/                      Background workers
│   ├── database/                     Schema and migrations
│   ├── camera_nfs_mounts/            NFS setup scripts
│   ├── www/                          Web interface
│   └── tests/                        Test suite
│
├── New Organized Directories
│   ├── docs/                         [NEW]
│   │   ├── PROJECT_CENTRAL.md        Project documentation
│   │   ├── FILE_MAP_CENTRAL.md       File map
│   │   ├── AI_INSTRUCTIONS.md        AI context
│   │   └── CLEANUP.md                This file
│   │
│   ├── logs/                         [NEW]
│   │   ├── run_api.log               API server logs
│   │   ├── worker_*.log              Worker logs
│   │   └── .gitignore                (ignore *.log)
│   │
│   └── monitoring/                   [NEW]
│       ├── health_checker.py         Main health monitor
│       ├── camera_health_check.py    Camera health (or delete if redundant)
│       ├── thread_monitor.py         Thread monitor (or delete if redundant)
│       ├── emergency_diagnostic.py   Emergency diagnostics
│       └── README.md                 Monitoring documentation
│
├── Root Files (Clean and minimal)
│   ├── README.md                     Enhanced project overview
│   ├── requirements.txt              Python dependencies
│   ├── .gitignore                    Git ignore (updated)
│   ├── project_inventory.py          Utility script
│   ├── central_server_controller.sh  Service management
│   ├── run_api.sh                    API launcher
│   ├── gitsync.sh                    Git sync
│   └── killpython.sh                 Emergency cleanup
│
└── Runtime Directories (gitignored)
    ├── __pycache__/
    └── *.egg-info/
```

## Implementation Script

Here's a bash script to implement Phase 1 safely:

```bash
#!/bin/bash
# cleanup_phase1.sh - Safe cleanup of Security-Camera-Central

set -e  # Exit on error

echo "Security Camera Central Server - Cleanup Phase 1"
echo "================================================"
echo ""

# Verify we're in the right directory
if [[ ! -d "api" ]] || [[ ! -d "www" ]]; then
    echo "ERROR: Must run from Security-Camera-Central root directory"
    exit 1
fi

echo "Creating new directories..."
mkdir -p docs
mkdir -p logs
mkdir -p monitoring

echo ""
echo "Moving documentation..."
if [[ -f "AI_INSTRUCTIONS.md" ]]; then
    mv AI_INSTRUCTIONS.md docs/
    echo "  ✓ Moved AI_INSTRUCTIONS.md to docs/"
fi

echo ""
echo "Moving log files..."
if [[ -f "run_api.log" ]]; then
    mv run_api.log logs/
    echo "  ✓ Moved run_api.log to logs/"
fi

echo ""
echo "Deleting obsolete files..."
if [[ -f "check_db.py" ]]; then
    rm check_db.py
    echo "  ✓ Deleted check_db.py"
fi

if [[ -f "project_structure.txt" ]]; then
    rm project_structure.txt
    echo "  ✓ Deleted project_structure.txt"
fi

echo ""
echo "Updating .gitignore..."
if ! grep -q "^logs/\*.log" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Log files" >> .gitignore
    echo "logs/*.log" >> .gitignore
    echo "  ✓ Added logs/*.log to .gitignore"
fi

echo ""
echo "================================================"
echo "Phase 1 Cleanup Complete!"
echo ""
echo "Next steps (manual review needed):"
echo "1. Review monitoring scripts for consolidation"
echo "2. Move monitoring scripts: mv *_checker.py monitoring/"
echo "3. Enhance README.md with quick start guide"
echo "4. Update documentation paths in code if needed"
echo ""
echo "Current structure:"
ls -la docs/ 2>/dev/null || echo "  (docs/ created but empty)"
ls -la logs/ 2>/dev/null || echo "  (logs/ created but empty)"
ls -la monitoring/ 2>/dev/null || echo "  (monitoring/ created but empty)"
```

## Benefits of Cleanup

**Before (Current):**
- 12 loose files in root directory
- Unclear what's essential vs. temporary
- Log files mixed with code
- Documentation scattered

**After (Proposed):**
- 8 essential files in root
- Clear separation: code / docs / logs / monitoring
- Easy to identify obsolete files
- Better for AI context (docs/ directory)
- Cleaner for version control

## .gitignore Updates Needed

Add these entries to `.gitignore`:

```gitignore
# Logs
logs/*.log
run_api.log

# Documentation (auto-generated)
project_structure.txt

# Python cache
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

## Migration Checklist

- [ ] Phase 1: Safe deletions and moves
  - [ ] Delete check_db.py
  - [ ] Delete project_structure.txt
  - [ ] Create logs/ directory
  - [ ] Move run_api.log to logs/
  - [ ] Create docs/ directory
  - [ ] Move AI_INSTRUCTIONS.md to docs/
  - [ ] Copy PROJECT_CENTRAL.md to docs/
  - [ ] Copy FILE_MAP_CENTRAL.md to docs/
  - [ ] Update .gitignore

- [ ] Phase 2: Review monitoring scripts
  - [ ] Analyze health_checker.py functionality
  - [ ] Analyze camera_health_check.py functionality
  - [ ] Analyze thread_monitor.py functionality
  - [ ] Decide: consolidate or keep separate
  - [ ] Create monitoring/ directory
  - [ ] Move monitoring scripts
  - [ ] Create monitoring/README.md

- [ ] Phase 3: Documentation
  - [ ] Enhance README.md
  - [ ] Update any hard-coded paths in scripts
  - [ ] Verify all imports still work
  - [ ] Update systemd service files if needed

- [ ] Phase 4: Validation
  - [ ] Test API starts: ./run_api.sh
  - [ ] Test workers start: scripts/jobctl.sh start all
  - [ ] Verify web interface loads
  - [ ] Check monitoring scripts still work
  - [ ] Run test suite: pytest tests/

## Risk Assessment

**Low Risk (Phase 1):**
- Deleting check_db.py and project_structure.txt - these are clearly temporary
- Moving log files to logs/ - doesn't affect functionality
- Moving docs to docs/ - organizational only

**Medium Risk (Phase 2):**
- Moving monitoring scripts - verify no hard-coded paths
- Consolidating monitoring scripts - requires code review

**No Risk:**
- Enhancing README.md
- Updating .gitignore

## Rollback Plan

If something breaks:

```bash
# Restore from git
git checkout .gitignore
git checkout README.md

# Manually restore files from backup
cp /backup/check_db.py ./
cp /backup/run_api.log ./

# Or restore entire directory
cd /home/pi
mv Security-Camera-Central Security-Camera-Central.broken
git clone <repo> Security-Camera-Central
```

## Recommendation

**Start with Phase 1** - it's safe, low-risk, and immediately improves organization. You can always do Phase 2 later after reviewing the monitoring scripts more carefully.

The cleanup script above implements Phase 1 safely with validation checks.
