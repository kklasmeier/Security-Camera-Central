# Session 1A-2: Testing Checklist

Use this checklist to verify your NFS setup is working correctly.

## Phase 1: Central Server Setup

### Pre-Installation Checks
- [ ] Central server (Pi 4) is running and accessible
- [ ] SSD is mounted at `/mnt/sdcard`
- [ ] You have sudo access as user `pi`
- [ ] Server has static IP: 192.168.1.26

### Installation
- [ ] Copied all 5 files to `/home/pi/Security-Camera-Central/`
- [ ] Made scripts executable: `chmod +x *.sh`
- [ ] Ran: `sudo ./setup_nfs.sh`
- [ ] Setup completed without errors

### Verification (Central Server)
Run: `sudo ./verify_nfs.sh`

- [ ] Test 1: Root Privileges - PASS
- [ ] Test 2: NFS Package Installation - PASS
- [ ] Test 3: Storage Base Directory - PASS
- [ ] Test 4: Directory Structure - PASS (12 directories)
- [ ] Test 5: Ownership and Permissions - PASS
- [ ] Test 6: NFS Service Status - PASS
- [ ] Test 7: NFS Export Configuration - PASS
- [ ] Test 8: Active NFS Exports - PASS
- [ ] Test 9: NFS Network Ports - PASS (port 2049 listening)
- [ ] Test 10: Showmount Test - PASS

### Manual Verification
```bash
# Check service
sudo systemctl status nfs-kernel-server
# Should show: active (running)

# Check exports
sudo exportfs -v
# Should show: /mnt/sdcard/security_camera/security_footage

# Check directory structure
tree /mnt/sdcard/security_camera/security_footage
# Should show all 4 cameras with subdirectories

# Check disk space
df -h /mnt/sdcard
# Should show available space on SSD
```

- [ ] NFS service is active
- [ ] Exports are configured
- [ ] Directory structure exists
- [ ] Sufficient disk space available

## Phase 2: Camera Client Testing

Pick ONE camera to test with initially.

### Camera Preparation
- [ ] Camera is on same network (192.168.1.0/24)
- [ ] Camera can ping central server: `ping 192.168.1.26`
- [ ] NFS client installed: `sudo apt-get install -y nfs-common`

### Client-Side Test Script
Copy `test_nfs_mount.sh` to camera and run:

```bash
scp test_nfs_mount.sh pi@camera_1:/tmp/
ssh pi@camera_1
cd /tmp
chmod +x test_nfs_mount.sh
sudo ./test_nfs_mount.sh 192.168.1.26
```

Expected results:
- [ ] Network Connectivity - SUCCESS
- [ ] NFS Port Accessible - SUCCESS
- [ ] Showmount Query - SUCCESS (shows export)
- [ ] Mount Test - SUCCESS
- [ ] Read Access - SUCCESS (can list directories)
- [ ] Write Access - SUCCESS (can create file)
- [ ] Delete Access - SUCCESS (can remove file)

### Manual Camera Test
```bash
# Create mount point
sudo mkdir -p /mnt/footage

# Mount NFS share
sudo mount -t nfs 192.168.1.26:/mnt/sdcard/security_camera/security_footage /mnt/footage

# Verify mount
mountpoint /mnt/footage
# Should show: /mnt/footage is a mountpoint

# List contents
ls /mnt/footage
# Should show: camera_1  camera_2  camera_3  camera_4

# Test write (use camera_1 for testing)
sudo touch /mnt/footage/camera_1/pictures/manual_test.txt
ls /mnt/footage/camera_1/pictures/manual_test.txt
# Should show the file

# Verify on server
ssh pi@192.168.1.26 "ls /mnt/sdcard/security_camera/security_footage/camera_1/pictures/manual_test.txt"
# Should show the file exists on server

# Cleanup
sudo rm /mnt/footage/camera_1/pictures/manual_test.txt
sudo umount /mnt/footage
```

Checklist:
- [ ] Mount successful
- [ ] Can list directories
- [ ] Can create file
- [ ] File visible on server
- [ ] Can delete file
- [ ] Unmount successful

## Phase 3: Permanent Mount Configuration

On the test camera:

### Configure /etc/fstab
```bash
# Backup existing fstab
sudo cp /etc/fstab /etc/fstab.backup

# Add NFS mount
echo "192.168.1.26:/mnt/sdcard/security_camera/security_footage /mnt/footage nfs _netdev,soft,timeo=10,retrans=3,nofail 0 0" | sudo tee -a /etc/fstab

# Create mount point
sudo mkdir -p /mnt/footage

# Test mount
sudo mount -a

# Verify
mountpoint /mnt/footage
```

- [ ] Added entry to /etc/fstab
- [ ] Entry includes `nofail` option
- [ ] Mount successful with `mount -a`
- [ ] Mount persists after reboot

### Resilience Test
```bash
# On camera, reboot while server is running
sudo reboot

# After reboot, check mount
mountpoint /mnt/footage
# Should be mounted
```

- [ ] Camera boots successfully
- [ ] Mount is active after boot

### Failure Resilience Test
```bash
# On central server, stop NFS
sudo systemctl stop nfs-kernel-server

# On camera, reboot
sudo reboot

# After reboot
# Camera should boot successfully (not hang)
# Check boot time (should be < 2 minutes)

# On server, start NFS again
sudo systemctl start nfs-kernel-server

# On camera, try mount
sudo mount /mnt/footage
# Should succeed
```

- [ ] Camera boots even with server down
- [ ] Boot doesn't hang (< 2 minutes)
- [ ] Mount works when server comes back

## Phase 4: Multi-Camera Rollout

After successful test with one camera, configure remaining cameras:

### Camera 2
- [ ] Installed nfs-common
- [ ] Added /etc/fstab entry
- [ ] Created /mnt/footage
- [ ] Mounted successfully
- [ ] Write test successful
- [ ] Reboot test successful

### Camera 3
- [ ] Installed nfs-common
- [ ] Added /etc/fstab entry
- [ ] Created /mnt/footage
- [ ] Mounted successfully
- [ ] Write test successful
- [ ] Reboot test successful

### Camera 4
- [ ] Installed nfs-common
- [ ] Added /etc/fstab entry
- [ ] Created /mnt/footage
- [ ] Mounted successfully
- [ ] Write test successful
- [ ] Reboot test successful

## Phase 5: System Integration Test

### Simultaneous Write Test
From each camera, write a test file:

```bash
# On camera_1
sudo touch /mnt/footage/camera_1/pictures/test_camera1.txt

# On camera_2
sudo touch /mnt/footage/camera_2/pictures/test_camera2.txt

# On camera_3
sudo touch /mnt/footage/camera_3/pictures/test_camera3.txt

# On camera_4
sudo touch /mnt/footage/camera_4/pictures/test_camera4.txt

# On server, verify all files
ls /mnt/sdcard/security_camera/security_footage/camera_*/pictures/test_*.txt
# Should show all 4 files
```

- [ ] All 4 cameras can write simultaneously
- [ ] No errors or conflicts
- [ ] All files appear on server

### Cleanup Test Files
```bash
# On server
sudo rm /mnt/sdcard/security_camera/security_footage/camera_*/pictures/test_*.txt
```

- [ ] Test files removed

## Final Checklist

### Central Server
- [ ] NFS service enabled and running
- [ ] Exports configured correctly
- [ ] Directory structure created for 4 cameras
- [ ] Verification script passes all tests
- [ ] Disk space monitored

### All Cameras
- [ ] nfs-common installed
- [ ] /etc/fstab configured with `nofail`
- [ ] Mount point created
- [ ] Mount successful
- [ ] Can read/write/delete files
- [ ] Boots successfully even if server down

### System-Wide
- [ ] All 4 cameras can mount NFS share
- [ ] Simultaneous writes work correctly
- [ ] No permission errors
- [ ] Network performance acceptable
- [ ] Resilience verified (cameras boot without server)

## Common Issues & Solutions

### Issue: Camera hangs at boot
- **Check**: /etc/fstab has `nofail` option
- **Fix**: Edit /etc/fstab, add `nofail` to options

### Issue: Permission denied on write
- **Check**: Ownership on server
- **Fix**: `sudo chown -R pi:pi /mnt/sdcard/security_camera/security_footage`

### Issue: Mount fails
- **Check**: Server is reachable (`ping 192.168.1.26`)
- **Check**: NFS service running on server
- **Check**: Export is active (`showmount -e 192.168.1.26`)

### Issue: Stale file handle
- **Fix**: Unmount and remount: `sudo umount -f /mnt/footage && sudo mount /mnt/footage`

## Success Criteria

You can proceed to the next session when:

✅ Central server NFS is running and verified  
✅ All 4 cameras can mount the share  
✅ All 4 cameras can read/write/delete files  
✅ Cameras boot successfully even when server is down  
✅ No errors in NFS logs  
✅ Adequate disk space available  

## Next Session

Once all checks pass, you're ready for:
- **Session 1A-1**: PostgreSQL Database Schema

---

**Status**: [ ] Not Started  |  [ ] In Progress  |  [ ] Complete

**Notes**:
_Use this space to document any issues or observations during testing_