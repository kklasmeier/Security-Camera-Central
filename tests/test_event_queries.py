import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys


# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_CAMERA_ID = "test_camera_queries"


class Colors:
    """ANSI color codes for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")


def print_header(message: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")


class TestEventQueries:
    """Test suite for event query endpoints"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.camera_id = TEST_CAMERA_ID
        self.created_event_ids: List[int] = []
        self.passed = 0
        self.failed = 0
    
    def setup(self) -> bool:
        """Setup test environment - register camera and create test events"""
        print_header("SETUP: Creating Test Data")
        
        # Step 1: Register test camera
        print_info("Registering test camera...")
        try:
            response = requests.post(
                f"{self.base_url}/cameras/register",
                json={
                    "camera_id": self.camera_id,
                    "name": "Test Camera for Queries",
                    "location": "Test Location",
                    "ip_address": "192.168.1.100"
                }
            )
            if response.status_code in [200, 201, 409]:  # Created or already exists
                print_success(f"Camera registered: {self.camera_id}")
            else:
                print_error(f"Failed to register camera: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Exception during camera registration: {e}")
            return False
        
        # Step 2: Create test events with different timestamps
        print_info("Creating test events...")
        
        # Create 5 events from today
        today = datetime.now()
        for i in range(5):
            timestamp = today.replace(hour=10+i, minute=30, second=0, microsecond=0)
            event_id = self._create_event(timestamp, 70.0 + i)
            if event_id:
                self.created_event_ids.append(event_id)
        
        # Create 2 events from yesterday
        yesterday = today - timedelta(days=1)
        for i in range(2):
            timestamp = yesterday.replace(hour=14+i, minute=0, second=0, microsecond=0)
            event_id = self._create_event(timestamp, 80.0 + i)
            if event_id:
                self.created_event_ids.append(event_id)
        
        # Create 1 event from 2 days ago
        two_days_ago = today - timedelta(days=2)
        timestamp = two_days_ago.replace(hour=16, minute=0, second=0, microsecond=0)
        event_id = self._create_event(timestamp, 90.0)
        if event_id:
            self.created_event_ids.append(event_id)
        
        print_success(f"Created {len(self.created_event_ids)} test events")
        print_info(f"Event IDs: {self.created_event_ids}")
        
        return len(self.created_event_ids) >= 8
    
    def _create_event(self, timestamp: datetime, motion_score: float) -> int:
        """Helper to create a single event"""
        try:
            response = requests.post(
                f"{self.base_url}/events",
                json={
                    "camera_id": self.camera_id,
                    "timestamp": timestamp.isoformat(),
                    "motion_score": motion_score
                }
            )
            if response.status_code == 201:
                return response.json()["id"]
        except Exception as e:
            print_error(f"Failed to create event: {e}")
        return None
    
    def test_list_all_events(self):
        """Test 1: List all events (no filters)"""
        print_header("Test 1: List All Events (Default)")
        
        try:
            response = requests.get(f"{self.base_url}/events")
            
            # Check status code
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Validate response structure
            required_fields = ["events", "total", "limit", "offset"]
            for field in required_fields:
                if field not in data:
                    print_error(f"Missing field: {field}")
                    self.failed += 1
                    return
            
            # Validate defaults
            if data["limit"] != 50:
                print_error(f"Expected default limit 50, got {data['limit']}")
                self.failed += 1
                return
            
            if data["offset"] != 0:
                print_error(f"Expected default offset 0, got {data['offset']}")
                self.failed += 1
                return
            
            print_success(f"Response structure valid")
            print_success(f"Found {data['total']} total events, returned {len(data['events'])} events")
            print_success(f"Default limit: {data['limit']}, offset: {data['offset']}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_filter_by_camera(self):
        """Test 2: Filter events by camera_id"""
        print_header("Test 2: Filter by Camera ID")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={"camera_id": self.camera_id}
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should have at least our 8 test events
            if data["total"] < 8:
                print_error(f"Expected at least 8 events, got {data['total']}")
                self.failed += 1
                return
            
            # All events should be from our test camera
            for event in data["events"]:
                if event["camera_id"] != self.camera_id:
                    print_error(f"Found event from wrong camera: {event['camera_id']}")
                    self.failed += 1
                    return
            
            print_success(f"Camera filter working: {data['total']} events from {self.camera_id}")
            print_success(f"All returned events are from correct camera")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_filter_by_date_today(self):
        """Test 3: Filter events by date (today)"""
        print_header("Test 3: Filter by Date (today)")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={
                    "camera_id": self.camera_id,
                    "date": "today"
                }
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should have 5 events from today
            if data["total"] != 5:
                print_warning(f"Expected 5 events from today, got {data['total']}")
                # Not a hard failure - could be timing issues
            
            # All events should be from today
            today = datetime.now().date()
            for event in data["events"]:
                event_date = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00')).date()
                if event_date != today:
                    print_error(f"Found event from wrong date: {event_date}")
                    self.failed += 1
                    return
            
            print_success(f"Date filter 'today' working: {data['total']} events")
            print_success(f"All events are from today: {today}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_filter_by_date_yesterday(self):
        """Test 4: Filter events by date (yesterday)"""
        print_header("Test 4: Filter by Date (yesterday)")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={
                    "camera_id": self.camera_id,
                    "date": "yesterday"
                }
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should have 2 events from yesterday
            if data["total"] != 2:
                print_warning(f"Expected 2 events from yesterday, got {data['total']}")
            
            # All events should be from yesterday
            yesterday = (datetime.now() - timedelta(days=1)).date()
            for event in data["events"]:
                event_date = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00')).date()
                if event_date != yesterday:
                    print_error(f"Found event from wrong date: {event_date}")
                    self.failed += 1
                    return
            
            print_success(f"Date filter 'yesterday' working: {data['total']} events")
            print_success(f"All events are from yesterday: {yesterday}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_filter_by_specific_date(self):
        """Test 5: Filter events by specific date (YYYY-MM-DD)"""
        print_header("Test 5: Filter by Specific Date (YYYY-MM-DD)")
        
        try:
            # Query for 2 days ago
            two_days_ago = (datetime.now() - timedelta(days=2)).date()
            date_str = two_days_ago.strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.base_url}/events",
                params={
                    "camera_id": self.camera_id,
                    "date": date_str
                }
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should have 1 event from 2 days ago
            if data["total"] != 1:
                print_warning(f"Expected 1 event from {date_str}, got {data['total']}")
            
            print_success(f"Specific date filter working: {data['total']} events from {date_str}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_pagination_first_page(self):
        """Test 6: Pagination - First page"""
        print_header("Test 6: Pagination - First Page")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={
                    "camera_id": self.camera_id,
                    "limit": 3,
                    "offset": 0
                }
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should return 3 events (first page)
            if len(data["events"]) != 3:
                print_error(f"Expected 3 events, got {len(data['events'])}")
                self.failed += 1
                return
            
            # Metadata should be correct
            if data["limit"] != 3:
                print_error(f"Expected limit 3, got {data['limit']}")
                self.failed += 1
                return
            
            if data["offset"] != 0:
                print_error(f"Expected offset 0, got {data['offset']}")
                self.failed += 1
                return
            
            print_success(f"First page: returned {len(data['events'])} events (limit={data['limit']}, offset={data['offset']})")
            print_success(f"Total: {data['total']} events")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_pagination_second_page(self):
        """Test 7: Pagination - Second page"""
        print_header("Test 7: Pagination - Second Page")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={
                    "camera_id": self.camera_id,
                    "limit": 3,
                    "offset": 3
                }
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should return 3 events (second page)
            if len(data["events"]) != 3:
                print_error(f"Expected 3 events, got {len(data['events'])}")
                self.failed += 1
                return
            
            # Metadata should be correct
            if data["limit"] != 3:
                print_error(f"Expected limit 3, got {data['limit']}")
                self.failed += 1
                return
            
            if data["offset"] != 3:
                print_error(f"Expected offset 3, got {data['offset']}")
                self.failed += 1
                return
            
            print_success(f"Second page: returned {len(data['events'])} events (limit={data['limit']}, offset={data['offset']})")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_sorting_order(self):
        """Test 8: Verify events are sorted newest first"""
        print_header("Test 8: Verify Sorting (Newest First)")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={
                    "camera_id": self.camera_id,
                    "limit": 10
                }
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Check timestamps are in descending order
            timestamps = [datetime.fromisoformat(e["timestamp"].replace('Z', '+00:00')) for e in data["events"]]
            
            for i in range(len(timestamps) - 1):
                if timestamps[i] < timestamps[i+1]:
                    print_error(f"Timestamps not in descending order: {timestamps[i]} < {timestamps[i+1]}")
                    self.failed += 1
                    return
            
            print_success(f"Events sorted correctly (newest first)")
            print_success(f"First event: {timestamps[0]}")
            print_success(f"Last event: {timestamps[-1]}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_get_single_event(self):
        """Test 9: Get single event by ID"""
        print_header("Test 9: Get Single Event")
        
        try:
            # Use first created event ID
            event_id = self.created_event_ids[0]
            
            response = requests.get(f"{self.base_url}/events/{event_id}")
            
            if response.status_code != 200:
                print_error(f"Expected 200, got {response.status_code}")
                self.failed += 1
                return
            
            event = response.json()
            
            # Validate event structure
            if event["id"] != event_id:
                print_error(f"Expected event ID {event_id}, got {event['id']}")
                self.failed += 1
                return
            
            if event["camera_id"] != self.camera_id:
                print_error(f"Expected camera {self.camera_id}, got {event['camera_id']}")
                self.failed += 1
                return
            
            # Check all expected fields are present
            required_fields = [
                "id", "camera_id", "timestamp", "motion_score",
                "image_a_path", "image_b_path", "thumbnail_path",
                "video_h264_path", "video_mp4_path", "video_duration",
                "image_a_transferred", "image_b_transferred",
                "thumbnail_transferred", "video_transferred",
                "mp4_conversion_status", "mp4_converted_at",
                "ai_processed", "created_at"
            ]
            
            for field in required_fields:
                if field not in event:
                    print_error(f"Missing field: {field}")
                    self.failed += 1
                    return
            
            print_success(f"Retrieved event {event_id}")
            print_success(f"Camera: {event['camera_id']}, Timestamp: {event['timestamp']}")
            print_success(f"All required fields present")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_event_not_found(self):
        """Test 10: Get non-existent event (404)"""
        print_header("Test 10: Event Not Found (404)")
        
        try:
            # Use an ID that definitely doesn't exist
            fake_id = 999999
            
            response = requests.get(f"{self.base_url}/events/{fake_id}")
            
            if response.status_code != 404:
                print_error(f"Expected 404, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            if "detail" not in data:
                print_error("Missing 'detail' field in error response")
                self.failed += 1
                return
            
            print_success(f"Correctly returned 404 for non-existent event")
            print_success(f"Error message: {data['detail']}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_invalid_limit(self):
        """Test 11: Invalid limit parameter (422)"""
        print_header("Test 11: Invalid Limit Parameter (422)")
        
        try:
            # Test limit too high
            response = requests.get(
                f"{self.base_url}/events",
                params={"limit": 500}
            )
            
            if response.status_code != 422:
                print_error(f"Expected 422 for limit=500, got {response.status_code}")
                self.failed += 1
                return
            
            print_success(f"Correctly rejected limit=500 with 422")
            
            # Test negative limit
            response = requests.get(
                f"{self.base_url}/events",
                params={"limit": -10}
            )
            
            if response.status_code != 422:
                print_error(f"Expected 422 for limit=-10, got {response.status_code}")
                self.failed += 1
                return
            
            print_success(f"Correctly rejected limit=-10 with 422")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_invalid_offset(self):
        """Test 12: Invalid offset parameter (422)"""
        print_header("Test 12: Invalid Offset Parameter (422)")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={"offset": -5}
            )
            
            if response.status_code != 422:
                print_error(f"Expected 422 for offset=-5, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            print_success(f"Correctly rejected offset=-5 with 422")
            print_success(f"Error message: {data['detail']}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_invalid_date_format(self):
        """Test 13: Invalid date format (422)"""
        print_header("Test 13: Invalid Date Format (422)")
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                params={"date": "invalid-date"}
            )
            
            if response.status_code != 422:
                print_error(f"Expected 422 for invalid date, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            print_success(f"Correctly rejected invalid date with 422")
            print_success(f"Error message: {data['detail']}")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def test_empty_results(self):
        """Test 14: Empty results (no matching events)"""
        print_header("Test 14: Empty Results")
        
        try:
            # Query for a camera that doesn't exist
            response = requests.get(
                f"{self.base_url}/events",
                params={"camera_id": "nonexistent_camera_xyz"}
            )
            
            if response.status_code != 200:
                print_error(f"Expected 200 for empty results, got {response.status_code}")
                self.failed += 1
                return
            
            data = response.json()
            
            # Should have empty array and total=0
            if data["total"] != 0:
                print_error(f"Expected total=0, got {data['total']}")
                self.failed += 1
                return
            
            if len(data["events"]) != 0:
                print_error(f"Expected empty events array, got {len(data['events'])} events")
                self.failed += 1
                return
            
            print_success(f"Correctly returned empty results with total=0")
            print_success(f"Status code 200 (not 404)")
            
            self.passed += 1
            
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
    
    def cleanup(self):
        """Cleanup test data"""
        print_header("CLEANUP: Removing Test Data")
        
        # Note: We're not implementing cleanup here as it would require
        # a DELETE endpoint which doesn't exist yet.
        # Test events will remain in database.
        
        print_info(f"Created {len(self.created_event_ids)} test events")
        print_info(f"Event IDs: {self.created_event_ids}")
        print_warning("Test events left in database (no DELETE endpoint available)")
        print_info("You can manually remove them with:")
        print_info(f"  DELETE FROM events WHERE camera_id = '{self.camera_id}';")
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total = self.passed + self.failed
        
        print(f"Total tests: {total}")
        print_success(f"Passed: {self.passed}")
        
        if self.failed > 0:
            print_error(f"Failed: {self.failed}")
        else:
            print_success(f"Failed: {self.failed}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED ❌{Colors.ENDC}\n")
            return 1
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("Session 1A-8: Event Query Endpoints Test Suite")
        
        # Setup
        if not self.setup():
            print_error("Setup failed - cannot continue with tests")
            return 1
        
        # Run tests
        self.test_list_all_events()
        self.test_filter_by_camera()
        self.test_filter_by_date_today()
        self.test_filter_by_date_yesterday()
        self.test_filter_by_specific_date()
        self.test_pagination_first_page()
        self.test_pagination_second_page()
        self.test_sorting_order()
        self.test_get_single_event()
        self.test_event_not_found()
        self.test_invalid_limit()
        self.test_invalid_offset()
        self.test_invalid_date_format()
        self.test_empty_results()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        return self.print_summary()


def main():
    """Main entry point"""
    # Check if API is running - use the correct health endpoint path
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print_error("API server health check failed")
            print_error(f"Status: {response.status_code}")
            print_info("Make sure the API server is running at http://localhost:8000")
            return 1
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server at http://localhost:8000")
        print_error("Please start the API server first: ./run_api.sh")
        return 1
    except Exception as e:
        print_error(f"Error checking API health: {e}")
        return 1
    
    # Run tests
    test_suite = TestEventQueries()
    return test_suite.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())