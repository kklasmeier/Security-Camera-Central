"""
Health Check Endpoint for Camera Control API
=============================================
Add this to your camera_control_api.py to enable health monitoring.

This provides:
1. Thread health status
2. Frame capture diagnostics
3. Component responsiveness checks
4. Buffer health metrics

Usage:
    GET /health - Returns comprehensive health status
    GET /health/quick - Returns quick alive/dead status
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class HealthChecker:
    """
    Health monitoring for camera system components.
    
    Tracks:
    - Thread status (alive/dead)
    - Frame capture activity (are new frames being captured?)
    - Motion detection activity (is detector running?)
    - Event processing activity (is processor responsive?)
    - Buffer health (is circular buffer working?)
    """
    
    def __init__(self, circular_buffer, motion_detector, event_processor, 
                 transfer_manager=None, mjpeg_server=None):
        """
        Initialize health checker.
        
        Args:
            circular_buffer: CircularBuffer instance
            motion_detector: MotionDetector instance
            event_processor: EventProcessor instance
            transfer_manager: TransferManager instance (optional)
            mjpeg_server: MJPEGServer instance (optional)
        """
        self.circular_buffer = circular_buffer
        self.motion_detector = motion_detector
        self.event_processor = event_processor
        self.transfer_manager = transfer_manager
        self.mjpeg_server = mjpeg_server
        
        # Track last known good states
        self.last_frame_hash = None
        self.last_frame_check = None
        self.frame_update_count = 0
    
    def check_thread_health(self) -> Dict[str, Any]:
        """
        Check if all expected threads are alive.
        
        Returns:
            dict: {
                'all_threads_alive': bool,
                'threads': {
                    'CircularBufferCapture': bool,
                    'MotionDetector': bool,
                    'EventProcessor': bool,
                    ...
                },
                'missing_threads': [list of missing thread names]
            }
        """
        threads = threading.enumerate()
        thread_names = {t.name: t.is_alive() for t in threads}
        
        expected = [
            'CircularBufferCapture',
            'MotionDetector', 
            'EventProcessor',
            'TransferManager',
        ]
        
        missing = [name for name in expected if name not in thread_names]
        
        return {
            'all_threads_alive': len(missing) == 0,
            'threads': thread_names,
            'expected_threads': {name: thread_names.get(name, False) for name in expected},
            'missing_threads': missing,
            'total_threads': len(threads)
        }
    
    def check_frame_capture(self) -> Dict[str, Any]:
        """
        Check if camera is capturing new frames.
        
        This is THE KEY DIAGNOSTIC for your issue.
        If frames aren't updating, the camera thread is stuck.
        
        Returns:
            dict: {
                'frames_updating': bool,
                'current_frame_available': bool,
                'previous_frame_available': bool,
                'frames_identical': bool (BAD if True),
                'last_update_seconds_ago': float or None
            }
        """
        try:
            prev_frame, curr_frame = self.circular_buffer.get_frames_for_detection()
            
            # Check if frames exist
            frames_available = (prev_frame is not None and curr_frame is not None)
            
            if not frames_available:
                return {
                    'frames_updating': False,
                    'current_frame_available': curr_frame is not None,
                    'previous_frame_available': prev_frame is not None,
                    'frames_identical': None,
                    'last_update_seconds_ago': None,
                    'error': 'Frames not available'
                }
            
            # Check if frames are identical (sign of stuck camera)
            import numpy as np
            frames_identical = np.array_equal(prev_frame, curr_frame)
            
            # Calculate frame hash to track changes
            import hashlib
            curr_hash = hashlib.md5(curr_frame.tobytes()).hexdigest()
            
            now = time.time()
            
            # Check if frame has changed since last check
            frames_updating = True
            if self.last_frame_hash is not None:
                if curr_hash == self.last_frame_hash:
                    frames_updating = False
                else:
                    self.frame_update_count += 1
            
            time_since_last_check = None
            if self.last_frame_check is not None:
                time_since_last_check = now - self.last_frame_check
            
            # Update tracking
            self.last_frame_hash = curr_hash
            self.last_frame_check = now
            
            return {
                'frames_updating': frames_updating,
                'current_frame_available': True,
                'previous_frame_available': True,
                'frames_identical': frames_identical,
                'frame_shape': curr_frame.shape,
                'update_count': self.frame_update_count,
                'time_since_last_check': time_since_last_check
            }
            
        except Exception as e:
            return {
                'frames_updating': False,
                'error': str(e)
            }
    
    def check_motion_detector(self) -> Dict[str, Any]:
        """
        Check motion detector health.
        
        Returns:
            dict: {
                'running': bool,
                'in_cooldown': bool,
                'last_detection_time': float or None
            }
        """
        try:
            is_running = self.motion_detector.running
            in_cooldown = self.motion_detector._in_cooldown()
            last_detection = self.motion_detector.last_detection_time
            
            seconds_since_detection = None
            if last_detection > 0:
                seconds_since_detection = time.time() - last_detection
            
            return {
                'running': is_running,
                'in_cooldown': in_cooldown,
                'last_detection_time': last_detection,
                'seconds_since_detection': seconds_since_detection,
                'threshold': self.motion_detector.threshold,
                'sensitivity': self.motion_detector.sensitivity
            }
        except Exception as e:
            return {
                'running': False,
                'error': str(e)
            }
    
    def check_buffer_health(self) -> Dict[str, Any]:
        """
        Check circular buffer health.
        
        Returns:
            dict: {
                'capture_running': bool,
                'camera_initialized': bool,
                'encoder_initialized': bool
            }
        """
        try:
            return {
                'capture_running': self.circular_buffer.running,
                'camera_initialized': self.circular_buffer.picam2 is not None,
                'encoder_initialized': self.circular_buffer.encoder is not None,
                'circular_output_initialized': self.circular_buffer.circular_output is not None
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def check_event_processor(self) -> Dict[str, Any]:
        """
        Check event processor health.
        
        Returns:
            dict: {
                'running': bool,
                'currently_processing': bool
            }
        """
        try:
            return {
                'running': self.event_processor.running,
                'currently_processing': self.event_processor.is_processing()
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of all components.
        
        Returns:
            dict: Complete health report
        """
        threads = self.check_thread_health()
        frames = self.check_frame_capture()
        motion = self.check_motion_detector()
        buffer = self.check_buffer_health()
        processor = self.check_event_processor()
        
        # Determine overall health
        critical_issues = []
        warnings = []
        
        # Check for critical issues
        if not threads['all_threads_alive']:
            critical_issues.append(f"Missing threads: {threads['missing_threads']}")
        
        if not frames['frames_updating']:
            critical_issues.append("Camera frames not updating - CAMERA STUCK")
        
        if frames.get('frames_identical'):
            warnings.append("Previous and current frames are identical")
        
        if not buffer.get('capture_running'):
            critical_issues.append("Circular buffer capture not running")
        
        if not motion.get('running'):
            critical_issues.append("Motion detector not running")
        
        # Overall health status
        if critical_issues:
            overall_status = "CRITICAL"
        elif warnings:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'critical_issues': critical_issues,
            'warnings': warnings,
            'components': {
                'threads': threads,
                'frame_capture': frames,
                'motion_detector': motion,
                'circular_buffer': buffer,
                'event_processor': processor
            }
        }
    
    def get_quick_health(self) -> Dict[str, Any]:
        """
        Get quick health check (fast, minimal computation).
        
        Returns:
            dict: Quick status
        """
        threads_ok = self.check_thread_health()['all_threads_alive']
        buffer_ok = self.circular_buffer.running
        
        status = "ok" if (threads_ok and buffer_ok) else "degraded"
        
        return {
            'status': status,
            'threads_alive': threads_ok,
            'buffer_running': buffer_ok,
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# INTEGRATION WITH camera_control_api.py
# ============================================================================

"""
Add these endpoints to your CameraControlAPI class:

    def __init__(self, circular_buffer, mjpeg_server, event_processor):
        # ... existing code ...
        
        # Add health checker
        self.health_checker = HealthChecker(
            circular_buffer=circular_buffer,
            motion_detector=None,  # Pass from main
            event_processor=event_processor,
            transfer_manager=None,  # Pass from main
            mjpeg_server=mjpeg_server
        )
    
    def _setup_routes(self):
        # ... existing routes ...
        
        # Health check endpoints
        self.app.route('/health', methods=['GET'])(self.get_health)
        self.app.route('/health/quick', methods=['GET'])(self.get_quick_health)
    
    def get_health(self):
        '''GET /health - Comprehensive health check'''
        health = self.health_checker.get_comprehensive_health()
        
        status_code = 200
        if health['overall_status'] == 'CRITICAL':
            status_code = 503  # Service Unavailable
        elif health['overall_status'] == 'WARNING':
            status_code = 200  # Still operational
        
        return jsonify(health), status_code
    
    def get_quick_health(self):
        '''GET /health/quick - Fast health check'''
        health = self.health_checker.get_quick_health()
        status_code = 200 if health['status'] == 'ok' else 503
        return jsonify(health), status_code
"""