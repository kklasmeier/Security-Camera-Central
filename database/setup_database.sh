#!/bin/bash
# ============================================================================
# Security Camera System - Database Setup Script
# ============================================================================
# Purpose: Automated database and user creation for MariaDB
# Usage: sudo ./setup_database.sh
# ============================================================================

set -e  # Exit on any error

echo "============================================"
echo "Security Camera System - Database Setup"
echo "============================================"
echo ""

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root or with sudo"
    echo "Usage: sudo ./setup_database.sh"
    exit 1
fi

# Check if MariaDB is installed and running
if ! systemctl is-active --quiet mariadb; then
    echo "ERROR: MariaDB is not running"
    echo "Please start MariaDB: sudo systemctl start mariadb"
    exit 1
fi

echo "✓ MariaDB is running"
echo ""

# Prompt for MariaDB root password
echo "Step 1: MariaDB Root Authentication"
echo "------------------------------------"
read -sp "Enter MariaDB root password: " MYSQL_ROOT_PASSWORD
echo ""
echo ""

# Test root connection
if ! mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1;" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to MariaDB with provided root password"
    echo "Please verify your root password is correct"
    exit 1
fi

echo "✓ Root authentication successful"
echo ""

# Prompt for new securitycam user password
echo "Step 2: Create Database User"
echo "------------------------------------"
echo "Creating user: securitycam"
echo ""
read -sp "Enter password for 'securitycam' user: " SECURITYCAM_PASSWORD
echo ""
read -sp "Confirm password: " SECURITYCAM_PASSWORD_CONFIRM
echo ""

if [ "$SECURITYCAM_PASSWORD" != "$SECURITYCAM_PASSWORD_CONFIRM" ]; then
    echo "ERROR: Passwords do not match"
    exit 1
fi

if [ -z "$SECURITYCAM_PASSWORD" ]; then
    echo "ERROR: Password cannot be empty"
    exit 1
fi

echo ""
echo "✓ Password confirmed"
echo ""

# Execute schema creation
echo "Step 3: Creating Database Schema"
echo "------------------------------------"

# Create user and grant privileges
mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<EOF
-- Create user if doesn't exist
CREATE USER IF NOT EXISTS 'securitycam'@'localhost' IDENTIFIED BY '${SECURITYCAM_PASSWORD}';

-- Grant privileges on security_cameras database
GRANT ALL PRIVILEGES ON security_cameras.* TO 'securitycam'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify user was created
SELECT User, Host FROM mysql.user WHERE User = 'securitycam';
EOF

if [ $? -eq 0 ]; then
    echo "✓ User 'securitycam' created successfully"
else
    echo "ERROR: Failed to create user"
    exit 1
fi

echo ""

# Create database and tables from schema.sql
echo "Creating database and tables..."
mysql -u root -p"${MYSQL_ROOT_PASSWORD}" < schema.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Database schema created successfully"
else
    echo "ERROR: Failed to create database schema"
    exit 1
fi

echo ""

# Verify tables were created
echo "Step 4: Verification"
echo "------------------------------------"

TABLE_COUNT=$(mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -D security_cameras -se "SHOW TABLES;" | wc -l)

if [ "$TABLE_COUNT" -eq 3 ]; then
    echo "✓ All 3 tables created successfully:"
    mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -D security_cameras -e "SHOW TABLES;"
    echo ""
else
    echo "WARNING: Expected 3 tables, found $TABLE_COUNT"
fi

# Test connection with new user
echo "Testing connection with 'securitycam' user..."
if mysql -u securitycam -p"${SECURITYCAM_PASSWORD}" -D security_cameras -e "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ User 'securitycam' can connect successfully"
else
    echo "ERROR: Cannot connect with 'securitycam' user"
    exit 1
fi

echo ""

# Save connection info (for reference only - NOT secure for production)
echo "Step 5: Connection Information"
echo "------------------------------------"
echo ""
echo "Database: security_cameras"
echo "User: securitycam"
echo "Host: localhost"
echo "Port: 3306"
echo ""
echo "Python connection string:"
echo "mysql+pymysql://securitycam:PASSWORD@localhost/security_cameras"
echo ""
echo "PHP PDO connection:"
echo "mysql:host=localhost;dbname=security_cameras;charset=utf8mb4"
echo ""

# Save to .env file
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file with database credentials..."
    cat > "$ENV_FILE" <<ENVEOF
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=security_cameras
DB_USER=securitycam
DB_PASSWORD=${SECURITYCAM_PASSWORD}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=GENERATE_A_SECURE_SECRET_KEY

# NFS Configuration
NFS_MOUNT_PATH=/mnt/security_footage

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/security-api/api.log
ENVEOF
    echo "✓ .env file created at $ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "✓ Set permissions to 600 (owner read/write only)"
else
    echo "Note: .env file already exists, not overwriting"
    echo "You may need to manually update DB_PASSWORD in: $ENV_FILE"
fi

echo ""
echo "============================================"
echo "✓ Database Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Run test_database.sql to verify installation"
echo "2. Configure your API to use these credentials"
echo "3. Start building Session 1A-3 (FastAPI application)"
echo ""
echo "To test:"
echo "  mysql -u securitycam -p security_cameras < test_database.sql"
echo ""