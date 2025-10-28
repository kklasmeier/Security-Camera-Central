#!/bin/bash

################################################################################
# NFS Server Setup Script for Security Camera System
# Purpose: Configure NFS server on central Raspberry Pi 4 for shared storage
# Target: /mnt/sdcard/security_camera/security_footage/
# Usage: sudo ./setup_nfs.sh [subnet]
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STORAGE_BASE="/mnt/sdcard/security_camera/security_footage"
DEFAULT_SUBNET="192.168.1.0/24"
SUBNET="${1:-$DEFAULT_SUBNET}"
CAMERAS=("camera_1" "camera_2" "camera_3" "camera_4")
SUBDIRS=("videos" "pictures" "thumbs")

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

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

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

################################################################################
# Main Functions
################################################################################

check_storage_base() {
    print_header "Checking Storage Base"
    
    if [ ! -d "/mnt/sdcard" ]; then
        print_error "/mnt/sdcard does not exist!"
        print_info "Please ensure your SSD is mounted at /mnt/sdcard"
        exit 1
    fi
    
    print_success "/mnt/sdcard exists"
    
    # Show available space
    AVAILABLE=$(df -h /mnt/sdcard | awk 'NR==2 {print $4}')
    print_info "Available space on SSD: $AVAILABLE"
}

install_nfs_server() {
    print_header "Installing NFS Server"
    
    # Check if already installed
    if dpkg -l | grep -q nfs-kernel-server; then
        print_warning "nfs-kernel-server is already installed"
    else
        print_info "Updating package list..."
        apt-get update -qq
        
        print_info "Installing nfs-kernel-server..."
        apt-get install -y nfs-kernel-server
        
        print_success "NFS server installed"
    fi
}

create_directory_structure() {
    print_header "Creating Directory Structure"
    
    # Create base directory
    if [ ! -d "$STORAGE_BASE" ]; then
        mkdir -p "$STORAGE_BASE"
        print_success "Created: $STORAGE_BASE"
    else
        print_warning "Directory already exists: $STORAGE_BASE"
    fi
    
    # Create camera subdirectories
    for camera in "${CAMERAS[@]}"; do
        for subdir in "${SUBDIRS[@]}"; do
            TARGET="$STORAGE_BASE/$camera/$subdir"
            if [ ! -d "$TARGET" ]; then
                mkdir -p "$TARGET"
                print_success "Created: $TARGET"
            else
                print_warning "Already exists: $TARGET"
            fi
        done
    done
    
    # Set ownership and permissions
    print_info "Setting ownership to pi:pi..."
    chown -R pi:pi "$STORAGE_BASE"
    
    print_info "Setting permissions (755 for directories)..."
    find "$STORAGE_BASE" -type d -exec chmod 755 {} \;
    
    print_success "Directory structure created and configured"
}

configure_nfs_exports() {
    print_header "Configuring NFS Exports"
    
    EXPORT_LINE="$STORAGE_BASE $SUBNET(rw,sync,no_subtree_check,no_root_squash)"
    EXPORTS_FILE="/etc/exports"
    
    # Backup existing exports file
    if [ -f "$EXPORTS_FILE" ]; then
        BACKUP_FILE="${EXPORTS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$EXPORTS_FILE" "$BACKUP_FILE"
        print_info "Backed up existing exports to: $BACKUP_FILE"
    fi
    
    # Check if export already exists
    if grep -q "^$STORAGE_BASE " "$EXPORTS_FILE" 2>/dev/null; then
        print_warning "Export already exists in $EXPORTS_FILE"
        print_info "Current export:"
        grep "^$STORAGE_BASE " "$EXPORTS_FILE"
    else
        # Add export with comment
        echo "" >> "$EXPORTS_FILE"
        echo "# Security Camera System - Shared Storage" >> "$EXPORTS_FILE"
        echo "$EXPORT_LINE" >> "$EXPORTS_FILE"
        print_success "Added export to $EXPORTS_FILE"
    fi
    
    print_info "Export configuration:"
    echo "  $EXPORT_LINE"
    
    # Apply exports
    print_info "Applying exports..."
    exportfs -ra
    print_success "Exports applied"
}

configure_nfs_service() {
    print_header "Configuring NFS Service"
    
    # Enable service
    print_info "Enabling nfs-kernel-server to start on boot..."
    systemctl enable nfs-kernel-server
    print_success "Service enabled"
    
    # Start/restart service
    print_info "Starting NFS service..."
    systemctl restart nfs-kernel-server
    
    # Check status
    sleep 2
    if systemctl is-active --quiet nfs-kernel-server; then
        print_success "NFS service is running"
    else
        print_error "NFS service failed to start"
        print_info "Check logs with: sudo journalctl -u nfs-kernel-server -n 50"
        exit 1
    fi
}

verify_configuration() {
    print_header "Verifying Configuration"
    
    # Check service status
    if systemctl is-active --quiet nfs-kernel-server; then
        print_success "NFS service is active"
    else
        print_error "NFS service is not active"
    fi
    
    # Check if enabled
    if systemctl is-enabled --quiet nfs-kernel-server; then
        print_success "NFS service is enabled for boot"
    else
        print_warning "NFS service is not enabled for boot"
    fi
    
    # Check exports
    print_info "Current exports:"
    exportfs -v | grep "$STORAGE_BASE" || print_warning "Export not found in active exports"
    
    # Check directory structure
    TOTAL_DIRS=$(find "$STORAGE_BASE" -type d | wc -l)
    print_success "Created $TOTAL_DIRS directories"
    
    # Check permissions
    OWNER=$(stat -c '%U:%G' "$STORAGE_BASE")
    if [ "$OWNER" = "pi:pi" ]; then
        print_success "Ownership is correct (pi:pi)"
    else
        print_warning "Ownership is $OWNER (expected pi:pi)"
    fi
}

print_summary() {
    print_header "Setup Complete!"
    
    echo -e "${GREEN}NFS server is configured and running${NC}\n"
    
    echo "Configuration Summary:"
    echo "  Storage Location: $STORAGE_BASE"
    echo "  Subnet Allowed:   $SUBNET"
    echo "  Cameras:          ${CAMERAS[*]}"
    echo "  Server IP:        192.168.1.26"
    echo ""
    
    echo "Next Steps:"
    echo "  1. Verify setup: sudo ./verify_nfs.sh"
    echo "  2. Test from camera: sudo ./test_nfs_mount.sh 192.168.1.26"
    echo "  3. Configure cameras to mount this share (Session 1B)"
    echo ""
    
    echo "Camera Mount Command:"
    echo "  sudo mount -t nfs 192.168.1.26:$STORAGE_BASE /mnt/footage"
    echo ""
    
    echo "To add more cameras later:"
    echo "  sudo ./add_camera.sh camera_5"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "NFS Server Setup for Security Camera System"
    
    echo "This script will:"
    echo "  • Install NFS server package"
    echo "  • Create directory structure on SSD"
    echo "  • Configure NFS exports"
    echo "  • Enable and start NFS service"
    echo ""
    echo "Target: $STORAGE_BASE"
    echo "Subnet: $SUBNET"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    
    check_root
    check_storage_base
    install_nfs_server
    create_directory_structure
    configure_nfs_exports
    configure_nfs_service
    verify_configuration
    print_summary
}

# Run main function
main "$@"