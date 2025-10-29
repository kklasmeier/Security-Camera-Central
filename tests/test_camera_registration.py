#!/usr/bin/env python3
"""
Test script for Camera Registration Endpoint (Session 1A-4)

Tests:
1. Register new camera (expect 200 with camera data)
2. Re-register same camera (expect 200 with updated data)
3. Register multiple cameras
4. Validation errors (missing fields, invalid format)
5. Verify database state
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
REGISTER_ENDPOINT = f"{API_BASE_URL}/cameras/register"

# Test counters
tests_passed = 0
tests_failed = 0


def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)


def print_result(passed, message):
    """Print test result"""
    global tests_passed, tests_failed
    if passed:
        print(f"✅ PASS: {message}")
        tests_passed += 1
    else:
        print(f"❌ FAIL: {message}")
        tests_failed += 1


def test_register_new_camera():
    """Test 1: Register a new camera"""
    print_test_header("Register New Camera")
    
    data = {
        "camera_id": "test_camera_1",
        "name": "Test Camera 1",
        "location": "Test Location 1",
        "ip_address": "192.168.1.201"
    }
    
    print(f"POST {REGISTER_ENDPOINT}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(REGISTER_ENDPOINT, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Check status code (should be 200, spec allows 200 or 201)
        if response.status_code in [200, 201]:
            print_result(True, f"Status code {response.status_code} (new camera)")
        else:
            print_result(False, f"Expected 200/201, got {response.status_code}")
            return
        
        # Check response data
        resp_data = response.json()
        print_result(resp_data.get("camera_id") == "test_camera_1", "camera_id matches")
        print_result(resp_data.get("name") == "Test Camera 1", "name matches")
        print_result(resp_data.get("location") == "Test Location 1", "location matches")
        print_result(resp_data.get("ip_address") == "192.168.1.201", "ip_address matches")
        print_result(resp_data.get("status") == "online", "status is 'online'")
        print_result("id" in resp_data, "response includes database id")
        print_result("created_at" in resp_data, "response includes created_at")
        print_result("updated_at" in resp_data, "response includes updated_at")
        
    except requests.exceptions.RequestException as e:
        print_result(False, f"Request failed: {e}")


def test_reregister_camera():
    """Test 2: Re-register existing camera (update)"""
    print_test_header("Re-register Existing Camera (Update)")
    
    data = {
        "camera_id": "test_camera_1",
        "name": "Test Camera 1 Updated",
        "location": "New Location",
        "ip_address": "192.168.1.202"
    }
    
    print(f"POST {REGISTER_ENDPOINT}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(REGISTER_ENDPOINT, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 200 for update
        print_result(response.status_code == 200, f"Status code 200 (update)")
        
        # Check updated data
        resp_data = response.json()
        print_result(resp_data.get("name") == "Test Camera 1 Updated", "name was updated")
        print_result(resp_data.get("location") == "New Location", "location was updated")
        print_result(resp_data.get("ip_address") == "192.168.1.202", "ip_address was updated")
        print_result(resp_data.get("status") == "online", "status is 'online'")
        
    except requests.exceptions.RequestException as e:
        print_result(False, f"Request failed: {e}")


def test_register_multiple_cameras():
    """Test 3: Register 4 cameras (simulating real deployment)"""
    print_test_header("Register Multiple Cameras")
    
    cameras = [
        {"camera_id": "camera_1", "name": "Front Door", "location": "Main Entrance", "ip_address": "192.168.1.101"},
        {"camera_id": "camera_2", "name": "Backyard", "location": "Backyard Facing Street", "ip_address": "192.168.1.102"},
        {"camera_id": "camera_3", "name": "Garage", "location": "Garage Door", "ip_address": "192.168.1.103"},
        {"camera_id": "camera_4", "name": "Side Entrance", "location": "Side Door", "ip_address": "192.168.1.104"},
    ]
    
    for camera in cameras:
        print(f"\nRegistering {camera['camera_id']}...")
        try:
            response = requests.post(REGISTER_ENDPOINT, json=camera, timeout=10)
            if response.status_code in [200, 201]:
                print_result(True, f"{camera['camera_id']} registered")
            else:
                print_result(False, f"{camera['camera_id']} failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print_result(False, f"{camera['camera_id']} request failed: {e}")


def test_missing_required_field():
    """Test 4: Missing required field (validation error)"""
    print_test_header("Validation Error - Missing Required Field")
    
    data = {
        "camera_id": "test_invalid",
        "name": "Invalid Camera"
        # Missing: location, ip_address
    }
    
    print(f"POST {REGISTER_ENDPOINT}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(REGISTER_ENDPOINT, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 422 (Unprocessable Entity)
        print_result(response.status_code == 422, "Status code 422 (validation error)")
        
        # Should include error details
        resp_data = response.json()
        print_result("detail" in resp_data, "Response includes error details")
        
    except requests.exceptions.RequestException as e:
        print_result(False, f"Request failed: {e}")


def test_invalid_camera_id_format():
    """Test 5: Invalid camera_id format"""
    print_test_header("Validation Error - Invalid camera_id Format")
    
    data = {
        "camera_id": "camera-with-hyphens",  # Hyphens not allowed
        "name": "Invalid Camera",
        "location": "Test Location",
        "ip_address": "192.168.1.1"
    }
    
    print(f"POST {REGISTER_ENDPOINT}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(REGISTER_ENDPOINT, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 422 (validation error)
        print_result(response.status_code == 422, "Status code 422 (validation error)")
        
        resp_data = response.json()
        error_msg = str(resp_data)
        print_result("camera_id" in error_msg, "Error mentions camera_id field")
        
    except requests.exceptions.RequestException as e:
        print_result(False, f"Request failed: {e}")


def test_health_check():
    """Test 0: Verify API is running"""
    print_test_header("Health Check - Verify API is Running")
    
    health_url = f"{API_BASE_URL}/health"
    print(f"GET {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print_result(response.status_code == 200, "API is running")
        
        resp_data = response.json()
        print_result(resp_data.get("status") == "healthy", "API status is healthy")
        print_result(resp_data.get("database") == "connected", "Database is connected")
        
    except requests.exceptions.RequestException as e:
        print_result(False, f"API health check failed: {e}")
        print("\n⚠️  API does not appear to be running!")
        print("Please start the API with: ./run_api.sh")
        sys.exit(1)


def print_summary():
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📊 Total:  {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} TEST(S) FAILED")
        return 1


def main():
    """Run all tests"""
    print("=" * 80)
    print("CAMERA REGISTRATION ENDPOINT TEST SUITE")
    print("Session 1A-4")
    print("=" * 80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests in order
    test_health_check()
    test_register_new_camera()
    test_reregister_camera()
    test_register_multiple_cameras()
    test_missing_required_field()
    test_invalid_camera_id_format()
    
    # Print summary and exit
    exit_code = print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
