# NFS Server Configuration for Security Camera System

## Overview

This guide covers the setup of Network File System (NFS) on the central Raspberry Pi 4 server to provide shared storage for 4+ camera agents (Raspberry Pi Zero 2W). The NFS share allows cameras to transfer captured images and videos to centralized storage on an external SSD.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Central Server (Pi 4)                     │
│                    IP: 192.168.1.26                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  NFS Server                                         │    │
│  │  Export: /mnt/sdcard/security_camera/               │    │
│  │         security_footage/                           │    │
│  │                                                      │    │
│  │  Storage: External SSD (938GB)                      │    │
│  │  Mounted at: /mnt/sdcard                           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ NFS Export (192.168.1.0/24)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │Camera 1 │         │Camera 2 │         │Camera 4 │
   │Pi Zero  │         │Pi Zero  │    ...  │Pi Zero  │
   │  2W     │         │  2W     │         │  2W     │
   └─────────┘         └─────────┘         └─────────┘
   WiFi Clients        WiFi Clients        WiFi Clients
   Mount: /mnt/footage
```

## Directory Structure

```
/mnt/sdcard/security_camera/security_footage/
├── camera_1/
│   ├── videos/      # H.264 and MP4 video files
│   ├── pictures/    # Motion detection images (A & B)
│   └── thumbs/      # Video thumbnails
├── camera_2/
│   ├── videos/
│   ├── pictures/
│   └── thumbs/
├── camera_3/
│   ├── videos/
│   ├── pictures/
│   └── thumbs/
└── camera_4/
    ├── videos/
    ├── pictures/
    └── thumbs/
```

**Design Rationale:**
- **Camera-based organization**: Easy to identify which camera generated which files
- **Type-based subdirectories**: Matches database schema (image_a_path, video_h264_path, etc.)
- **Scalable**: Simple to add camera_5, camera_6, etc.
- **Web-friendly**: URL structure: `/footage/camera_1/pictures/42_image_a.jpg`

## Prerequisites

### Hardware Requirements
- **Central Server**: Raspberry Pi 4 (any RAM size)
- **Storage**: External SSD mounted at `/mnt/sdcard` (already configured)
- **Network**: All devices on same subnet (192.168.1.0/24)
- **Static IP**: Central server should have static IP: 192.168.1.26

### Software Requirements
- **OS**: Raspberry Pi OS (Bookworm or later)
- **User**: Standard `pi` user
- **Sudo access**: Required for installation

### Network Requirements
- All cameras and central server on same local network
- Central server reachable from all cameras
- No firewall blocking NFS ports (2049, 111)

## Installation

### Quick Start

1. **Download the setup scripts** (to central server):
   ```bash
   cd /home/pi/Security-Camera-Central
   # Scripts should be in this directory:
   # - setup_nfs.sh
   # - verify_nfs.sh
   # - add_camera.sh
   # - test_nfs_mount.sh
   ```

2. **Make scripts executable**:
   ```bash
   chmod +x setup_nfs.sh verify_nfs.sh add_camera.sh test_nfs_mount.sh
   ```

3. **Run the setup script**:
   ```bash
   sudo ./setup_nfs.sh
   ```
   
   The script will:
   - Install NFS server package
   - Create directory structure on SSD
   - Configure NFS exports
   - Enable and start NFS service
   - Run verification checks

4. **Verify the setup**:
   ```bash
   sudo ./verify_nfs.sh
   ```
   
   Expected output: All tests should PASS

5. **Test from a camera** (optional, but recommended):
   ```bash
   # SSH into a camera, then run:
   sudo ./test_nfs_mount.sh 192.168.1.26
   ```

### Manual Installation (if needed)

If you prefer manual installation:

```bash
# 1. Install NFS server
sudo apt-get update
sudo apt-get install -y nfs-kernel-server

# 2. Create directory structure
sudo mkdir -p /mnt/sdcard/security_camera/security_footage
for camera in camera_1 camera_2 camera_3 camera_4; do
    sudo mkdir -p /mnt/sdcard/security_camera/security_footage/$camera/{videos,pictures,thumbs}
done

# 3. Set ownership and permissions
sudo chown -R pi:pi /mnt/sdcard/security_camera/security_footage
sudo chmod -R 755 /mnt/sdcard/security_camera/security_footage

# 4. Add export to /etc/exports
echo "/mnt/sdcard/security_camera/security_footage 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# 5. Apply exports
sudo exportfs -ra

# 6. Enable and start service
sudo systemctl enable nfs-kernel-server
sudo systemctl start nfs-kernel-server
```

## Configuration Details

### NFS Export Options

```
/mnt/sdcard/security_camera/security_footage 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)
```

**Option Breakdown:**

| Option | Description | Why |
|--------|-------------|-----|
| `rw` | Read-write access | Cameras need to write files |
| `sync` | Synchronous writes | Data safety (writes complete before ACK) |
| `no_subtree_check` | Disable subtree checking | Improved reliability |
| `no_root_squash` | Allow root user writes | Pi Zero cameras run as root |
| `192.168.1.0/24` | Client subnet | Restrict to local network only |

**Alternative: `async` mode**
- Faster performance (doesn't wait for disk sync)
- Risk of data loss if server crashes during write
- **NOT recommended** for security footage (reliability > speed)

### File Permissions

- **Owner**: `pi:pi` (standard Raspberry Pi user)
- **Directory mode**: `755` (rwxr-xr-x)
  - Owner: read, write, execute
  - Group: read, execute
  - Others: read, execute
- **File mode**: `644` (rw-r--r--) - set by camera when creating files
  - Owner: read, write
  - Group: read
  - Others: read

### Network Ports

NFS uses the following ports:
- **2049** (TCP/UDP): Main NFS port
- **111** (TCP/UDP): RPC portmapper
- **Ephemeral ports**: For mount daemon

**Firewall**: Raspberry Pi OS has no firewall by default (iptables inactive). If you enable a firewall later:

```bash
sudo ufw allow from 192.168.1.0/24 to any port nfs
sudo ufw allow from 192.168.1.0/24 to any port 111
```

## Client Configuration (Cameras)

### Installing NFS Client on Camera

Each camera needs the NFS client package:

```bash
# Run on each Pi Zero camera
sudo apt-get update
sudo apt-get install -y nfs-common
```

### Testing Mount (One-Time)

Before configuring permanent mount, test it:

```bash
# On camera
sudo mkdir -p /mnt/footage
sudo mount -t nfs 192.168.1.26:/mnt/sdcard/security_camera/security_footage /mnt/footage

# Verify
ls /mnt/footage
# Should show: camera_1  camera_2  camera_3  camera_4

# Test write
sudo touch /mnt/footage/camera_1/pictures/test.txt
ls /mnt/footage/camera_1/pictures/

# Cleanup
sudo rm /mnt/footage/camera_1/pictures/test.txt
sudo umount /mnt/footage
```

### Permanent Mount (Resilient Boot)

**Goal**: Camera boots even if NFS server is unavailable, then attempts to mount.

#### Method 1: Using /etc/fstab (Recommended)

Add to `/etc/fstab` on each camera:

```bash
192.168.1.26:/mnt/sdcard/security_camera/security_footage /mnt/footage nfs _netdev,soft,timeo=10,retrans=3,nofail 0 0
```

**Options explained:**
- `_netdev`: Wait for network before attempting mount
- `soft`: Return error if server unavailable (don't hang)
- `timeo=10`: 1 second timeout (10 × 0.1s)
- `retrans=3`: Retry 3 times before giving up
- `nofail`: **CRITICAL** - boot continues even if mount fails

Apply changes:
```bash
sudo mkdir -p /mnt/footage
sudo mount -a
```

#### Method 2: Systemd Mount Retry Service

For additional resilience, create a systemd service that retries mount at boot:

**File**: `/etc/systemd/system/nfs-mount-retry.service`

```ini
[Unit]
Description=Retry NFS mount for security footage
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/mount-retry.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

**File**: `/usr/local/bin/mount-retry.sh`

```bash
#!/bin/bash
# Try to mount NFS, retry up to 10 times with 5 second delay
for i in {1..10}; do
    if mountpoint -q /mnt/footage; then
        echo "NFS already mounted"
        exit 0
    fi
    mount /mnt/footage && exit 0
    sleep 5
done
echo "Failed to mount NFS after 10 attempts"
```

Make executable and enable:
```bash
sudo chmod +x /usr/local/bin/mount-retry.sh
sudo systemctl enable nfs-mount-retry.service
sudo systemctl start nfs-mount-retry.service
```

**Result:**
- ✅ Camera boots even if server is down
- ✅ Attempts mount 10 times over 50 seconds at boot
- ✅ Doesn't hang boot process
- ✅ Lazy mount on access (if fstab configured)

## Verification

### On Central Server

```bash
# Check NFS service status
sudo systemctl status nfs-kernel-server

# Check active exports
sudo exportfs -v

# Check showmount
showmount -e localhost

# Check directory structure
tree /mnt/sdcard/security_camera/security_footage/

# Check disk space
df -h /mnt/sdcard
```

### On Camera

```bash
# Check if mounted
mountpoint /mnt/footage

# List contents
ls /mnt/footage

# Check mount options
mount | grep footage

# Test write
sudo touch /mnt/footage/camera_1/pictures/test.txt
ls /mnt/footage/camera_1/pictures/test.txt
sudo rm /mnt/footage/camera_1/pictures/test.txt
```

### Using Verification Scripts

**On central server:**
```bash
sudo ./verify_nfs.sh
```

**On camera:**
```bash
sudo ./test_nfs_mount.sh 192.168.1.26
```

## Troubleshooting

### Problem: NFS service won't start

**Symptoms:**
```bash
sudo systemctl status nfs-kernel-server
# Shows: failed or inactive
```

**Solutions:**
1. Check logs: `sudo journalctl -u nfs-kernel-server -n 50`
2. Verify exports syntax: `sudo exportfs -v`
3. Check for typos in `/etc/exports`
4. Restart service: `sudo systemctl restart nfs-kernel-server`

### Problem: Camera can't mount (connection refused)

**Symptoms:**
```bash
sudo mount -t nfs 192.168.1.26:/mnt/sdcard/security_camera/security_footage /mnt/footage
# Error: Connection refused
```

**Solutions:**
1. Verify server is reachable: `ping 192.168.1.26`
2. Check NFS service: `ssh pi@192.168.1.26 "sudo systemctl status nfs-kernel-server"`
3. Verify export: `showmount -e 192.168.1.26`
4. Check firewall (if enabled): `sudo iptables -L -n`

### Problem: Permission denied when writing

**Symptoms:**
```bash
touch /mnt/footage/camera_1/pictures/test.txt
# Error: Permission denied
```

**Solutions:**
1. Check ownership on server:
   ```bash
   ls -la /mnt/sdcard/security_camera/security_footage/camera_1/
   # Should show: pi pi
   ```
2. Fix ownership if needed:
   ```bash
   sudo chown -R pi:pi /mnt/sdcard/security_camera/security_footage
   ```
3. Check export options include `no_root_squash`: `sudo exportfs -v`

### Problem: Mount hangs at boot

**Symptoms:**
- Camera takes 90+ seconds to boot
- Boot seems to hang at "A start job is running..."

**Solutions:**
1. Add `nofail` to `/etc/fstab` mount options (CRITICAL)
2. Add `_netdev` to wait for network
3. Use systemd mount retry service instead
4. Check boot logs: `sudo journalctl -b`

### Problem: Stale file handle

**Symptoms:**
```bash
ls /mnt/footage
# Error: Stale file handle
```

**Solutions:**
1. Unmount: `sudo umount -f /mnt/footage`
2. Remount: `sudo mount /mnt/footage`
3. If still fails, reboot camera
4. On server, check NFS status and restart if needed

### Problem: Camera not writing to correct directory

**Symptoms:**
- Camera tries to write but files don't appear on server

**Solutions:**
1. Verify mount is active: `mountpoint /mnt/footage`
2. Check camera configuration has correct camera_id
3. Verify directory exists: `ls /mnt/footage/camera_1/pictures/`
4. Test write manually: `sudo touch /mnt/footage/camera_1/pictures/test.txt`

## Performance Considerations

### Network Bandwidth

- **Typical event**: ~50MB (2 images @ 5MB each + video @ 40MB)
- **4 cameras**: Can burst simultaneously (~200MB total)
- **WiFi 5GHz**: ~50-100 Mbps typical (sufficient)
- **WiFi 2.4GHz**: ~10-20 Mbps typical (may be slow if 4 cameras write simultaneously)

**Recommendations:**
- Use 5GHz WiFi for cameras if available (less congestion)
- Consider wired Ethernet for central server
- Cameras write sequentially within an event (not all at once)

### Disk Performance

- **SSD**: ~100-200 MB/s write speed (plenty fast)
- **SD card**: ~10-20 MB/s write speed (avoid for footage)
- **NFS overhead**: ~10-20% (acceptable for local network)

### Storage Capacity

**Current setup:**
- SSD size: 938GB
- Available: 310GB (as of documentation)

**Estimated usage:**
- 4 cameras × 10 events/day × 50MB/event = ~2GB/day
- 310GB available = ~155 days of footage
- After 5 months, oldest footage should be purged (implement cleanup job)

## Maintenance

### Regular Tasks

**Daily:**
- None required (service runs automatically)

**Weekly:**
- Check disk space: `df -h /mnt/sdcard`
- Verify mounts on cameras: `for i in {1..4}; do ssh pi@camera_$i "mountpoint /mnt/footage"; done`

**Monthly:**
- Check NFS logs: `sudo journalctl -u nfs-kernel-server -n 100`
- Verify exports: `sudo exportfs -v`

### Monitoring Disk Space

Create a cron job to alert when disk space is low:

```bash
# Add to crontab: crontab -e
0 2 * * * /home/pi/check_disk_space.sh
```

**Script**: `/home/pi/check_disk_space.sh`
```bash
#!/bin/bash
THRESHOLD=90
USAGE=$(df -h /mnt/sdcard | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "ALERT: Disk usage is ${USAGE}% (threshold: ${THRESHOLD}%)" | \
        mail -s "NFS Storage Alert" pi@localhost
fi
```

### Cleanup Old Footage

Create a cleanup script to remove footage older than 30 days:

**Script**: `/home/pi/cleanup_footage.sh`
```bash
#!/bin/bash
FOOTAGE_DIR="/mnt/sdcard/security_camera/security_footage"
DAYS_TO_KEEP=30

# Find and delete files older than 30 days
find "$FOOTAGE_DIR" -type f -mtime +$DAYS_TO_KEEP -delete

echo "Cleanup complete: Removed footage older than $DAYS_TO_KEEP days"
```

**Add to crontab:**
```bash
# Run daily at 3 AM
0 3 * * * /home/pi/cleanup_footage.sh >> /var/log/footage_cleanup.log 2>&1
```

## Adding More Cameras

### Using the Helper Script

```bash
sudo ./add_camera.sh camera_5
```

This will:
- Create `camera_5/videos`, `camera_5/pictures`, `camera_5/thumbs`
- Set correct ownership (pi:pi)
- Set correct permissions (755)

### Manual Method

```bash
cd /mnt/sdcard/security_camera/security_footage
sudo mkdir -p camera_5/{videos,pictures,thumbs}
sudo chown -R pi:pi camera_5
sudo chmod -R 755 camera_5
```

**No NFS configuration changes needed** - the entire directory is already exported.

## Future Expansion

### Replacing SSD with Larger Drive

If you need more storage:

1. Connect new drive to Pi 4
2. Format: `sudo mkfs.ext4 /dev/sdb1` (adjust device as needed)
3. Get UUID: `sudo blkid /dev/sdb1`
4. Update `/etc/fstab`:
   ```
   UUID=xxxx-xxxx /mnt/sdcard ext4 defaults,nofail 0 2
   ```
5. Copy data: `sudo rsync -av /mnt/sdcard/ /mnt/new_drive/`
6. Unmount old, mount new
7. Reboot and verify

**No NFS changes needed** - NFS exports the mount point, not the underlying device.

### Adding External USB Drive for Archives

Keep recent footage on SSD, archive old footage:

```bash
# Mount archive drive
sudo mkdir -p /mnt/archive
# Add to /etc/fstab...

# Create archive script
#!/bin/bash
# Move footage older than 90 days to archive
find /mnt/sdcard/security_camera/security_footage -type f -mtime +90 \
    -exec mv {} /mnt/archive/ \;
```

## Security Considerations

### Current Security Model

- **Network isolation**: Only local subnet (192.168.1.0/24) can access
- **No authentication**: NFS trusts network-level security
- **No encryption**: Data transferred in plaintext on local network

**This is appropriate for:**
- Home/local network deployments
- Trusted LAN environments
- Non-sensitive footage (home security, not financial/medical)

### Not Recommended For:

- Internet-facing deployments
- Multi-tenant environments
- Highly sensitive footage

### Additional Security (if needed)

**Option 1: IPsec/VPN**
- Encrypt NFS traffic over VPN tunnel
- Requires IPsec configuration on Pi devices

**Option 2: SSH Tunnel**
- Mount NFS over SSH tunnel
- Higher overhead, more complex

**Option 3: NFSv4 with Kerberos**
- Add authentication layer
- Significantly more complex setup

**For most home use cases, the current security model is sufficient.**

## Support and Troubleshooting

### Log Files

**NFS Server logs:**
```bash
sudo journalctl -u nfs-kernel-server -f  # Follow logs
sudo journalctl -u nfs-kernel-server -n 100  # Last 100 lines
```

**System logs:**
```bash
sudo dmesg | grep nfs
sudo cat /var/log/syslog | grep nfs
```

### Useful Commands

```bash
# Show all active mounts
showmount -a

# Reload exports without restarting
sudo exportfs -ra

# Restart NFS server
sudo systemctl restart nfs-kernel-server

# Check NFS statistics
nfsstat

# Force unmount (if stuck)
sudo umount -f /mnt/footage
```

### Getting Help

If you encounter issues not covered here:

1. Check logs first (see above)
2. Verify network connectivity
3. Test with simple mount command
4. Check Raspberry Pi forums
5. Review NFS documentation: `man nfs`, `man exports`

## Summary Checklist

### Central Server Setup

- [ ] SSD mounted at `/mnt/sdcard`
- [ ] NFS server package installed
- [ ] Directory structure created
- [ ] Exports configured
- [ ] NFS service running
- [ ] Verification script passes

### Camera Setup (for each camera)

- [ ] NFS client installed (`nfs-common`)
- [ ] Mount point created (`/mnt/footage`)
- [ ] `/etc/fstab` entry added (with `nofail`)
- [ ] Mount successful
- [ ] Write test successful
- [ ] Mount retry service enabled (optional)

### Testing

- [ ] Camera can read directory listing
- [ ] Camera can create files
- [ ] Camera can delete files
- [ ] Server shows files created by camera
- [ ] Camera boots successfully with server down
- [ ] Mount recovers when server comes back

## Conclusion

Your NFS server is now configured to provide reliable, high-performance shared storage for your multi-camera security system. The resilient mount configuration ensures cameras can boot and operate even when the central server is temporarily unavailable.

**Next Steps:**
- Proceed to Session 1A-1 (PostgreSQL Database Schema)
- Configure camera agents (Session 1B) to use this NFS share
- Test end-to-end file transfer workflow

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-28  
**System Version:** Phase 1A - Central Server Foundation