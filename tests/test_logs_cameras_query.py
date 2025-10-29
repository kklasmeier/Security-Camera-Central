#!/usr/bin/env python3
"""
Test script for Session 1A-9: Log and Camera Query Endpoints

Tests:
1. GET /api/v1/logs - Query logs with filtering
2. GET /api/v1/cameras - List all registered cameras

Usage:
    python test_logs_cameras_query.py
"""

import requests
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://192.168.1.26:8000/api/v1"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0
}


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Colors.ENDC}\n")


def print_test(name: str):
    """Print test name"""
    print(f"{Colors.OKBLUE}► {name}{Colors.ENDC}")


def print_success(message: str):
    """Print success message"""
    print(f"  {Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"  {Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def mark_test_passed():
    """Mark current test as passed"""
    test_results["passed"] += 1
    test_results["total"] += 1


def mark_test_failed():
    """Mark current test as failed"""
    test_results["failed"] += 1
    test_results["total"] += 1


def print_json(data: Any, indent: int = 2):
    """Pretty print JSON data"""
    print(f"{Colors.OKCYAN}{json.dumps(data, indent=indent, default=str)}{Colors.ENDC}")


# ============================================================================
# SETUP: Create test data
# ============================================================================

def setup_test_data():
    """Create test cameras and logs for testing"""
    print_header("SETUP: Creating Test Data")
    
    # Register test cameras
    cameras = [
        {
            "camera_id": "camera_1",
            "name": "Front Door",
            "location": "Main Entrance",
            "ip_address": "192.168.1.201"
        },
        {
            "camera_id": "camera_2",
            "name": "Backyard",
            "location": "Backyard Facing Street",
            "ip_address": "192.168.1.202"
        }
    ]
    
    for camera in cameras:
        try:
            response = requests.post(f"{BASE_URL}/cameras/register", json=camera)
            if response.status_code in [200, 201]:
                print_success(f"Registered camera: {camera['camera_id']}")
            else:
                print_error(f"Failed to register camera: {camera['camera_id']}")
        except Exception as e:
            print_error(f"Error registering camera: {e}")
    
    # Create test logs
    logs = [
        {
            "source": "camera_1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": "Motion detected at threshold 75.3"
        },
        {
            "source": "camera_1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": "Event 42 created successfully"
        },
        {
            "source": "camera_1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR",
            "message": "Failed to transfer image_a"
        },
        {
            "source": "camera_2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": "Motion detected at threshold 82.1"
        },
        {
            "source": "camera_2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "WARNING",
            "message": "Network latency high: 250ms"
        },
        {
            "source": "central",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": "MP4 conversion worker started"
        }
    ]
    
    try:
        response = requests.post(f"{BASE_URL}/logs", json=logs)
        if response.status_code == 201:
            result = response.json()
            print_success(f"Inserted {result['logs_inserted']} log entries")
        else:
            print_error(f"Failed to insert logs: {response.text}")
    except Exception as e:
        print_error(f"Error inserting logs: {e}")


# ============================================================================
# TEST 1: List All Cameras
# ============================================================================

def test_list_cameras():
    """Test GET /api/v1/cameras"""
    print_header("TEST 1: List All Cameras")
    
    print_test("GET /api/v1/cameras")
    
    try:
        response = requests.get(f"{BASE_URL}/cameras")
        
        if response.status_code == 200:
            cameras = response.json()
            print_success(f"Status: {response.status_code}")
            print_success(f"Returned {len(cameras)} cameras")
            
            # Verify structure
            if len(cameras) > 0:
                camera = cameras[0]
                required_fields = ["id", "camera_id", "name", "location", "ip_address", 
                                 "status", "created_at", "updated_at"]
                
                all_fields_present = True
                for field in required_fields:
                    if field in camera:
                        print_success(f"Field '{field}' present")
                    else:
                        print_error(f"Field '{field}' missing")
                        all_fields_present = False
                
                # Verify sorting (should be by camera_id)
                camera_ids = [c["camera_id"] for c in cameras]
                sorted_ids = sorted(camera_ids)
                if camera_ids == sorted_ids:
                    print_success("Cameras sorted by camera_id")
                else:
                    print_error(f"Cameras not sorted correctly: {camera_ids}")
                    all_fields_present = False
                
                print_info("Sample camera:")
                print_json(cameras[0])
                
                if all_fields_present:
                    mark_test_passed()
                else:
                    mark_test_failed()
            else:
                print_error("No cameras returned")
                mark_test_failed()
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            mark_test_failed()
    
    except Exception as e:
        print_error(f"Error: {e}")
        mark_test_failed()


# ============================================================================
# TEST 2: Get All Logs (Default)
# ============================================================================

def test_get_all_logs():
    """Test GET /api/v1/logs with no filters"""
    print_header("TEST 2: Get All Logs (Default)")
    
    print_test("GET /api/v1/logs")
    
    try:
        response = requests.get(f"{BASE_URL}/logs")
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Status: {response.status_code}")
            print_success(f"Returned {len(result['logs'])} logs")
            print_success(f"Total: {result['total']}")
            print_success(f"Limit: {result['limit']}")
            print_success(f"Offset: {result['offset']}")
            
            # Verify structure
            test_passed = True
            if len(result['logs']) > 0:
                log = result['logs'][0]
                required_fields = ["id", "source", "timestamp", "level", "message"]
                
                for field in required_fields:
                    if field in log:
                        print_success(f"Field '{field}' present")
                    else:
                        print_error(f"Field '{field}' missing")
                        test_passed = False
                
                # Verify sorting (should be newest first)
                timestamps = [log["timestamp"] for log in result['logs']]
                sorted_timestamps = sorted(timestamps, reverse=True)
                if timestamps == sorted_timestamps:
                    print_success("Logs sorted by timestamp DESC (newest first)")
                else:
                    print_error("Logs not sorted correctly")
                    test_passed = False
                
                print_info("Sample log:")
                print_json(result['logs'][0])
                
                if test_passed:
                    mark_test_passed()
                else:
                    mark_test_failed()
            else:
                print_error("No logs returned")
                mark_test_failed()
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            mark_test_failed()
    
    except Exception as e:
        print_error(f"Error: {e}")
        mark_test_failed()


# ============================================================================
# TEST 3: Filter Logs by Source
# ============================================================================

def test_filter_by_source():
    """Test GET /api/v1/logs?source=camera_1"""
    print_header("TEST 3: Filter Logs by Source")
    
    print_test("GET /api/v1/logs?source=camera_1")
    
    try:
        response = requests.get(f"{BASE_URL}/logs", params={"source": "camera_1"})
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Status: {response.status_code}")
            print_success(f"Returned {len(result['logs'])} logs from camera_1")
            print_success(f"Total: {result['total']}")
            
            # Verify all logs are from camera_1
            all_from_camera_1 = all(log["source"] == "camera_1" for log in result['logs'])
            if all_from_camera_1:
                print_success("All logs are from camera_1")
                mark_test_passed()
            else:
                print_error("Some logs are not from camera_1")
                mark_test_failed()
            
            if len(result['logs']) > 0:
                print_info("Sample log:")
                print_json(result['logs'][0])
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            mark_test_failed()
    
    except Exception as e:
        print_error(f"Error: {e}")
        mark_test_failed()


# ============================================================================
# TEST 4: Filter Logs by Level
# ============================================================================

def test_filter_by_level():
    """Test GET /api/v1/logs?level=ERROR"""
    print_header("TEST 4: Filter Logs by Level")
    
    print_test("GET /api/v1/logs?level=ERROR")
    
    try:
        response = requests.get(f"{BASE_URL}/logs", params={"level": "ERROR"})
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Status: {response.status_code}")
            print_success(f"Returned {len(result['logs'])} ERROR logs")
            print_success(f"Total: {result['total']}")
            
            # Verify all logs are ERROR level
            all_errors = all(log["level"] == "ERROR" for log in result['logs'])
            if all_errors:
                print_success("All logs are ERROR level")
                mark_test_passed()
            else:
                print_error("Some logs are not ERROR level")
                mark_test_failed()
            
            if len(result['logs']) > 0:
                print_info("Sample log:")
                print_json(result['logs'][0])
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            mark_test_failed()
    
    except Exception as e:
        print_error(f"Error: {e}")
        mark_test_failed()


# ============================================================================
# TEST 5: Combined Filters (Source + Level)
# ============================================================================

def test_combined_filters():
    """Test GET /api/v1/logs?source=camera_1&level=ERROR"""
    print_header("TEST 5: Combined Filters (Source + Level)")
    
    print_test("GET /api/v1/logs?source=camera_1&level=ERROR")
    
    try:
        response = requests.get(
            f"{BASE_URL}/logs",
            params={"source": "camera_1", "level": "ERROR"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Status: {response.status_code}")
            print_success(f"Returned {len(result['logs'])} logs")
            print_success(f"Total: {result['total']}")
            
            # Verify filters applied correctly
            correct_filters = all(
                log["source"] == "camera_1" and log["level"] == "ERROR"
                for log in result['logs']
            )
            if correct_filters:
                print_success("All logs match filters (source=camera_1, level=ERROR)")
                mark_test_passed()
            else:
                print_error("Some logs don't match filters")
                mark_test_failed()
            
            if len(result['logs']) > 0:
                print_info("Sample log:")
                print_json(result['logs'][0])
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            mark_test_failed()
    
    except Exception as e:
        print_error(f"Error: {e}")
        mark_test_failed()


# ============================================================================
# TEST 6: Pagination
# ============================================================================

def test_pagination():
    """Test GET /api/v1/logs?limit=2&offset=0"""
    print_header("TEST 6: Pagination")
    
    print_test("GET /api/v1/logs?limit=2&offset=0")
    
    try:
        response = requests.get(f"{BASE_URL}/logs", params={"limit": 2, "offset": 0})
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Status: {response.status_code}")
            print_success(f"Returned {len(result['logs'])} logs (expected 2)")
            print_success(f"Total: {result['total']}")
            print_success(f"Limit: {result['limit']}")
            print_success(f"Offset: {result['offset']}")
            
            pagination_passed = True
            if len(result['logs']) == 2:
                print_success("Pagination working correctly (limit=2)")
            else:
                print_error(f"Expected 2 logs, got {len(result['logs'])}")
                pagination_passed = False
            
            # Test offset
            print_test("GET /api/v1/logs?limit=2&offset=2")
            response2 = requests.get(f"{BASE_URL}/logs", params={"limit": 2, "offset": 2})
            
            if response2.status_code == 200:
                result2 = response2.json()
                print_success(f"Returned {len(result2['logs'])} logs with offset=2")
                
                # Verify different logs returned
                first_ids = [log["id"] for log in result['logs']]
                second_ids = [log["id"] for log in result2['logs']]
                
                if not any(id in second_ids for id in first_ids):
                    print_success("Offset working correctly (different logs returned)")
                else:
                    print_error("Offset not working (same logs returned)")
                    pagination_passed = False
            else:
                pagination_passed = False
            
            if pagination_passed:
                mark_test_passed()
            else:
                mark_test_failed()
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            mark_test_failed()
    
    except Exception as e:
        print_error(f"Error: {e}")
        mark_test_failed()


# ============================================================================
# TEST 7: Parameter Validation
# ============================================================================

def test_parameter_validation():
    """Test parameter validation"""
    print_header("TEST 7: Parameter Validation")
    
    validation_passed = True
    
    # Test invalid limit (> 500)
    print_test("GET /api/v1/logs?limit=600 (should fail)")
    try:
        response = requests.get(f"{BASE_URL}/logs", params={"limit": 600})
        if response.status_code == 422:
            print_success("Correctly rejected limit > 500")
        else:
            print_error(f"Expected 422, got {response.status_code}")
            validation_passed = False
    except Exception as e:
        print_error(f"Error: {e}")
        validation_passed = False
    
    # Test invalid offset (< 0)
    print_test("GET /api/v1/logs?offset=-1 (should fail)")
    try:
        response = requests.get(f"{BASE_URL}/logs", params={"offset": -1})
        if response.status_code == 422:
            print_success("Correctly rejected negative offset")
        else:
            print_error(f"Expected 422, got {response.status_code}")
            validation_passed = False
    except Exception as e:
        print_error(f"Error: {e}")
        validation_passed = False
    
    # Test invalid level
    print_test("GET /api/v1/logs?level=INVALID (should fail)")
    try:
        response = requests.get(f"{BASE_URL}/logs", params={"level": "INVALID"})
        if response.status_code == 422:
            print_success("Correctly rejected invalid level")
        else:
            print_error(f"Expected 422, got {response.status_code}")
            validation_passed = False
    except Exception as e:
        print_error(f"Error: {e}")
        validation_passed = False
    
    if validation_passed:
        mark_test_passed()
    else:
        mark_test_failed()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  Session 1A-9: Log and Camera Query Endpoints Test Suite")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    
    # Setup
    setup_test_data()
    
    # Run tests
    test_list_cameras()
    test_get_all_logs()
    test_filter_by_source()
    test_filter_by_level()
    test_combined_filters()
    test_pagination()
    test_parameter_validation()
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"{Colors.BOLD}Total Tests: {test_results['total']}{Colors.ENDC}")
    
    if test_results['passed'] > 0:
        print(f"{Colors.OKGREEN}✓ Passed: {test_results['passed']}{Colors.ENDC}")
    
    if test_results['failed'] > 0:
        print(f"{Colors.FAIL}✗ Failed: {test_results['failed']}{Colors.ENDC}")
    
    if test_results['failed'] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}")
    
    print_info("\nCheck Swagger UI at: http://192.168.1.26:8000/docs")
    print_info("You can now test both endpoints interactively!")


if __name__ == "__main__":
    main()