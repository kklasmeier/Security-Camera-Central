#!/usr/bin/env python3
"""
EMERGENCY DIAGNOSTIC - Camera Frame Capture Check
==================================================
Run this on the stuck camera to diagnose frame capture issues.

This script does NOT require the camera system to be running.
It directly inspects system state.

Usage:
    python3 emergency_diagnostic.py

What it checks:
1. Are Python threads still alive?
2. Is the camera device accessible?
3. Can we capture a test frame?
4. What's using system resources?
"""

import subprocess
import sys
import os
from datetime import datetime

def print_header(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def check_process_threads():
    """Check threads of the running camera process."""
    print_header("PROCESS THREAD CHECK")
    
    try:
        # Find the camera process
        result = subprocess.run(
            ['pgrep', '-f', 'sec_cam_main.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("✗ Camera process not running!")
            return None
        
        pid = result.stdout.strip().split('\n')[0]
        print(f"✓ Camera process found: PID {pid}")
        
        # Get thread count
        result = subprocess.run(
            ['ps', '-T', '-p', pid],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            thread_count = len(lines) - 1  # Subtract header
            print(f"  Thread count: {thread_count}")
            print("\nThread details:")
            print(result.stdout)
        
        # Get stack traces of all threads
        print("\nAttempting to get thread stack traces...")
        try:
            import gdb
            print("  Note: Requires gdb and py-bt (python debugging symbols)")
        except:
            print("  Note: Install py-spy for thread stack traces:")
            print("    pip3 install py-spy")
            print("    sudo py-spy dump --pid", pid)
        
        return pid
        
    except Exception as e:
        print(f"✗ Error checking process: {e}")
        return None

def check_camera_device():
    """Check if camera device is accessible."""
    print_header("CAMERA DEVICE CHECK")
    
    try:
        # Check for camera device
        result = subprocess.run(
            ['vcgencmd', 'get_camera'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"Camera status: {result.stdout.strip()}")
            
            # Check if detected
            if "detected=1" in result.stdout:
                print("✓ Camera detected by system")
            else:
                print("✗ Camera NOT detected by system")
                print("  Try: sudo reboot")
                return False
                
            # Check if supported
            if "supported=1" in result.stdout:
                print("✓ Camera supported")
            else:
                print("✗ Camera not supported")
                return False
        else:
            print("✗ Could not query camera status")
            return False
        
        # Check video devices
        print("\nVideo devices:")
        if os.path.exists('/dev/video0'):
            print("✓ /dev/video0 exists")
        else:
            print("✗ /dev/video0 missing")
        
        # List all video devices
        result = subprocess.run(
            ['ls', '-l', '/dev/video*'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(result.stdout)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ Camera check timed out - possible hardware hang")
        return False
    except Exception as e:
        print(f"✗ Error checking camera: {e}")
        return False

def test_camera_capture():
    """Try to capture a test frame."""
    print_header("TEST CAMERA CAPTURE")
    
    print("Attempting to capture test frame...")
    print("(This will FAIL if camera is in use by the main process)")
    
    try:
        from picamera2 import Picamera2
        import time
        
        print("Initializing camera...")
        picam2 = Picamera2()
        
        print("Configuring camera...")
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam2.configure(config)
        
        print("Starting camera...")
        picam2.start()
        
        print("Waiting 2 seconds for camera to stabilize...")
        time.sleep(2)
        
        print("Capturing frame...")
        frame = picam2.capture_array()
        
        print(f"✓ Test capture successful!")
        print(f"  Frame shape: {frame.shape}")
        print(f"  Frame dtype: {frame.dtype}")
        
        picam2.stop()
        picam2.close()
        
        return True
        
    except RuntimeError as e:
        if "Camera is in use" in str(e) or "already open" in str(e):
            print("✓ Camera is in use (expected - camera process has it locked)")
            print("  This means the camera device itself is working")
            print("  The issue is likely in the frame capture THREAD")
            return True
        else:
            print(f"✗ Camera error: {e}")
            return False
    except Exception as e:
        print(f"✗ Test capture failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_system_resources():
    """Check system resource usage."""
    print_header("SYSTEM RESOURCES")
    
    try:
        # Memory
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        print("Memory:")
        print(result.stdout)
        
        # Temperature
        result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\nTemperature: {result.stdout.strip()}")
        
        # Throttling status
        result = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Throttling: {result.stdout.strip()}")
            throttled = result.stdout.strip()
            if "throttled=0x0" in throttled:
                print("✓ No throttling detected")
            else:
                print("⚠ WARNING: System has been throttled!")
                print("  This can cause camera issues")
        
        # Disk space
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        print("\nDisk space:")
        print(result.stdout)
        
        # Top processes by memory
        result = subprocess.run(
            ['ps', 'aux', '--sort=-rss'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')[:10]  # Top 10
            print("\nTop processes by memory:")
            print('\n'.join(lines))
        
    except Exception as e:
        print(f"Error checking resources: {e}")

def check_camera_api():
    """Check if camera API is responsive."""
    print_header("CAMERA API CHECK")
    
    try:
        import requests
        
        print("Checking camera API endpoints...")
        
        # Try health endpoint (if implemented)
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            print(f"✓ Health endpoint: {response.status_code}")
            print(f"  Response: {response.json()}")
        except requests.exceptions.ConnectionError:
            print("⚠ Health endpoint not available (not implemented yet)")
        except Exception as e:
            print(f"✗ Health endpoint error: {e}")
        
        # Try status endpoint
        try:
            response = requests.get('http://localhost:5000/status', timeout=5)
            print(f"✓ Status endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"  Response: {response.json()}")
        except Exception as e:
            print(f"⚠ Status endpoint: {e}")
        
    except ImportError:
        print("Note: requests module not available")
        print("Install with: pip3 install requests")

def main():
    print("\n" + "="*60)
    print("EMERGENCY DIAGNOSTIC - Camera Frame Capture")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Hostname: {subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()}")
    
    # Run all checks
    pid = check_process_threads()
    camera_ok = check_camera_device()
    check_system_resources()
    
    if camera_ok:
        test_camera_capture()
    
    check_camera_api()
    
    # Summary and recommendations
    print_header("DIAGNOSTIC SUMMARY")
    
    if pid is None:
        print("✗ CRITICAL: Camera process is not running")
        print("\nRecommendations:")
        print("  1. Check systemd status: sudo systemctl status security-camera-agent")
        print("  2. Check logs: journalctl -u security-camera-agent -n 100")
        print("  3. Try restarting: sudo systemctl restart security-camera-agent")
    else:
        print("✓ Camera process is running")
        print("\nBased on your earlier logs showing score=0/50 consistently:")
        print("  This suggests the CircularBufferCapture thread has STOPPED")
        print("  updating frames, even though the thread is technically alive.")
        print("\nMost likely causes:")
        print("  1. Camera hardware locked up (requires camera restart)")
        print("  2. Thread is stuck in a blocking call")
        print("  3. Exception was caught but thread entered invalid state")
        print("\nRecommendations:")
        print("  1. Restart the service: sudo systemctl restart security-camera-agent")
        print("  2. Add health check endpoint to detect this automatically")
        print("  3. Implement camera watchdog to auto-restart on frame stall")
        print("  4. Check for camera thermal throttling or power issues")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Implement health check endpoint (see health_checker.py)")
    print("2. Add camera watchdog (auto-restart on stall)")
    print("3. Monitor for:")
    print("   - Frame capture timestamps")
    print("   - Thread liveness")
    print("   - Camera device errors")

if __name__ == "__main__":
    main()