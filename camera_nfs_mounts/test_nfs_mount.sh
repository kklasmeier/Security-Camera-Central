#!/bin/bash

################################################################################
# NFS Mount Test Script (Run on Camera)
# Purpose: Test NFS mount from camera to central server
# Usage: sudo ./test_nfs_mount.sh <server_ip>
# Example: sudo ./test_nfs_mount.sh 192.168.1.26
################################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVER_IP="${1}"
REMOTE_PATH="/mnt/sdcard/security_camera/security_footage"
LOCAL_MOUNT="/tmp/nfs_test_mount"
TEST_FILE="test_$(date +%s).txt"

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

cleanup() {
    print_info "Cleaning up..."
    
    # Remove test file if it exists
    if [ -f "$LOCAL_MOUNT/camera_1/pictures/$TEST_FILE" ]; then
        rm -f "$LOCAL_MOUNT/camera_1/pictures/$TEST_FILE" 2>/dev/null
        print_info "Removed test file"
    fi
    
    # Unmount if mounted
    if mountpoint -q "$LOCAL_MOUNT" 2>/dev/null; then
        umount "$LOCAL_MOUNT" 2>/dev/null
        print_info "Unmounted $LOCAL_MOUNT"
    fi
    
    # Remove mount directory
    if [ -d "$LOCAL_MOUNT" ]; then
        rmdir "$LOCAL_MOUNT" 2>/dev/null
        print_info "Removed temporary mount directory"
    fi
}

################################################################################
# Validation Functions
################################################################################

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

validate_input() {
    if [ -z "$SERVER_IP" ]; then
        print_error "Server IP address is required"
        echo ""
        echo "Usage: sudo $0 <server_ip>"
        echo "Example: sudo $0 192.168.1.26"
        exit 1
    fi
    
    # Basic IP validation
    if ! [[ $SERVER_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        print_error "Invalid IP address format: $SERVER_IP"
        exit 1
    fi
}

check_nfs_client() {
    print_header "Checking NFS Client"
    
    if dpkg -l | grep -q nfs-common; then
        print_success "nfs-common is installed"
    else
        print_error "nfs-common is NOT installed"
        print_info "Installing nfs-common..."
        apt-get update -qq
        apt-get install -y nfs-common
        print_success "nfs-common installed"
    fi
}

################################################################################
# Test Functions
################################################################################

test_network_connectivity() {
    print_header "Testing Network Connectivity"
    
    print_info "Pinging server: $SERVER_IP"
    
    if ping -c 3 -W 2 "$SERVER_IP" > /dev/null 2>&1; then
        print_success "Server is reachable"
    else
        print_error "Cannot reach server at $SERVER_IP"
        print_info "Check network connection and server IP"
        exit 1
    fi
}

test_nfs_port() {
    print_header "Testing NFS Port"
    
    print_info "Checking if NFS port 2049 is accessible..."
    
    if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$SERVER_IP/2049" 2>/dev/null; then
        print_success "NFS port 2049 is accessible"
    else
        print_warning "Cannot connect to NFS port 2049"
        print_info "Server may not be running NFS service"
    fi
}

test_showmount() {
    print_header "Testing Showmount"
    
    print_info "Querying available exports from server..."
    
    RESULT=$(showmount -e "$SERVER_IP" 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        print_success "Server responded to showmount"
        echo ""
        echo "Available exports:"
        echo "$RESULT" | sed 's/^/  /'
        echo ""
        
        if echo "$RESULT" | grep -q "$REMOTE_PATH"; then
            print_success "Found expected export: $REMOTE_PATH"
        else
            print_warning "Expected export not found: $REMOTE_PATH"
        fi
    else
        print_error "Showmount failed"
        print_info "Error: $RESULT"
        exit 1
    fi
}

test_mount() {
    print_header "Testing Mount"
    
    # Create mount point
    mkdir -p "$LOCAL_MOUNT"
    print_info "Created mount point: $LOCAL_MOUNT"
    
    # Attempt mount
    print_info "Attempting to mount NFS share..."
    
    if mount -t nfs "$SERVER_IP:$REMOTE_PATH" "$LOCAL_MOUNT"; then
        print_success "Mount successful!"
    else
        print_error "Mount failed"
        cleanup
        exit 1
    fi
    
    # Verify mount
    if mountpoint -q "$LOCAL_MOUNT"; then
        print_success "Mount point is valid"
    else
        print_error "Mount verification failed"
        cleanup
        exit 1
    fi
}

test_read_access() {
    print_header "Testing Read Access"
    
    print_info "Listing directories..."
    
    if ls "$LOCAL_MOUNT" > /dev/null 2>&1; then
        print_success "Can read directory listing"
        
        echo ""
        echo "Contents of $LOCAL_MOUNT:"
        ls -la "$LOCAL_MOUNT" | sed 's/^/  /'
        echo ""
        
        # Check for expected camera directories
        for camera in camera_1 camera_2 camera_3 camera_4; do
            if [ -d "$LOCAL_MOUNT/$camera" ]; then
                print_success "Found camera directory: $camera"
            else
                print_warning "Camera directory not found: $camera"
            fi
        done
    else
        print_error "Cannot read directory"
        cleanup
        exit 1
    fi
}

test_write_access() {
    print_header "Testing Write Access"
    
    TEST_TARGET="$LOCAL_MOUNT/camera_1/pictures/$TEST_FILE"
    
    print_info "Attempting to create test file..."
    print_info "Target: $TEST_TARGET"
    
    if echo "NFS write test - $(date)" > "$TEST_TARGET" 2>/dev/null; then
        print_success "File created successfully"
        
        # Verify file exists
        if [ -f "$TEST_TARGET" ]; then
            print_success "File verified on mount"
            
            # Read back content
            CONTENT=$(cat "$TEST_TARGET")
            print_info "Content: $CONTENT"
        else
            print_error "File not found after creation"
            cleanup
            exit 1
        fi
    else
        print_error "Cannot write to NFS share"
        print_info "Check permissions on server"
        cleanup
        exit 1
    fi
}

test_delete_access() {
    print_header "Testing Delete Access"
    
    TEST_TARGET="$LOCAL_MOUNT/camera_1/pictures/$TEST_FILE"
    
    print_info "Attempting to delete test file..."
    
    if rm -f "$TEST_TARGET" 2>/dev/null; then
        print_success "File deleted successfully"
        
        # Verify deletion
        if [ ! -f "$TEST_TARGET" ]; then
            print_success "Deletion verified"
        else
            print_warning "File still exists after deletion"
        fi
    else
        print_error "Cannot delete file"
        cleanup
        exit 1
    fi
}

################################################################################
# Summary
################################################################################

print_test_summary() {
    print_header "Test Summary"
    
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "NFS mount is working correctly:"
    echo "  Server:      $SERVER_IP"
    echo "  Remote Path: $REMOTE_PATH"
    echo "  Local Mount: $LOCAL_MOUNT"
    echo ""
    echo "Capabilities verified:"
    echo "  ✓ Network connectivity"
    echo "  ✓ NFS service accessible"
    echo "  ✓ Export visible"
    echo "  ✓ Mount successful"
    echo "  ✓ Read access"
    echo "  ✓ Write access"
    echo "  ✓ Delete access"
    echo ""
    echo "Next steps:"
    echo "  1. Configure permanent mount in /etc/fstab"
    echo "  2. Set up mount retry service"
    echo "  3. Test camera agent file transfers"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   NFS Mount Test Script                  ║${NC}"
    echo -e "${BLUE}║   Run on Camera Device                   ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
    echo ""
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Run tests
    check_root
    validate_input
    check_nfs_client
    test_network_connectivity
    test_nfs_port
    test_showmount
    test_mount
    test_read_access
    test_write_access
    test_delete_access
    
    # Cleanup happens automatically via trap
    
    print_test_summary
}

# Run main
main "$@"