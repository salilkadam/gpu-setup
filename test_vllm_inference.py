#!/usr/bin/env python3
"""
vLLM Inference Test Script for Blackwell GPUs
Tests basic vLLM functionality after compilation
"""

import requests
import json
import time
import sys

def test_vllm_health():
    """Test vLLM health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ vLLM health check passed")
            return True
        else:
            print(f"❌ vLLM health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ vLLM health check error: {e}")
        return False

def test_vllm_completion():
    """Test vLLM text completion"""
    try:
        payload = {
            "model": "phi-2",
            "prompt": "Hello, how are you?",
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        response = requests.post(
            "http://localhost:8000/v1/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ vLLM completion test passed")
            print(f"Response: {result['choices'][0]['text']}")
            return True
        else:
            print(f"❌ vLLM completion test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ vLLM completion test error: {e}")
        return False

def test_vllm_chat():
    """Test vLLM chat completion"""
    try:
        payload = {
            "model": "phi-2",
            "messages": [
                {"role": "user", "content": "What is the capital of France?"}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ vLLM chat test passed")
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ vLLM chat test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ vLLM chat test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting vLLM Inference Tests for Blackwell GPUs")
    print("=" * 60)
    
    # Wait for vLLM to be ready
    print("⏳ Waiting for vLLM to be ready...")
    time.sleep(10)
    
    tests = [
        ("Health Check", test_vllm_health),
        ("Text Completion", test_vllm_completion),
        ("Chat Completion", test_vllm_chat)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! vLLM is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check vLLM configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
