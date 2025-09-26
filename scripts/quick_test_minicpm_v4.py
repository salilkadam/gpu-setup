#!/usr/bin/env python3
"""
Quick test of MiniCPM-V-4 capabilities
"""

import requests
import json

def test_minicpm_v4():
    """Test MiniCPM-V-4 with a simple text query"""
    print("🧪 Testing MiniCPM-V-4")
    print("=" * 40)
    
    url = "http://192.168.0.20:8000/v1/chat/completions"
    
    payload = {
        "model": "/app/models/multimodal/minicpm-v-4",
        "messages": [{
            "role": "user",
            "content": "Explain the concept of temporal context in video processing in 2-3 sentences."
        }],
        "max_tokens": 200,
        "temperature": 0.7
    }
    
    try:
        print("📤 Sending request...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ Response received:")
            print(f"   {content}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_minicpm_v4()
    if success:
        print("\n✅ MiniCPM-V-4 is working correctly!")
    else:
        print("\n❌ MiniCPM-V-4 test failed!")
