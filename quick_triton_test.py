#!/usr/bin/env python3
"""
Quick Triton Server Test Script
===============================

This script quickly tests the current Triton server status and identifies issues.
"""

import requests
import json
import time
import sys

def test_triton_server():
    """Test Triton server functionality"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Triton Inference Server...")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Health Check:")
    try:
        response = requests.get(f"{base_url}/v2/health/ready", timeout=10)
        if response.status_code == 200:
            print("   ✅ Server is healthy")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Models List
    print("\n2. Models List:")
    try:
        response = requests.get(f"{base_url}/v2/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"   ✅ Models endpoint working, found {len(models)} models")
            for model in models:
                print(f"      - {model.get('name', 'Unknown')}: {model.get('state', 'Unknown')}")
        else:
            print(f"   ❌ Models endpoint failed: {response.status_code}")
            if response.status_code == 404:
                print("      This suggests no models are loaded or the endpoint is not working")
    except Exception as e:
        print(f"   ❌ Models endpoint error: {e}")
    
    # Test 3: Specific Model Info
    print("\n3. Phi-2 Model Info:")
    try:
        response = requests.get(f"{base_url}/v2/models/phi-2", timeout=10)
        if response.status_code == 200:
            model_info = response.json()
            print("   ✅ Phi-2 model info retrieved")
            print(f"      - Backend: {model_info.get('backend', 'Unknown')}")
            print(f"      - Status: {model_info.get('state', 'Unknown')}")
            print(f"      - Inputs: {len(model_info.get('inputs', []))}")
            print(f"      - Outputs: {len(model_info.get('outputs', []))}")
        else:
            print(f"   ❌ Phi-2 model info failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Phi-2 model info error: {e}")
    
    # Test 4: Model Ready Check
    print("\n4. Model Ready Check:")
    try:
        response = requests.get(f"{base_url}/v2/models/phi-2/ready", timeout=10)
        if response.status_code == 200:
            print("   ✅ Phi-2 model is ready")
        else:
            print(f"   ❌ Phi-2 model ready check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Phi-2 model ready check error: {e}")
    
    # Test 5: Simple Inference Test
    print("\n5. Simple Inference Test:")
    try:
        # Test with minimal input
        test_input = {
            "inputs": [],
            "outputs": [{"name": "text_output"}]
        }
        
        response = requests.post(
            f"{base_url}/v2/models/phi-2/infer",
            json=test_input,
            timeout=30
        )
        
        if response.status_code == 200:
            print("   ✅ Inference successful")
            result = response.json()
            print(f"      - Response: {result}")
        else:
            print(f"   ❌ Inference failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"      - Error: {error_detail}")
            except:
                print(f"      - Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Inference error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("   - If health check passes but models fail, the server is running but has model issues")
    print("   - If models endpoint returns 404, no models are loaded")
    print("   - If inference fails, the model configuration has issues")
    
    return True

if __name__ == "__main__":
    try:
        success = test_triton_server()
        if success:
            print("\n✅ Quick test completed successfully")
        else:
            print("\n❌ Quick test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
