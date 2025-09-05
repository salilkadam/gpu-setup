#!/usr/bin/env python3
"""
Test script to verify that the routing system includes STT and TTS services
"""

import requests
import json
import time

def test_routing_api():
    """Test the routing API to ensure it includes STT and TTS"""
    print("🧪 Testing Routing API with Audio Services")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # Test cases for different use cases
    test_cases = [
        {
            "name": "STT Request",
            "query": "transcribe this audio file",
            "expected_use_case": "stt",
            "expected_endpoint": "http://localhost:8002"
        },
        {
            "name": "TTS Request", 
            "query": "synthesize speech from this text",
            "expected_use_case": "tts",
            "expected_endpoint": "http://localhost:8003"
        },
        {
            "name": "Agent Request",
            "query": "write a Python function to calculate fibonacci",
            "expected_use_case": "agent",
            "expected_endpoint": "http://localhost:8000"
        },
        {
            "name": "Multimodal Request",
            "query": "analyze this image and describe what you see",
            "expected_use_case": "multimodal", 
            "expected_endpoint": "http://localhost:8000"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Query: {test_case['query']}")
        
        try:
            # Test routing
            response = requests.post(
                f"{base_url}/route",
                json={
                    "query": test_case["query"],
                    "session_id": f"test_{int(time.time())}"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Routing successful")
                print(f"   Use Case: {result.get('use_case', 'unknown')}")
                print(f"   Endpoint: {result.get('endpoint', 'unknown')}")
                print(f"   Model: {result.get('model_id', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
                
                # Verify expected results
                if result.get('use_case') == test_case['expected_use_case']:
                    print(f"   ✅ Use case matches expected: {test_case['expected_use_case']}")
                else:
                    print(f"   ❌ Use case mismatch. Expected: {test_case['expected_use_case']}, Got: {result.get('use_case')}")
                
                if result.get('endpoint') == test_case['expected_endpoint']:
                    print(f"   ✅ Endpoint matches expected: {test_case['expected_endpoint']}")
                else:
                    print(f"   ❌ Endpoint mismatch. Expected: {test_case['expected_endpoint']}, Got: {result.get('endpoint')}")
                
                results.append({
                    "test": test_case['name'],
                    "success": True,
                    "use_case_match": result.get('use_case') == test_case['expected_use_case'],
                    "endpoint_match": result.get('endpoint') == test_case['expected_endpoint']
                })
                
            else:
                print(f"   ❌ Routing failed: {response.status_code}")
                print(f"   Response: {response.text}")
                results.append({
                    "test": test_case['name'],
                    "success": False,
                    "use_case_match": False,
                    "endpoint_match": False
                })
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "use_case_match": False,
                "endpoint_match": False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ROUTING TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    use_case_matches = sum(1 for r in results if r['use_case_match'])
    endpoint_matches = sum(1 for r in results if r['endpoint_match'])
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful Requests: {successful_tests}")
    print(f"Use Case Matches: {use_case_matches}")
    print(f"Endpoint Matches: {endpoint_matches}")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅ PASS" if result['success'] and result['use_case_match'] and result['endpoint_match'] else "❌ FAIL"
        print(f"   {result['test']}: {status}")
    
    # Check if STT and TTS are properly integrated
    stt_working = any(r['test'] == 'STT Request' and r['success'] and r['use_case_match'] and r['endpoint_match'] for r in results)
    tts_working = any(r['test'] == 'TTS Request' and r['success'] and r['use_case_match'] and r['endpoint_match'] for r in results)
    
    print(f"\n🎯 Audio Services Integration:")
    print(f"   STT Routing: {'✅ WORKING' if stt_working else '❌ NOT WORKING'}")
    print(f"   TTS Routing: {'✅ WORKING' if tts_working else '❌ NOT WORKING'}")
    
    if stt_working and tts_working:
        print(f"\n🎉 SUCCESS: Routing system properly integrates STT and TTS services!")
        return True
    else:
        print(f"\n⚠️ ISSUE: STT and/or TTS routing not working properly")
        return False

def test_direct_audio_services():
    """Test direct access to audio services"""
    print("\n🔊 Testing Direct Audio Services Access")
    print("=" * 60)
    
    # Test STT service
    print("🎤 Testing STT Service...")
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ STT service is healthy")
        else:
            print(f"   ❌ STT service unhealthy: {response.status_code}")
    except Exception as e:
        print(f"   ❌ STT service unreachable: {e}")
    
    # Test TTS service
    print("🔊 Testing TTS Service...")
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ TTS service is healthy")
        else:
            print(f"   ❌ TTS service unhealthy: {response.status_code}")
    except Exception as e:
        print(f"   ❌ TTS service unreachable: {e}")

def main():
    """Main test function"""
    print("🧪 Comprehensive Routing + Audio Services Test")
    print("=" * 60)
    print("Testing if routing system includes STT and TTS services")
    print("=" * 60)
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    # Test direct audio services
    test_direct_audio_services()
    
    # Test routing integration
    routing_success = test_routing_api()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULT")
    print("=" * 60)
    
    if routing_success:
        print("✅ SUCCESS: Routing system properly integrates STT and TTS services!")
        print("✅ All audio services are accessible through the routing API!")
    else:
        print("❌ FAILURE: Routing system does not properly integrate audio services")
        print("❌ STT and/or TTS services are not accessible through routing")
    
    return routing_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
