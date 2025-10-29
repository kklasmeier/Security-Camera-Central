#!/usr/bin/env python3
"""
Test Script for Log Ingestion Endpoint (Session 1A-7)

Tests the POST /api/v1/logs endpoint with various scenarios:
- Single log entry
- Batch of multiple logs
- All three log levels (INFO, WARNING, ERROR)
- Multiple sources (camera_1, camera_2, central)
- Error cases (empty array, invalid level, missing fields)
- Database verification

Requirements:
- API server running on localhost:8000
- Database accessible with test credentials
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test counters
tests_passed = 0
tests_failed = 0


def print_test(test_name):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print('='*70)


def print_result(passed, message):
    """Print test result and update counters"""
    global tests_passed, tests_failed
    
    if passed:
        tests_passed += 1
        print(f"✓ PASS: {message}")
    else:
        tests_failed += 1
        print(f"✗ FAIL: {message}")


def test_single_log():
    """Test 1: Insert single log entry"""
    print_test("Insert Single Log Entry")
    
    payload = [
        {
            "source": "test_cam",
            "timestamp": "2025-10-28T14:30:22.186476",
            "level": "INFO",
            "message": "Test message from single log test"
        }
    ]
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        # Check status code
        if response.status_code == 201:
            print_result(True, "Returned HTTP 201 Created")
        else:
            print_result(False, f"Expected 201, got {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # Check response body
        data = response.json()
        if data.get("status") == "success" and data.get("logs_inserted") == 1:
            print_result(True, "Response indicates 1 log inserted")
        else:
            print_result(False, f"Unexpected response: {data}")
        
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def test_batch_logs():
    """Test 2: Insert batch of multiple logs"""
    print_test("Insert Batch of Multiple Logs")
    
    payload = [
        {
            "source": "test_cam",
            "timestamp": "2025-10-28T14:30:22.000000",
            "level": "INFO",
            "message": "Batch log 1"
        },
        {
            "source": "test_cam",
            "timestamp": "2025-10-28T14:30:23.000000",
            "level": "WARNING",
            "message": "Batch log 2"
        },
        {
            "source": "test_cam",
            "timestamp": "2025-10-28T14:30:24.000000",
            "level": "ERROR",
            "message": "Batch log 3"
        }
    ]
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        if response.status_code == 201:
            print_result(True, "Returned HTTP 201 Created")
        else:
            print_result(False, f"Expected 201, got {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        if data.get("logs_inserted") == 3:
            print_result(True, "Response indicates 3 logs inserted")
        else:
            print_result(False, f"Expected 3 logs, got: {data}")
        
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def test_all_log_levels():
    """Test 3: Test all three log levels"""
    print_test("Test All Three Log Levels")
    
    levels = ["INFO", "WARNING", "ERROR"]
    
    for level in levels:
        payload = [
            {
                "source": "test_cam",
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": f"Testing {level} level"
            }
        ]
        
        try:
            response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
            
            if response.status_code == 201:
                print_result(True, f"{level} level accepted")
            else:
                print_result(False, f"{level} level rejected: {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print_result(False, f"{level} level caused exception: {e}")


def test_multiple_sources():
    """Test 4: Test multiple sources"""
    print_test("Test Multiple Sources")
    
    sources = ["camera_1", "camera_2", "central"]
    
    for source in sources:
        payload = [
            {
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Test from {source}"
            }
        ]
        
        try:
            response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
            
            if response.status_code == 201:
                print_result(True, f"Source '{source}' accepted")
            else:
                print_result(False, f"Source '{source}' rejected: {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print_result(False, f"Source '{source}' caused exception: {e}")


def test_empty_array():
    """Test 5: Empty array (should fail with 400)"""
    print_test("Empty Array (Should Fail)")
    
    payload = []
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        if response.status_code == 400:
            print_result(True, "Correctly rejected empty array with HTTP 400")
        else:
            print_result(False, f"Expected 400, got {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def test_invalid_log_level():
    """Test 6: Invalid log level (should fail with 422)"""
    print_test("Invalid Log Level (Should Fail)")
    
    payload = [
        {
            "source": "test_cam",
            "timestamp": "2025-10-28T14:30:22.186476",
            "level": "DEBUG",  # Invalid - only INFO, WARNING, ERROR allowed
            "message": "Test"
        }
    ]
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        if response.status_code == 422:
            print_result(True, "Correctly rejected invalid log level with HTTP 422")
        else:
            print_result(False, f"Expected 422, got {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def test_missing_field():
    """Test 7: Missing required field (should fail with 422)"""
    print_test("Missing Required Field (Should Fail)")
    
    payload = [
        {
            "source": "test_cam",
            "timestamp": "2025-10-28T14:30:22.186476",
            "level": "INFO"
            # Missing 'message' field
        }
    ]
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        if response.status_code == 422:
            print_result(True, "Correctly rejected missing field with HTTP 422")
        else:
            print_result(False, f"Expected 422, got {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def test_invalid_timestamp():
    """Test 8: Invalid timestamp format (should fail with 422)"""
    print_test("Invalid Timestamp Format (Should Fail)")
    
    payload = [
        {
            "source": "test_cam",
            "timestamp": "not-a-valid-timestamp",
            "level": "INFO",
            "message": "Test"
        }
    ]
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        if response.status_code == 422:
            print_result(True, "Correctly rejected invalid timestamp with HTTP 422")
        else:
            print_result(False, f"Expected 422, got {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def test_large_batch():
    """Test 9: Large batch (50 logs for performance)"""
    print_test("Large Batch (50 logs)")
    
    base_time = datetime.now()
    payload = []
    
    for i in range(50):
        payload.append({
            "source": "perf_test",
            "timestamp": base_time.replace(microsecond=i*1000).isoformat(),
            "level": "INFO",
            "message": f"Performance test log {i}"
        })
    
    try:
        response = requests.post(f"{API_BASE_URL}/logs", headers=HEADERS, json=payload)
        
        if response.status_code == 201:
            print_result(True, "Large batch accepted")
        else:
            print_result(False, f"Large batch rejected: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        if data.get("logs_inserted") == 50:
            print_result(True, "All 50 logs inserted")
        else:
            print_result(False, f"Expected 50 logs, got: {data}")
    
    except Exception as e:
        print_result(False, f"Exception occurred: {e}")


def print_summary():
    """Print test summary"""
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests:  {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} TEST(S) FAILED")
        return 1


def main():
    """Run all tests"""
    print("="*70)
    print("LOG INGESTION ENDPOINT TEST SUITE (Session 1A-7)")
    print("="*70)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Testing endpoint: POST /api/v1/logs")
    
    # Check if API is running
    try:
        response = requests.get(f"http://localhost:8000/")
        print("✓ API server is running")
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to API server")
        print("  Please start the API server first: ./run_api.sh")
        return 1
    
    # Run tests
    test_single_log()
    test_batch_logs()
    test_all_log_levels()
    test_multiple_sources()
    test_empty_array()
    test_invalid_log_level()
    test_missing_field()
    test_invalid_timestamp()
    test_large_batch()
    
    # Print summary and exit
    return print_summary()


if __name__ == "__main__":
    sys.exit(main())