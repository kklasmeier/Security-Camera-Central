#!/bin/bash
# test_conversion_setup.sh - Quick verification of MP4 conversion setup

echo "=========================================="
echo "MP4 Conversion Worker - Setup Verification"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/pi/Security-Camera-Central"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/convert_pending_mp4.sh"
ENV_FILE="${PROJECT_ROOT}/.env"
MEDIA_ROOT="/mnt/sdcard/security_camera/security_footage"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# Test 1: Check if .env exists
echo "Test 1: Checking .env file..."
if [ -f "$ENV_FILE" ]; then
    pass ".env file exists at $ENV_FILE"
else
    fail ".env file NOT found at $ENV_FILE"
    exit 1
fi

# Test 2: Check if required credentials are in .env
echo ""
echo "Test 2: Verifying database credentials in .env..."
required_vars=("DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if grep -q "^${var}=" "$ENV_FILE"; then
        pass "$var is defined"
    else
        fail "$var is MISSING"
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo ""
    fail "Missing required variables. Script will not work."
    exit 1
fi

# Test 3: Check if script exists
echo ""
echo "Test 3: Checking conversion script..."
if [ -f "$SCRIPT_PATH" ]; then
    pass "Script exists at $SCRIPT_PATH"
else
    fail "Script NOT found at $SCRIPT_PATH"
    echo "    Run: cp convert_pending_mp4.sh ${PROJECT_ROOT}/scripts/"
    exit 1
fi

# Test 4: Check if script is executable
echo ""
echo "Test 4: Checking script permissions..."
if [ -x "$SCRIPT_PATH" ]; then
    pass "Script is executable"
else
    fail "Script is NOT executable"
    echo "    Run: chmod +x $SCRIPT_PATH"
    exit 1
fi

# Test 5: Check for required commands
echo ""
echo "Test 5: Checking required system commands..."
commands=("mysql" "ffmpeg" "ffprobe" "flock")
missing_commands=()

for cmd in "${commands[@]}"; do
    if command -v "$cmd" &> /dev/null; then
        pass "$cmd is installed"
    else
        fail "$cmd is NOT installed"
        missing_commands+=("$cmd")
    fi
done

if [ ${#missing_commands[@]} -gt 0 ]; then
    echo ""
    fail "Missing required commands. Install with:"
    if [[ " ${missing_commands[@]} " =~ " mysql " ]]; then
        echo "    sudo apt-get install mariadb-client"
    fi
    if [[ " ${missing_commands[@]} " =~ " ffmpeg " ]] || [[ " ${missing_commands[@]} " =~ " ffprobe " ]]; then
        echo "    sudo apt-get install ffmpeg"
    fi
    exit 1
fi

# Test 6: Check media root directory
echo ""
echo "Test 6: Checking media root directory..."
if [ -d "$MEDIA_ROOT" ]; then
    pass "Media root exists at $MEDIA_ROOT"
else
    fail "Media root NOT found at $MEDIA_ROOT"
    exit 1
fi

# Test 7: Check camera directories
echo ""
echo "Test 7: Checking camera directories..."
camera_count=0
for i in {1..4}; do
    camera_dir="${MEDIA_ROOT}/camera_${i}/videos"
    if [ -d "$camera_dir" ]; then
        pass "Camera $i directory exists"
        camera_count=$((camera_count + 1))
    else
        warn "Camera $i directory NOT found (may not be registered yet)"
    fi
done

if [ $camera_count -eq 0 ]; then
    fail "No camera directories found!"
    exit 1
fi

# Test 8: Test database connection
echo ""
echo "Test 8: Testing database connection..."
DB_HOST=$(grep "^DB_HOST=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | xargs)
DB_USER=$(grep "^DB_USER=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | xargs)
DB_PASSWORD=$(grep "^DB_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | xargs)
DB_NAME=$(grep "^DB_NAME=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | xargs)

if mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;" &> /dev/null; then
    pass "Database connection successful"
else
    fail "Database connection FAILED"
    echo "    Check credentials in .env file"
    exit 1
fi

# Test 9: Check for pending conversions
echo ""
echo "Test 9: Checking for pending conversions..."
pending_count=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -N -e \
    "SELECT COUNT(*) FROM events 
     WHERE video_transferred = 1 
     AND mp4_conversion_status = 'pending';" 2>/dev/null)

if [ -n "$pending_count" ]; then
    if [ "$pending_count" -gt 0 ]; then
        pass "Found $pending_count events ready for conversion"
    else
        warn "No pending conversions found (cameras may not have uploaded videos yet)"
    fi
else
    fail "Could not query database for pending events"
    exit 1
fi

# Test 10: Check log directory
echo ""
echo "Test 10: Checking log directory..."
log_dir="${PROJECT_ROOT}/scripts/logs"
if [ -d "$log_dir" ]; then
    pass "Log directory exists"
else
    warn "Log directory doesn't exist (will be created on first run)"
    echo "    Creating: mkdir -p $log_dir"
    mkdir -p "$log_dir"
fi

# Summary
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""

if [ ${#missing_vars[@]} -eq 0 ] && [ ${#missing_commands[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Your setup is ready. Next steps:"
    echo ""
    echo "1. Run the script manually to test:"
    echo "   $SCRIPT_PATH"
    echo ""
    echo "2. Watch the log file:"
    echo "   tail -f ${PROJECT_ROOT}/scripts/logs/mp4_conversion.log"
    echo ""
    echo "3. If successful, add to crontab:"
    echo "   crontab -e"
    echo "   Add line: * * * * * $SCRIPT_PATH"
    echo ""
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Fix the issues above before running the conversion script."
    exit 1
fi