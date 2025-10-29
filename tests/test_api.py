#!/usr/bin/env python3
"""
Test script for Security Camera Central Server API
Run this after starting the API to verify basic functionality
"""
import requests
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Root endpoint returned: {data}")
        return True
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False


def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health")
        response.raise_for_status()
        data = response.json()
        
        print(f"Status: {data['status']}")
        print(f"Database Connected: {data['database_connected']}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Version: {data['version']}")
        
        if data['status'] == 'healthy' and data['database_connected']:
            print("✓ Health check passed")
            return True
        else:
            print("✗ Health check failed - unhealthy status")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_api_docs():
    """Test that API documentation is accessible"""
    print("\n=== Testing API Documentation ===")
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print(f"✓ Swagger UI accessible at {API_BASE_URL}/docs")
            return True
        else:
            print(f"✗ Swagger UI returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API documentation failed: {e}")
        return False


def test_404_handling():
    """Test that 404 errors are handled properly"""
    print("\n=== Testing 404 Error Handling ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/nonexistent")
        if response.status_code == 404:
            print("✓ 404 error handled correctly")
            return True
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 404 test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Security Camera Central Server API - Test Suite")
    print("=" * 60)
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Test started at: {datetime.now()}")
    
    # Check if API is running
    try:
        requests.get(f"{API_BASE_URL}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to API")
        print("Make sure the API is running: ./run_api.sh")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Health Check", test_health_check()))
    results.append(("API Documentation", test_api_docs()))
    results.append(("404 Handling", test_404_handling()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()