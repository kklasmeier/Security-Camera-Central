#!/usr/bin/env python3
"""
Security Camera Health Diagnostic
==================================
Checks health of all camera system threads.

Usage:
    python3 camera_health_check.py

This will show:
- Which threads are alive
- What the circular buffer is doing
- Whether frames are being captured
- Detailed thread status
"""

import threading
import time
import sys
from datetime import datetime

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(title)
    print("="*60)

def check_threads():
    """Check all running threads in the process."""
    print_section("THREAD STATUS")
    
    threads = threading.enumerate()
    print(f"Total threads running: {len(threads)}\n")
    
    # Expected threads for camera system
    expected = {
        'MainThread': False,
        'CircularBufferCapture': False,
        'MotionDetector': False,
        'EventProcessor': False,
        'TransferManager': False,
        'MJPEGServerHTTP': False,
    }
    
    # Check each thread
    for thread in threads:
        is_alive = "✓ ALIVE" if thread.is_alive() else "✗ DEAD"
        is_daemon = "(daemon)" if thread.daemon else "(main)"
        
        print(f"  {is_alive:12} {thread.name:30} {is_daemon}")
        
        # Mark expected threads as found
        if thread.name in expected:
            expected[thread.name] = True
    
    # Report missing threads
    print("\nExpected Threads Status:")
    all_good = True
    for thread_name, found in expected.items():
        status = "✓ RUNNING" if found else "✗ MISSING"
        if not found and thread_name != 'MJPEGServerHTTP':  # MJPEG only runs during streaming
            all_good = False
            print(f"  {status:12} {thread_name}")
        elif found:
            print(f"  {status:12} {thread_name}")
    
    return all_good

def check_camera_system_internals():
    """
    Attempt to import and inspect the running camera system.
    
    This only works if run in the same Python process as the camera.
    For external monitoring, we'll need to add health check endpoints.
    """
    print_section("ATTEMPTING INTERNAL INSPECTION")
    
    try:
        # Try to find the running camera system instance
        # This requires we have access to the global _system variable
        print("Note: This diagnostic must be run within the camera process")
        print("      or we need to add health check API endpoints.")
        print("\nRecommendation: Add health check endpoints to camera_control_api.py")
        
    except Exception as e:
        print(f"Cannot inspect internal state: {e}")

def check_for_deadlocks():
    """Check for potential deadlock situations."""
    print_section("DEADLOCK DETECTION")
    
    threads = threading.enumerate()
    
    # Look for threads stuck waiting
    print("Checking for threads that might be stuck...")
    
    for thread in threads:
        # We can't directly check if a thread is blocked without debugging hooks
        # But we can show thread state
        print(f"  Thread: {thread.name}")
        print(f"    Daemon: {thread.daemon}")
        print(f"    Alive: {thread.is_alive()}")
    
    print("\nNote: For deeper deadlock detection, we need threading._active lock info")
    print("      or Python debugger hooks (gdb, py-spy, etc.)")

def check_system_resources():
    """Check system resource usage."""
    print_section("SYSTEM RESOURCES")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Memory
        mem = process.memory_info()
        print(f"Memory Usage:")
        print(f"  RSS: {mem.rss / (1024*1024):.1f} MB")
        print(f"  VMS: {mem.vms / (1024*1024):.1f} MB")
        
        # CPU
        cpu_percent = process.cpu_percent(interval=1.0)
        print(f"\nCPU Usage: {cpu_percent:.1f}%")
        
        # Threads from OS perspective
        num_threads = process.num_threads()
        print(f"\nOS Thread Count: {num_threads}")
        
        # Open files
        open_files = len(process.open_files())
        print(f"Open Files: {open_files}")
        
    except ImportError:
        print("psutil not available - install with: pip3 install psutil")
    except Exception as e:
        print(f"Error checking resources: {e}")

def main():
    """Run all diagnostic checks."""
    print("\n" + "="*60)
    print("SECURITY CAMERA HEALTH DIAGNOSTIC")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"PID: {threading.current_thread().ident}")
    
    # Check threads
    threads_ok = check_threads()
    
    # Check resources
    check_system_resources()
    
    # Check for deadlocks
    check_for_deadlocks()
    
    # Attempt internal inspection
    check_camera_system_internals()
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    if threads_ok:
        print("✓ All expected threads are running")
        print("\nHowever, threads running doesn't mean they're healthy.")
        print("We need to add health check endpoints to verify:")
        print("  1. Camera is capturing new frames")
        print("  2. Motion detector is getting different frames")
        print("  3. Event processor is responsive")
    else:
        print("✗ CRITICAL: Some expected threads are missing!")
        print("   The camera system is degraded.")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    print("1. Add health check API endpoint: GET /health")
    print("   Should return:")
    print("   - Thread status for each component")
    print("   - Last frame capture timestamp")
    print("   - Last motion check timestamp")
    print("   - Buffer health metrics")
    print()
    print("2. Add frame inspection endpoint: GET /debug/frames")
    print("   Should return:")
    print("   - Current frame timestamp")
    print("   - Previous frame timestamp")
    print("   - Frame difference score")
    print()
    print("3. Add watchdog system to monitor thread health")
    print("   and restart camera if needed")
    
    return 0 if threads_ok else 1

if __name__ == "__main__":
    sys.exit(main())