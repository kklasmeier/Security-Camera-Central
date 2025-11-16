#!/usr/bin/env python3
"""
Real-time Thread Monitor
========================
Continuously monitors camera system threads.

Usage:
    python3 thread_monitor.py [PID]
    
If PID not provided, will search for sec_cam_main.py process.

Press Ctrl+C to stop.
"""

import subprocess
import time
import sys
import signal

class ThreadMonitor:
    def __init__(self, pid):
        self.pid = pid
        self.running = True
        self.baseline_threads = None
        
        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nStopping monitor...")
        self.running = False
    
    def get_thread_info(self):
        """Get current thread information."""
        try:
            result = subprocess.run(
                ['ps', '-T', '-p', str(self.pid), '-o', 'pid,tid,comm,state,wchan:30'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # Parse threads
            threads = []
            for line in lines[1:]:  # Skip header
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    threads.append({
                        'pid': parts[0],
                        'tid': parts[1],
                        'comm': parts[2],
                        'state': parts[3],
                        'wchan': parts[4]
                    })
            
            return threads
            
        except Exception as e:
            print(f"Error getting thread info: {e}")
            return None
    
    def display_threads(self, threads, iteration):
        """Display thread information."""
        if threads is None:
            print("Process not found or error occurred")
            return
        
        # Clear screen
        print("\033[2J\033[H", end='')
        
        # Header
        print("="*80)
        print(f"Thread Monitor - PID {self.pid} - Iteration {iteration}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print(f"Total threads: {len(threads)}")
        print()
        
        # Thread table header
        print(f"{'TID':<10} {'NAME':<25} {'STATE':<8} {'WAITING ON':<30}")
        print("-"*80)
        
        # Thread details
        for thread in threads:
            tid = thread['tid']
            comm = thread['comm'][:24]
            state = thread['state']
            wchan = thread['wchan'][:29]
            
            # Color code by state
            if state == 'R':  # Running
                state_display = f"\033[92m{state}\033[0m"  # Green
            elif state == 'S':  # Sleeping (normal)
                state_display = f"\033[94m{state}\033[0m"  # Blue
            elif state == 'D':  # Uninterruptible sleep (BAD)
                state_display = f"\033[91m{state}\033[0m"  # Red
            elif state == 'Z':  # Zombie (VERY BAD)
                state_display = f"\033[91m{state}\033[0m"  # Red
            else:
                state_display = state
            
            print(f"{tid:<10} {comm:<25} {state_display:<8} {wchan:<30}")
        
        # State legend
        print()
        print("State: R=Running, S=Sleeping(normal), D=Uninterruptible(BAD), Z=Zombie(VERY BAD)")
        
        # Compare to baseline
        if self.baseline_threads is None:
            self.baseline_threads = set(t['tid'] for t in threads)
        else:
            current_tids = set(t['tid'] for t in threads)
            new_threads = current_tids - self.baseline_threads
            dead_threads = self.baseline_threads - current_tids
            
            if new_threads or dead_threads:
                print()
                if new_threads:
                    print(f"⚠ NEW threads: {new_threads}")
                if dead_threads:
                    print(f"✗ DEAD threads: {dead_threads}")
        
        # Check for stuck threads (D state or stuck in same wchan)
        stuck_threads = [t for t in threads if t['state'] == 'D']
        if stuck_threads:
            print()
            print("⚠ WARNING: Threads in uninterruptible sleep (stuck):")
            for t in stuck_threads:
                print(f"  TID {t['tid']}: {t['comm']} waiting on {t['wchan']}")
        
        print()
        print("Press Ctrl+C to stop monitoring...")
    
    def monitor(self):
        """Main monitoring loop."""
        iteration = 0
        
        while self.running:
            threads = self.get_thread_info()
            
            if threads is None:
                print(f"Process {self.pid} no longer exists or inaccessible")
                break
            
            self.display_threads(threads, iteration)
            iteration += 1
            
            time.sleep(2)  # Update every 2 seconds

def find_camera_pid():
    """Find PID of sec_cam_main.py process."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'sec_cam_main.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            if pids:
                return pids[0]
        
        return None
    except Exception as e:
        print(f"Error finding camera process: {e}")
        return None

def main():
    # Get PID
    if len(sys.argv) > 1:
        pid = sys.argv[1]
    else:
        print("Searching for sec_cam_main.py process...")
        pid = find_camera_pid()
        
        if pid is None:
            print("Could not find camera process")
            print("\nUsage:")
            print("  python3 thread_monitor.py [PID]")
            print("\nOr start the camera system first:")
            print("  sudo systemctl start security-camera-agent")
            return 1
        
        print(f"Found camera process: PID {pid}")
        time.sleep(1)
    
    # Start monitoring
    monitor = ThreadMonitor(pid)
    monitor.monitor()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())