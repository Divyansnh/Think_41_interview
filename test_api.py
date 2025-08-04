#!/usr/bin/env python3
"""
API Test Script - Test all endpoints using requests
Run this after starting the Flask app to verify all endpoints work correctly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, expected_status=200, params=None):
    """Test an API endpoint and return the result"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.request(method, url, timeout=10)
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code == expected_status:
            try:
                data = response.json()
                print(f"   Response keys: {list(data.keys())}")
                return True, data
            except json.JSONDecodeError:
                print(f"   Response: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False, None

def main():
    """Run all API tests"""
    print("🚀 Testing Customer API Endpoints")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ API server is not responding correctly")
            print("   Make sure to start the Flask app first: python app.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server")
        print("   Make sure to start the Flask app first: python app.py")
        sys.exit(1)
    
    print("✅ API server is running")
    print()
    
    # Test all endpoints
    tests = [
        # Basic endpoints
        ("GET", "/", 200),
        ("GET", "/api/health", 200),
        
        # Customer listing with different parameters
        ("GET", "/api/customers", 200),
        ("GET", "/api/customers", 200, {"page": 1, "limit": 5}),
        ("GET", "/api/customers", 200, {"page": 1, "limit": 10, "search": "test"}),
        
        # Customer details (test with ID 1, might not exist but should handle gracefully)
        ("GET", "/api/customers/1", None),  # Could be 200 or 404
        
        # Error cases
        ("GET", "/api/customers/0", 400),      # Invalid ID
        ("GET", "/api/customers/-1", 400),     # Invalid ID
        ("GET", "/api/customers/abc", 404),    # Non-numeric ID (Flask handles this)
        ("GET", "/api/customers/99999", 404),  # Non-existent customer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        method, endpoint = test[0], test[1]
        expected_status = test[2] if len(test) > 2 else 200
        params = test[3] if len(test) > 3 else None
        
        # For customer detail endpoint, accept both 200 and 404
        if endpoint == "/api/customers/1":
            success, data = test_endpoint(method, endpoint, params=params)
            if success:
                passed += 1
        else:
            success, data = test_endpoint(method, endpoint, expected_status, params)
            if success:
                passed += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📝 Manual Testing Commands:")
    print("curl \"http://localhost:5000/api/customers\"")
    print("curl \"http://localhost:5000/api/customers?page=1&limit=5\"")
    print("curl \"http://localhost:5000/api/customers/1\"")
    print("curl \"http://localhost:5000/api/health\"")

if __name__ == "__main__":
    main()
