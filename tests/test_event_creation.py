#!/usr/bin/env python3
"""
Test Script for Session 1A-5: Event Creation Endpoint
Tests all aspects of the event creation API
"""
import requests
import json
from datetime import datetime
import sys
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
API_URL = f"{API_BASE_URL}/api/v1"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(test_name):
    """Print test header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_pass(message):
    """Print success message"""
    print(f"{GREEN}✓ PASS: {message}{RESET}")

def print_fail(message):
    """Print failure message"""
    print(f"{RED}✗ FAIL: {message}{RESET}")

def print_info(message):
    """Print info message"""
    print(f"{YELLOW}ℹ INFO: {message}{RESET}")

# Track test results
tests_passed = 0
tests_failed = 0

def run_test(test_func):
    """Run a test function and track results"""
    global tests_passed, tests_failed
    try:
        if test_func():
            tests_passed += 1
            return True
        else:
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        tests_failed += 1
        return False


def test_1_api_health():
    """Test 1: Verify API is running"""
    print_test("Test 1: API Health Check")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print_pass(f"API is healthy: {response.json()}")
            return True
        else:
            print_fail(f"API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_fail("Cannot connect to API - is it running?")
        print_info("Start API with: ./run_api.sh")
        return False


def test_2_register_test_camera():
    """Test 2: Register a test camera"""
    print_test("Test 2: Register Test Camera")
    
    payload = {
        "camera_id": "test_cam",
        "name": "Test Camera",
        "location": "Test Location",
        "ip_address": "192.168.1.100"
    }
    
    response = requests.post(f"{API_URL}/cameras/register", json=payload)
    
    if response.status_code in [200, 201]:
        print_pass(f"Camera registered: {response.json()['camera_id']}")
        return True
    else:
        print_fail(f"Camera registration failed: {response.status_code} - {response.text}")
        return False


def test_3_create_event_success():
    """Test 3: Create event successfully"""
    print_test("Test 3: Create Event (Success)")
    
    payload = {
        "camera_id": "test_cam",
        "timestamp": datetime.now().isoformat(),
        "motion_score": 75.3
    }
    
    response = requests.post(f"{API_URL}/events", json=payload)
    
    if response.status_code == 201:
        event = response.json()
        print_pass(f"Event created with ID: {event['id']}")
        
        # Verify response structure
        assert event['camera_id'] == "test_cam", "camera_id mismatch"
        assert event['motion_score'] == 75.3, "motion_score mismatch"
        assert event['image_a_path'] is None, "image_a_path should be NULL"
        assert event['image_a_transferred'] is False, "image_a_transferred should be FALSE"
        assert event['mp4_conversion_status'] == "pending", "mp4_conversion_status should be 'pending'"
        assert event['ai_processed'] is False, "ai_processed should be FALSE"
        
        print_info(f"Event timestamp: {event['timestamp']}")
        print_info(f"All fields initialized correctly")
        return True
    else:
        print_fail(f"Event creation failed: {response.status_code} - {response.text}")
        return False


def test_4_create_multiple_events():
    """Test 4: Create multiple events (sequential IDs)"""
    print_test("Test 4: Create Multiple Events")
    
    event_ids = []
    
    for i in range(5):
        payload = {
            "camera_id": "test_cam",
            "timestamp": datetime.now().isoformat(),
            "motion_score": 70.0 + i
        }
        
        response = requests.post(f"{API_URL}/events", json=payload)
        
        if response.status_code == 201:
            event = response.json()
            event_ids.append(event['id'])
            time.sleep(0.1)  # Small delay between events
        else:
            print_fail(f"Failed to create event {i+1}")
            return False
    
    print_pass(f"Created 5 events with IDs: {event_ids}")
    
    # Verify IDs are sequential
    for i in range(len(event_ids) - 1):
        if event_ids[i+1] != event_ids[i] + 1:
            print_fail(f"Event IDs not sequential: {event_ids}")
            return False
    
    print_info("Event IDs are sequential ✓")
    return True


def test_5_camera_not_found():
    """Test 5: Create event for non-existent camera (should fail)"""
    print_test("Test 5: Event Creation - Camera Not Found")
    
    payload = {
        "camera_id": "nonexistent_camera",
        "timestamp": datetime.now().isoformat(),
        "motion_score": 75.3
    }
    
    response = requests.post(f"{API_URL}/events", json=payload)
    
    if response.status_code == 404:
        error = response.json()
        print_pass(f"Correctly returned 404: {error['detail']}")
        
        if "not registered" in error['detail']:
            print_info("Error message is clear and helpful")
            return True
        else:
            print_fail("Error message not helpful")
            return False
    else:
        print_fail(f"Expected 404, got {response.status_code}")
        return False


def test_6_missing_required_field():
    """Test 6: Create event with missing timestamp (should fail)"""
    print_test("Test 6: Event Creation - Missing Required Field")
    
    payload = {
        "camera_id": "test_cam",
        "motion_score": 75.3
        # Missing timestamp
    }
    
    response = requests.post(f"{API_URL}/events", json=payload)
    
    if response.status_code == 422:
        error = response.json()
        print_pass(f"Correctly returned 422 for validation error")
        print_info(f"Error: {error}")
        return True
    else:
        print_fail(f"Expected 422, got {response.status_code}")
        return False


def test_7_invalid_timestamp_format():
    """Test 7: Create event with invalid timestamp format (should fail)"""
    print_test("Test 7: Event Creation - Invalid Timestamp Format")
    
    payload = {
        "camera_id": "test_cam",
        "timestamp": "not-a-valid-timestamp",
        "motion_score": 75.3
    }
    
    response = requests.post(f"{API_URL}/events", json=payload)
    
    if response.status_code == 422:
        error = response.json()
        print_pass(f"Correctly returned 422 for invalid timestamp")
        print_info(f"Validation caught bad timestamp format")
        return True
    else:
        print_fail(f"Expected 422, got {response.status_code}")
        return False


def test_8_register_multiple_cameras():
    """Test 8: Register 4 cameras and create events from each"""
    print_test("Test 8: Multiple Cameras - Concurrent Event Creation")
    
    # Register 4 cameras
    for i in range(1, 5):
        payload = {
            "camera_id": f"camera_{i}",
            "name": f"Camera {i}",
            "location": f"Location {i}",
            "ip_address": f"192.168.1.20{i}"
        }
        response = requests.post(f"{API_URL}/cameras/register", json=payload)
        if response.status_code not in [200, 201]:
            print_fail(f"Failed to register camera_{i}")
            return False
    
    print_info("4 cameras registered successfully")
    
    # Create events from each camera
    event_ids = []
    for i in range(1, 5):
        payload = {
            "camera_id": f"camera_{i}",
            "timestamp": datetime.now().isoformat(),
            "motion_score": 80.0 + i
        }
        response = requests.post(f"{API_URL}/events", json=payload)
        if response.status_code == 201:
            event_ids.append(response.json()['id'])
        else:
            print_fail(f"Failed to create event for camera_{i}")
            return False
    
    print_pass(f"Created events from 4 cameras: {event_ids}")
    print_info(f"All event IDs are unique: {len(event_ids) == len(set(event_ids))}")
    return True


def test_9_verify_swagger_docs():
    """Test 9: Verify Swagger documentation is accessible"""
    print_test("Test 9: Swagger Documentation")
    
    response = requests.get(f"{API_BASE_URL}/docs")
    
    if response.status_code == 200:
        print_pass("Swagger docs accessible at /docs")
        print_info(f"View in browser: {API_BASE_URL}/docs")
        return True
    else:
        print_fail("Swagger docs not accessible")
        return False


def test_10_cleanup():
    """Test 10: Cleanup test data"""
    print_test("Test 10: Cleanup Test Data")
    
    print_info("Note: Database cleanup should be done via SQL")
    print_info("Run: mysql -u securitycam -p security_cameras")
    print_info("Then: DELETE FROM events WHERE camera_id LIKE 'test%' OR camera_id LIKE 'camera_%';")
    print_info("Then: DELETE FROM cameras WHERE camera_id LIKE 'test%' OR camera_id LIKE 'camera_%';")
    
    return True


def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Session 1A-5: Event Creation Endpoint - Test Suite{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    # Run all tests
    run_test(test_1_api_health)
    run_test(test_2_register_test_camera)
    run_test(test_3_create_event_success)
    run_test(test_4_create_multiple_events)
    run_test(test_5_camera_not_found)
    run_test(test_6_missing_required_field)
    run_test(test_7_invalid_timestamp_format)
    run_test(test_8_register_multiple_cameras)
    run_test(test_9_verify_swagger_docs)
    run_test(test_10_cleanup)
    
    # Print summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    print(f"Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}ALL TESTS PASSED! ✓{RESET}")
        print(f"{GREEN}{'='*70}{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}SOME TESTS FAILED ✗{RESET}")
        print(f"{RED}{'='*70}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()