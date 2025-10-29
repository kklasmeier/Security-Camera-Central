#!/bin/bash
# Script to start the Security Camera Central Server API

# Exit on error
set -e

echo "==================================================="
echo "Security Camera Central Server API"
echo "==================================================="

# Check if running on Raspberry Pi (check for /boot/config.txt)
if [ -f /boot/config.txt ]; then
    echo "Detected Raspberry Pi environment"
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Copy .env.example to .env and configure your database password"
    echo ""
    echo "Using default configuration from config.py"
    echo ""
fi

# Check database connection
echo "Checking database connection..."
python3 -c "from api.database import check_database_connection; exit(0 if check_database_connection() else 1)" || {
    echo ""
    echo "ERROR: Cannot connect to database!"
    echo "Please check:"
    echo "  1. MariaDB is running: sudo systemctl status mariadb"
    echo "  2. Database exists: security_cameras"
    echo "  3. Database password is correct in .env or api/config.py"
    echo ""
    exit 1
}

echo ""
echo "Starting API server..."
echo "API will be available at:"
echo "  - http://localhost:8000"
echo "  - http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "API Documentation:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API server with unified logging
# Note: Logging configuration is in api/main.py and will apply to all loggers including Uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload