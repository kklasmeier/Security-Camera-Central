#!/bin/bash

################################################################################
# Add Camera Script
# Purpose: Add directory structure for a new camera
# Usage: sudo ./add_camera.sh <camera_name>
# Example: sudo ./add_camera.sh camera_5
################################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
STORAGE_BASE="/mnt/sdcard/security_camera/security_footage"
SUBDIRS=("videos" "pictures" "thumbs")
CAMERA_NAME="${1}"

################################################################################
# Helper Functions
################################################################################

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# Validation
################################################################################

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

validate_input() {
    if [ -z "$CAMERA_NAME" ]; then
        print_error "Camera name is required"
        echo ""
        echo "Usage: sudo $0 <camera_name>"
        echo "Example: sudo $0 camera_5"
        echo ""
        exit 1
    fi
    
    # Validate camera name format (alphanumeric and underscore only)
    if ! [[ $CAMERA_NAME =~ ^[a-zA-Z0-9_]+$ ]]; then
        print_error "Invalid camera name: $CAMERA_NAME"
        print_info "Camera name must contain only letters, numbers, and underscores"
        exit 1
    fi
}

check_storage_base() {
    if [ ! -d "$STORAGE_BASE" ]; then
        print_error "Storage base does not exist: $STORAGE_BASE"
        print_info "Run setup_nfs.sh first to create the base structure"
        exit 1
    fi
}

check_camera_exists() {
    CAMERA_PATH="$STORAGE_BASE/$CAMERA_NAME"
    
    if [ -d "$CAMERA_PATH" ]; then
        print_warning "Camera directory already exists: $CAMERA_PATH"
        echo ""
        read -p "Do you want to recreate the subdirectories? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi
    fi
}

################################################################################
# Main Functions
################################################################################

create_camera_structure() {
    CAMERA_PATH="$STORAGE_BASE/$CAMERA_NAME"
    
    echo ""
    print_info "Creating directory structure for: $CAMERA_NAME"
    echo ""
    
    # Create base camera directory
    if [ ! -d "$CAMERA_PATH" ]; then
        mkdir -p "$CAMERA_PATH"
        print_success "Created: $CAMERA_PATH"
    fi
    
    # Create subdirectories
    for subdir in "${SUBDIRS[@]}"; do
        SUBDIR_PATH="$CAMERA_PATH/$subdir"
        if [ ! -d "$SUBDIR_PATH" ]; then
            mkdir -p "$SUBDIR_PATH"
            print_success "Created: $SUBDIR_PATH"
        else
            print_warning "Already exists: $SUBDIR_PATH"
        fi
    done
    
    # Set ownership
    print_info "Setting ownership to pi:pi..."
    chown -R pi:pi "$CAMERA_PATH"
    print_success "Ownership set"
    
    # Set permissions
    print_info "Setting permissions (755)..."
    chmod -R 755 "$CAMERA_PATH"
    print_success "Permissions set"
}

verify_structure() {
    CAMERA_PATH="$STORAGE_BASE/$CAMERA_NAME"
    
    echo ""
    print_info "Verifying structure..."
    echo ""
    
    # Check ownership
    OWNER=$(stat -c '%U:%G' "$CAMERA_PATH")
    if [ "$OWNER" = "pi:pi" ]; then
        print_success "Ownership: $OWNER"
    else
        print_warning "Ownership: $OWNER (expected pi:pi)"
    fi
    
    # Check permissions
    PERMS=$(stat -c '%a' "$CAMERA_PATH")
    if [ "$PERMS" = "755" ]; then
        print_success "Permissions: $PERMS"
    else
        print_warning "Permissions: $PERMS (expected 755)"
    fi
    
    # List structure
    echo ""
    print_info "Directory structure:"
    tree "$CAMERA_PATH" 2>/dev/null || ls -la "$CAMERA_PATH"
}

print_summary() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Camera Added Successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Camera: $CAMERA_NAME"
    echo "Location: $STORAGE_BASE/$CAMERA_NAME"
    echo ""
    echo "Subdirectories created:"
    for subdir in "${SUBDIRS[@]}"; do
        echo "  • $subdir"
    done
    echo ""
    echo "Next steps:"
    echo "  1. Configure camera agent with camera_id: $CAMERA_NAME"
    echo "  2. Update central server database to register camera"
    echo "  3. Camera will automatically use this directory structure"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Add Camera to NFS Storage              ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
    
    check_root
    validate_input
    check_storage_base
    check_camera_exists
    create_camera_structure
    verify_structure
    print_summary
}

# Run main
main "$@"