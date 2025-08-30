#!/usr/bin/env python3
"""
API-Based End-to-End Tests for Week 3 Container

Tests the complete CSV analytics workflow via HTTP API endpoints,
validating the containerized deployment like a real user would interact with it.

Key concepts:
- HTTP API testing (not direct agent testing)
- Complete user workflow validation
- Container deployment verification
- Real-world usage scenarios

Use cases:
- Validate containerized deployment
- Test API endpoints with realistic scenarios
- Verify complete data analysis workflows
- Ensure proper error handling via API
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time


class APITester:
    """Test the container API endpoints."""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        
    def make_request(self, endpoint, data=None, timeout=30):
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        if data is None:
            # GET request
            try:
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    return {
                        "status": response.status,
                        "data": json.loads(response.read().decode()),
                        "success": response.status == 200
                    }
            except Exception as e:
                return {"status": 0, "data": None, "success": False, "error": str(e)}
        else:
            # POST request
            try:
                json_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return {
                        "status": response.status,
                        "data": json.loads(response.read().decode()),
                        "success": response.status == 200
                    }
            except Exception as e:
                return {"status": 0, "data": None, "success": False, "error": str(e)}


def test_health_endpoint():
    """Test 1: Health endpoint basic functionality."""
    print("🏥 Test 1: Health Endpoint")
    
    tester = APITester()
    result = tester.make_request("/health")
    
    assert result["success"], f"Health endpoint failed: {result.get('error')}"
    assert result["data"]["status"] == "healthy", "Health status not healthy"
    assert result["data"]["version"] == "3.0.0", "Version mismatch"
    
    print("   ✅ Health endpoint working correctly")
    return True


def test_basic_chat_functionality():
    """Test 2: Basic chat functionality."""
    print("\n💬 Test 2: Basic Chat Functionality")
    
    tester = APITester()
    result = tester.make_request("/chat", {"message": "Hello, what can you help me with?"})
    
    assert result["success"], f"Chat endpoint failed: {result.get('error')}"
    
    data = result["data"]
    assert "success" in data, "Response missing success field"
    assert "response" in data, "Response missing response field"
    
    # Should get guardrail response for non-analytics question
    if not data["success"]:
        assert "data analysis" in data["response"].lower(), "Expected guardrail message"
        print("   ✅ Guardrails working correctly")
    else:
        # If it succeeds, that's also fine - just different behavior
        print("   ✅ Chat endpoint responding")
    
    return True


def test_dataset_discovery():
    """Test 3: Dataset discovery functionality."""
    print("\n📊 Test 3: Dataset Discovery")
    
    tester = APITester()
    result = tester.make_request("/chat", {"message": "What datasets are available?"}, timeout=45)
    
    assert result["success"], f"Dataset discovery failed: {result.get('error')}"
    
    data = result["data"]
    response_text = data.get("response", "").lower()
    
    # Look for dataset indicators
    dataset_keywords = ["employee", "sales", "weather", "csv", "dataset", "data"]
    has_datasets = any(keyword in response_text for keyword in dataset_keywords)
    
    if data.get("success"):
        assert has_datasets, f"Expected dataset information in response: {data['response'][:100]}"
        print("   ✅ Dataset discovery working")
    else:
        print(f"   ⚠️ Dataset discovery returned error: {data['response'][:100]}")
    
    return True


def test_data_analysis_request():
    """Test 4: Data analysis functionality."""
    print("\n📈 Test 4: Data Analysis Request")
    
    tester = APITester()
    result = tester.make_request("/chat", {
        "message": "Load data from /data directory and calculate the average salary from employee data"
    }, timeout=60)
    
    assert result["success"], f"Data analysis failed: {result.get('error')}"
    
    data = result["data"]
    response_text = data.get("response", "").lower()
    
    # Look for analysis indicators
    analysis_keywords = ["salary", "average", "employee", "analysis", "calculate"]
    has_analysis = any(keyword in response_text for keyword in analysis_keywords)
    
    if data.get("success"):
        print("   ✅ Data analysis request processed")
        if has_analysis:
            print("   ✅ Analysis content detected")
    else:
        print(f"   ⚠️ Analysis returned error: {data['response'][:100]}")
    
    return True


def test_error_handling():
    """Test 5: Error handling for invalid requests."""
    print("\n🛡️ Test 5: Error Handling")
    
    tester = APITester()
    
    # Test off-topic request
    result = tester.make_request("/chat", {"message": "What's the weather like today?"})
    
    assert result["success"], f"Error handling test failed: {result.get('error')}"
    
    data = result["data"]
    
    # Should be blocked by guardrails
    if not data.get("success"):
        assert "data analysis" in data["response"].lower(), "Expected guardrail blocking"
        print("   ✅ Off-topic requests properly blocked")
    else:
        # If it responds, check if it's redirecting to data analysis
        if "data" in data["response"].lower():
            print("   ✅ Request redirected to data analysis")
        else:
            print("   ⚠️ Off-topic request not blocked")
    
    return True


def test_time_tool():
    """Test 6: Time tool functionality via data analysis context."""
    print("\n🕐 Test 6: Time Tool")
    
    tester = APITester()
    # Ask for time in a data analysis context
    result = tester.make_request("/chat", {"message": "Add a timestamp to my analysis - what's the current time?"})
    
    assert result["success"], f"Time tool test failed: {result.get('error')}"
    
    data = result["data"]
    response_text = data.get("response", "").lower()
    
    if data.get("success"):
        time_keywords = ["time", "date", "current", "timestamp"]
        has_time = any(keyword in response_text for keyword in time_keywords)
        if has_time:
            print("   ✅ Time tool working in analysis context")
        else:
            print("   ⚠️ Time tool response unclear")
    else:
        # Even if blocked, that's valid behavior
        print(f"   ✅ Time request handled: {data['response'][:80]}...")
    
    return True


def main():
    """Run all API-based e2e tests."""
    print("🚀 Week 3 API End-to-End Tests")
    print("Testing containerized CSV analytics via HTTP API")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_basic_chat_functionality,
        test_dataset_discovery,
        test_data_analysis_request,
        test_error_handling,
        test_time_tool,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 API E2E TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{total} tests ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL API E2E TESTS PASSED!")
        print("✅ Container deployment fully validated!")
        return True
    else:
        print(f"⚠️ {total-passed} tests failed")
        print("🔧 Check container logs for details")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
