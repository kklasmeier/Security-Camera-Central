#!/usr/bin/env python3
"""
Test Script for Session 1A-6: File Update Endpoint
Tests the PATCH /api/v1/events/{event_id}/files endpoint

Requirements:
- API server running on http://localhost:8000
- Database configured and accessible
- Camera registered (camera_1)

Usage:
    python test_file_updates.py
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_CAMERA_ID = "camera_1"

# ANSI color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{BLUE}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{RESET}\n")


def print_test(test_name: str):
    """Print test name"""
    print(f"{YELLOW}TEST: {test_name}{RESET}")


def print_pass(message: str = "PASS"):
    """Print success message"""
    print(f"  {GREEN}✓ {message}{RESET}")


def print_fail(message: str):
    """Print failure message"""
    print(f"  {RED}✗ FAIL: {message}{RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"  {BLUE}ℹ {message}{RESET}")


def register_test_camera() -> bool:
    """Register test camera if not already registered"""
    print_test("Registering test camera")
    
    payload = {
        "camera_id": TEST_CAMERA_ID,
        "name": "Test Camera",
        "location": "Test Location",
        "ip_address": "192.168.1.100"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/cameras/register", json=payload)
        if response.status_code in [200, 201]:
            print_pass("Camera registered successfully")
            return True
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print_pass("Camera already registered")
            return True
        else:
            print_fail(f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


def create_test_event() -> Optional[int]:
    """Create a test event and return its ID"""
    print_test("Creating test event")
    
    payload = {
        "camera_id": TEST_CAMERA_ID,
        "timestamp": datetime.now().isoformat(),
        "motion_score": 75.3
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/events", json=payload)
        if response.status_code == 201:
            data = response.json()
            event_id = data['id']
            print_pass(f"Event created with ID: {event_id}")
            return event_id
        else:
            print_fail(f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_fail(f"Exception: {e}")
        return None


def update_file(event_id: int, file_type: str, file_path: str, 
                transferred: bool = True, video_duration: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Update a file for an event and return the updated event"""
    payload = {
        "file_type": file_type,
        "file_path": file_path,
        "transferred": transferred
    }
    
    if video_duration is not None:
        payload["video_duration"] = video_duration
    
    try:
        response = requests.patch(
            f"{API_BASE_URL}/events/{event_id}/files",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print_fail(f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_fail(f"Exception: {e}")
        return None


def get_event(event_id: int) -> Optional[Dict[str, Any]]:
    """Get event details - uses PATCH response since GET endpoint doesn't exist yet (Session 1A-8)"""
    # Since GET /events/{id} doesn't exist yet, we'll do a dummy update to get current state
    try:
        # Just update image_a with same values (idempotent) to get current state
        response = requests.patch(
            f"{API_BASE_URL}/events/{event_id}/files",
            json={
                "file_type": "image_a",
                "file_path": f"camera_1/pictures/{event_id}_dummy.jpg",
                "transferred": False  # Use False so we don't interfere with tests
            }
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def verify_event_state(event: Dict[str, Any], expected_transfers: Dict[str, bool]) -> bool:
    """Verify event transfer flags match expected state"""
    if not event:
        print_fail("Event is None")
        return False
    
    all_match = True
    for file_type, expected in expected_transfers.items():
        field_name = f"{file_type}_transferred"
        actual = event.get(field_name)
        
        if actual == expected:
            print_pass(f"{field_name}: {actual} (expected {expected})")
        else:
            print_fail(f"{field_name}: {actual} (expected {expected})")
            all_match = False
    
    return all_match


def test_full_event_lifecycle():
    """Test 1: Full event lifecycle with all file updates"""
    print_section("Test 1: Full Event Lifecycle")
    
    event_id = create_test_event()
    if not event_id:
        return False
    
    # Initially all files should be not transferred
    print_test("Verifying initial state (all files not transferred)")
    event = get_event(event_id)
    if not event:
        print_fail("Could not retrieve event")
        return False
    
    if not verify_event_state(event, {
        "image_a": False,
        "image_b": False,
        "thumbnail": False,
        "video": False
    }):
        return False
    
    # Update image_a
    print_test("Updating image_a")
    event = update_file(event_id, "image_a", f"{TEST_CAMERA_ID}/pictures/{event_id}_test_a.jpg")
    if not event:
        return False
    print_pass("image_a updated")
    
    # Update thumbnail
    print_test("Updating thumbnail")
    event = update_file(event_id, "thumbnail", f"{TEST_CAMERA_ID}/thumbs/{event_id}_test_thumb.jpg")
    if not event:
        return False
    print_pass("thumbnail updated")
    
    # Update image_b
    print_test("Updating image_b")
    event = update_file(event_id, "image_b", f"{TEST_CAMERA_ID}/pictures/{event_id}_test_b.jpg")
    if not event:
        return False
    print_pass("image_b updated")
    
    # Update video with duration
    print_test("Updating video (with duration)")
    event = update_file(event_id, "video", f"{TEST_CAMERA_ID}/videos/{event_id}_test_video.h264", 
                   video_duration=30.5)
    if not event:
        return False
    print_pass("video updated with duration")
    
    # Verify all files transferred
    print_test("Verifying final state (all files transferred)")
    if not verify_event_state(event, {
        "image_a": True,
        "image_b": True,
        "thumbnail": True,
        "video": True
    }):
        return False
    
    # Verify video duration from the last update response
    if event and event.get('video_duration') == 30.5:
        print_pass(f"video_duration: {event['video_duration']}")
    else:
        print_fail(f"video_duration incorrect: {event.get('video_duration') if event else 'N/A'}")
        return False
    
    print_pass("Test 1 PASSED - Full lifecycle works correctly")
    return True


def test_nonexistent_event():
    """Test 2: Update non-existent event (should return 404)"""
    print_section("Test 2: Non-Existent Event (Error Handling)")
    
    print_test("Attempting to update non-existent event (ID 99999)")
    
    payload = {
        "file_type": "image_a",
        "file_path": "test.jpg",
        "transferred": True
    }
    
    try:
        response = requests.patch(f"{API_BASE_URL}/events/99999/files", json=payload)
        
        if response.status_code == 404:
            print_pass("Correctly returned 404 Not Found")
            data = response.json()
            if "not found" in data.get('detail', '').lower():
                print_pass(f"Error message: {data['detail']}")
                return True
            else:
                print_fail(f"Unexpected error message: {data.get('detail')}")
                return False
        else:
            print_fail(f"Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


def test_invalid_file_type():
    """Test 3: Invalid file_type (should return 422)"""
    print_section("Test 3: Invalid file_type (Validation)")
    
    event_id = create_test_event()
    if not event_id:
        return False
    
    print_test("Attempting to update with invalid file_type")
    
    payload = {
        "file_type": "invalid_type",
        "file_path": "test.jpg",
        "transferred": True
    }
    
    try:
        response = requests.patch(f"{API_BASE_URL}/events/{event_id}/files", json=payload)
        
        if response.status_code == 422:
            print_pass("Correctly returned 422 Unprocessable Entity")
            data = response.json()
            print_info(f"Validation error: {data.get('detail')}")
            return True
        else:
            print_fail(f"Expected 422, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


def test_video_duration_for_non_video():
    """Test 4: video_duration for non-video file_type (should return 422)"""
    print_section("Test 4: video_duration for Non-Video (Validation)")
    
    event_id = create_test_event()
    if not event_id:
        return False
    
    print_test("Attempting to set video_duration for image_a")
    
    payload = {
        "file_type": "image_a",
        "file_path": "test.jpg",
        "transferred": True,
        "video_duration": 30.5
    }
    
    try:
        response = requests.patch(f"{API_BASE_URL}/events/{event_id}/files", json=payload)
        
        if response.status_code == 422:
            print_pass("Correctly returned 422 Unprocessable Entity")
            data = response.json()
            print_info(f"Validation error: {data.get('detail')}")
            return True
        else:
            print_fail(f"Expected 422, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


def test_idempotency():
    """Test 5: Idempotency (update same file twice)"""
    print_section("Test 5: Idempotency")
    
    event_id = create_test_event()
    if not event_id:
        return False
    
    print_test("Updating image_a first time")
    event = update_file(event_id, "image_a", f"{TEST_CAMERA_ID}/pictures/first.jpg")
    if not event:
        return False
    print_pass("First update succeeded")
    
    first_path = event.get('image_a_path')
    print_info(f"image_a_path after first update: {first_path}")
    
    print_test("Updating image_a second time (different path)")
    event = update_file(event_id, "image_a", f"{TEST_CAMERA_ID}/pictures/second.jpg")
    if not event:
        return False
    print_pass("Second update succeeded")
    
    second_path = event.get('image_a_path')
    print_info(f"image_a_path after second update: {second_path}")
    
    if second_path == f"{TEST_CAMERA_ID}/pictures/second.jpg":
        print_pass("Path correctly overwritten (idempotent)")
        return True
    else:
        print_fail(f"Path not overwritten correctly: {second_path}")
        return False


def test_missing_required_field():
    """Test 6: Missing required field (should return 422)"""
    print_section("Test 6: Missing Required Field")
    
    event_id = create_test_event()
    if not event_id:
        return False
    
    print_test("Attempting to update without file_path")
    
    payload = {
        "file_type": "image_a",
        "transferred": True
        # Missing file_path
    }
    
    try:
        response = requests.patch(f"{API_BASE_URL}/events/{event_id}/files", json=payload)
        
        if response.status_code == 422:
            print_pass("Correctly returned 422 Unprocessable Entity")
            data = response.json()
            print_info(f"Validation error: {data.get('detail')}")
            return True
        else:
            print_fail(f"Expected 422, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}")
    print("  Session 1A-6: File Update Endpoint Test Suite")
    print(f"{'='*70}{RESET}\n")
    
    print_info(f"Testing API at: {API_BASE_URL}")
    print_info(f"Test camera ID: {TEST_CAMERA_ID}\n")
    
    # Setup
    if not register_test_camera():
        print_fail("Failed to register test camera - aborting tests")
        return
    
    # Run tests
    tests = [
        ("Full Event Lifecycle", test_full_event_lifecycle),
        ("Non-Existent Event", test_nonexistent_event),
        ("Invalid file_type", test_invalid_file_type),
        ("video_duration for Non-Video", test_video_duration_for_non_video),
        ("Idempotency", test_idempotency),
        ("Missing Required Field", test_missing_required_field),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_fail(f"Test crashed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}{'='*70}")
        print(f"  ✓ ALL TESTS PASSED")
        print(f"{'='*70}{RESET}\n")
    else:
        print(f"{RED}{'='*70}")
        print(f"  ✗ SOME TESTS FAILED")
        print(f"{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()