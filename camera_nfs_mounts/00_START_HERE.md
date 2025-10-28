# Session 1A-2: NFS Server Configuration - START HERE 📁

## 🎯 Quick Overview

This session provides **complete NFS server setup** for your security camera system. You've received **8 files** that will configure shared storage on your Raspberry Pi 4 central server.

## 📦 What You Got

### 🔧 Executable Scripts (4)
1. **setup_nfs.sh** - Run this first! Automated installation
2. **verify_nfs.sh** - Run this second! Verify everything works
3. **test_nfs_mount.sh** - Run from cameras to test mounting
4. **add_camera.sh** - Add more cameras later (camera_5, camera_6, etc.)

### 📖 Documentation (4)
5. **QUICK_START.md** - ⭐ **Read this first!** Fast installation guide
6. **README_nfs.md** - Complete reference documentation
7. **TESTING_CHECKLIST.md** - Step-by-step testing guide
8. **SESSION_COMPLETE.md** - Session summary and next steps

## 🚀 Quick Start (5 Minutes)

### Step 1: Copy Files to Your Pi 4
```bash
# Transfer all files to your central server
# Target location: /home/pi/Security-Camera-Central/
```

### Step 2: Make Scripts Executable
```bash
cd /home/pi/Security-Camera-Central
chmod +x *.sh
```

### Step 3: Run Setup
```bash
sudo ./setup_nfs.sh
```

This will:
- ✅ Install NFS server
- ✅ Create directory structure on your SSD
- ✅ Configure exports for your subnet
- ✅ Start and enable the service

### Step 4: Verify
```bash
sudo ./verify_nfs.sh
```

Expected: **All 10 tests PASS** ✅

### Step 5: Test from a Camera (Optional)
```bash
# Copy test script to a camera
scp test_nfs_mount.sh pi@camera_1:/tmp/

# SSH to camera and run
ssh pi@camera_1
cd /tmp
chmod +x test_nfs_mount.sh
sudo ./test_nfs_mount.sh 192.168.1.26
```

Expected: **All tests pass** ✅

## 📋 Which File to Read First?

**If you want to get started immediately:**
→ Read **QUICK_START.md**

**If you want complete documentation:**
→ Read **README_nfs.md**

**If you want step-by-step testing:**
→ Read **TESTING_CHECKLIST.md**

**If you want to know what was built:**
→ Read **SESSION_COMPLETE.md**

## 🎯 What This Does

Creates shared storage on your SSD that all 4 cameras can access:

```
Central Server (192.168.1.26)
    └── SSD: /mnt/sdcard/security_camera/security_footage/
            ├── camera_1/ (videos, pictures, thumbs)
            ├── camera_2/ (videos, pictures, thumbs)
            ├── camera_3/ (videos, pictures, thumbs)
            └── camera_4/ (videos, pictures, thumbs)

Each camera will mount this as: /mnt/footage
```

## ⚙️ Key Configuration

- **Central Server IP**: 192.168.1.26
- **Storage Path**: `/mnt/sdcard/security_camera/security_footage/`
- **Subnet**: 192.168.1.0/24
- **User**: pi (all machines)
- **SSD Size**: 938GB (310GB available)

## ✨ Special Features

1. **Resilient Boot**: Cameras boot even if server is down
2. **Automatic Retry**: Attempts to reconnect when server comes back
3. **SSD Storage**: Avoids SD card wear on Pi 4
4. **Scalable**: Easy to add camera_5, camera_6, etc.

## 🧪 Success Criteria

You're done when:
- ✅ `sudo ./verify_nfs.sh` shows all tests pass
- ✅ Camera can mount: `mountpoint /mnt/footage`
- ✅ Camera can write: `touch /mnt/footage/camera_1/pictures/test.txt`
- ✅ Camera boots successfully even when server is off

## 🔍 Troubleshooting

**Can't mount from camera?**
```bash
ping 192.168.1.26                    # Test connectivity
showmount -e 192.168.1.26            # Check exports
sudo systemctl status nfs-kernel-server  # Check service
```

**Permission denied?**
```bash
sudo chown -R pi:pi /mnt/sdcard/security_camera/security_footage
sudo chmod -R 755 /mnt/sdcard/security_camera/security_footage
```

**More help?** See **README_nfs.md** troubleshooting section

## 📁 File Descriptions

| File | Purpose | When to Use |
|------|---------|-------------|
| **QUICK_START.md** | Fast installation guide | Start here! |
| **setup_nfs.sh** | Automated setup | Run on Pi 4 |
| **verify_nfs.sh** | Test configuration | After setup |
| **test_nfs_mount.sh** | Test from camera | On each camera |
| **add_camera.sh** | Add new cameras | When expanding |
| **README_nfs.md** | Complete docs | Reference |
| **TESTING_CHECKLIST.md** | Testing guide | Methodical testing |
| **SESSION_COMPLETE.md** | Session summary | Review what was built |

## 🎬 Next Steps

After NFS is working:

1. **Immediate Next**: Session 1A-1 (PostgreSQL Database Schema)
2. **Or**: Session 1A-3 (FastAPI Application Structure)
3. **Later**: Session 1B (Camera Agent Refactor to use this NFS mount)

## 💡 Pro Tips

1. **Always run verify_nfs.sh** after making any changes
2. **Test with one camera first** before configuring all 4
3. **Check disk space regularly**: `df -h /mnt/sdcard`
4. **The `nofail` option is critical** - don't remove it from fstab
5. **Keep backups** of your /etc/fstab before editing

## 📞 Support

All troubleshooting information is in:
- **README_nfs.md** - Comprehensive troubleshooting section
- **TESTING_CHECKLIST.md** - Common issues and solutions

## 🎉 Ready to Begin?

**Start here**: Open **QUICK_START.md** and follow the steps!

---

**Session 1A-2: NFS Server Configuration**  
**Status**: Ready for Deployment ✅  
**Files**: 8 deliverables  
**Estimated Setup Time**: 10-15 minutes  
**Difficulty**: Low  

**Let's get your shared storage working!** 🚀