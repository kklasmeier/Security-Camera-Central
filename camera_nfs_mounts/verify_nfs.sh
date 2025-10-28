#!/bin/bash

################################################################################
# NFS Server Verification Script
# Purpose: Verify NFS server configuration for security camera system
# Usage: sudo ./verify_nfs.sh
################################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

STORAGE_BASE="/mnt/sdcard/security_camera/security_footage"
EXPECTED_CAMERAS=("camera_1" "camera_2" "camera_3" "camera_4")
EXPECTED_SUBDIRS=("videos" "pictures" "thumbs")

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

################################################################################
# Helper Functions
################################################################################

print_test_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

test_pass() {
    echo -e "${GREEN}✓ PASS${NC} - $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC} - $1"
    ((TESTS_FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠ WARN${NC} - $1"
    ((TESTS_WARNING++))
}

print_info() {
    echo -e "  ${BLUE}→${NC} $1"
}

################################################################################
# Test Functions
################################################################################

test_root_check() {
    print_test_header "Test 1: Root Privileges"
    
    if [ "$EUID" -ne 0 ]; then
        test_fail "Script must be run as root (use sudo)"
        return 1
    else
        test_pass "Running with root privileges"
        return 0
    fi
}

test_nfs_package() {
    print_test_header "Test 2: NFS Package Installation"
    
    if dpkg -l | grep -q nfs-kernel-server; then
        test_pass "nfs-kernel-server is installed"
        
        # Show version
        VERSION=$(dpkg -l | grep nfs-kernel-server | awk '{print $3}')
        print_info "Version: $VERSION"
        return 0
    else
        test_fail "nfs-kernel-server is NOT installed"
        print_info "Install with: sudo apt-get install nfs-kernel-server"
        return 1
    fi
}

test_storage_base() {
    print_test_header "Test 3: Storage Base Directory"
    
    if [ -d "$STORAGE_BASE" ]; then
        test_pass "Storage base exists: $STORAGE_BASE"
        
        # Show disk usage
        USAGE=$(df -h "$STORAGE_BASE" | awk 'NR==2 {print $5}')
        AVAILABLE=$(df -h "$STORAGE_BASE" | awk 'NR==2 {print $4}')
        print_info "Disk usage: $USAGE used, $AVAILABLE available"
        return 0
    else
        test_fail "Storage base does NOT exist: $STORAGE_BASE"
        print_info "Create with: sudo mkdir -p $STORAGE_BASE"
        return 1
    fi
}

test_directory_structure() {
    print_test_header "Test 4: Directory Structure"
    
    local all_exist=true
    local count=0
    
    for camera in "${EXPECTED_CAMERAS[@]}"; do
        for subdir in "${EXPECTED_SUBDIRS[@]}"; do
            TARGET="$STORAGE_BASE/$camera/$subdir"
            if [ -d "$TARGET" ]; then
                ((count++))
            else
                if $all_exist; then
                    echo "  Missing directories:"
                    all_exist=false
                fi
                echo "    - $TARGET"
            fi
        done
    done
    
    if $all_exist; then
        test_pass "All $count expected directories exist"
        return 0
    else
        test_fail "Some directories are missing"
        print_info "Found $count directories, expected 12"
        return 1
    fi
}

test_permissions() {
    print_test_header "Test 5: Ownership and Permissions"
    
    local owner=$(stat -c '%U:%G' "$STORAGE_BASE" 2>/dev/null)
    local perms=$(stat -c '%a' "$STORAGE_BASE" 2>/dev/null)
    
    if [ "$owner" = "pi:pi" ]; then
        test_pass "Ownership is correct (pi:pi)"
    else
        test_fail "Ownership is $owner (expected pi:pi)"
        print_info "Fix with: sudo chown -R pi:pi $STORAGE_BASE"
        return 1
    fi
    
    if [ "$perms" = "755" ]; then
        test_pass "Base directory permissions are correct (755)"
    else
        test_warn "Base directory permissions are $perms (expected 755)"
        print_info "Fix with: sudo chmod 755 $STORAGE_BASE"
    fi
    
    return 0
}

test_nfs_service() {
    print_test_header "Test 6: NFS Service Status"
    
    if systemctl is-active --quiet nfs-kernel-server; then
        test_pass "NFS service is active (running)"
    else
        test_fail "NFS service is NOT active"
        print_info "Start with: sudo systemctl start nfs-kernel-server"
        return 1
    fi
    
    if systemctl is-enabled --quiet nfs-kernel-server; then
        test_pass "NFS service is enabled (starts on boot)"
    else
        test_warn "NFS service is NOT enabled for boot"
        print_info "Enable with: sudo systemctl enable nfs-kernel-server"
    fi
    
    return 0
}

test_exports_config() {
    print_test_header "Test 7: NFS Export Configuration"
    
    if [ ! -f /etc/exports ]; then
        test_fail "/etc/exports file does not exist"
        return 1
    fi
    
    if grep -q "$STORAGE_BASE" /etc/exports; then
        test_pass "Export is configured in /etc/exports"
        print_info "Configuration:"
        grep "$STORAGE_BASE" /etc/exports | sed 's/^/    /'
        return 0
    else
        test_fail "Export NOT found in /etc/exports"
        print_info "Add to /etc/exports:"
        print_info "$STORAGE_BASE 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)"
        return 1
    fi
}

test_active_exports() {
    print_test_header "Test 8: Active NFS Exports"
    
    if command -v exportfs &> /dev/null; then
        if exportfs -v | grep -q "$STORAGE_BASE"; then
            test_pass "Export is active and available"
            print_info "Active export details:"
            exportfs -v | grep "$STORAGE_BASE" | sed 's/^/    /'
            return 0
        else
            test_fail "Export is NOT active"
            print_info "Apply with: sudo exportfs -ra"
            return 1
        fi
    else
        test_fail "exportfs command not found"
        return 1
    fi
}

test_network_ports() {
    print_test_header "Test 9: NFS Network Ports"
    
    # Check if port 2049 is listening
    if ss -tuln | grep -q ':2049'; then
        test_pass "NFS port 2049 is listening"
        
        # Show listening addresses
        print_info "Listening on:"
        ss -tuln | grep ':2049' | sed 's/^/    /'
        return 0
    else
        test_fail "NFS port 2049 is NOT listening"
        print_info "Check NFS service status"
        return 1
    fi
}

test_showmount() {
    print_test_header "Test 10: Showmount Test"
    
    if command -v showmount &> /dev/null; then
        RESULT=$(showmount -e localhost 2>&1)
        
        if echo "$RESULT" | grep -q "$STORAGE_BASE"; then
            test_pass "Export is visible via showmount"
            print_info "Showmount output:"
            echo "$RESULT" | sed 's/^/    /'
            return 0
        else
            test_fail "Export is NOT visible via showmount"
            print_info "Output: $RESULT"
            return 1
        fi
    else
        test_warn "showmount command not available"
        print_info "Install with: sudo apt-get install nfs-common"
        return 0
    fi
}

################################################################################
# Summary and Recommendations
################################################################################

print_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}VERIFICATION SUMMARY${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    TOTAL=$((TESTS_PASSED + TESTS_FAILED + TESTS_WARNING))
    
    echo -e "  ${GREEN}Passed:${NC}   $TESTS_PASSED"
    echo -e "  ${RED}Failed:${NC}   $TESTS_FAILED"
    echo -e "  ${YELLOW}Warnings:${NC} $TESTS_WARNING"
    echo -e "  Total:    $TOTAL"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ NFS Server is properly configured!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Test mount from a camera:"
        echo "     sudo ./test_nfs_mount.sh 192.168.1.26"
        echo ""
        echo "  2. Configure cameras to mount this share (Session 1B)"
        echo ""
    else
        echo -e "${RED}✗ NFS Server has configuration issues${NC}"
        echo ""
        echo "Please address the failed tests above."
        echo "Run this script again after making fixes."
        echo ""
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   NFS Server Verification Script         ║${NC}"
    echo -e "${BLUE}║   Security Camera System                 ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
    echo ""
    echo "Verifying NFS configuration..."
    echo "Target: $STORAGE_BASE"
    echo ""
    
    test_root_check
    test_nfs_package
    test_storage_base
    test_directory_structure
    test_permissions
    test_nfs_service
    test_exports_config
    test_active_exports
    test_network_ports
    test_showmount
    
    print_summary
    
    # Exit code based on failures
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main
main "$@"