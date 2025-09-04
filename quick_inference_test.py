#!/usr/bin/env python3

import requests
import json
import time
import sys

def test_inference():
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Triton Inference...")
    
    # Wait for model to be ready
    max_attempts = 60  # 60 seconds
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/v2/models/phi-2")
            if response.status_code == 200:
                model_data = response.json()
                if model_data.get("state") == "READY":
                    print(f"✅ Model is READY! (attempt {attempt + 1})")
                    break
            print(f"⏳ Waiting for model... (attempt {attempt + 1})")
            time.sleep(1)
        except Exception as e:
            print(f"⏳ Waiting for server... (attempt {attempt + 1})")
            time.sleep(1)
    else:
        print("❌ Model never became ready")
        return False
    
    # Now make an inference request immediately
    print("🔥 Making inference request...")
    
    inference_data = {
        "inputs": [
            {
                "name": "text_input",
                "shape": [1],
                "datatype": "BYTES",
                "data": ["Hello, how are you today?"]
            }
        ],
        "outputs": [
            {
                "name": "text_output"
            }
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/v2/models/phi-2/infer",
            json=inference_data,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        print(f"⚡ Response time: {end_time - start_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            output_data = result["outputs"][0]["data"][0]
            print(f"✅ SUCCESS! Model response: {output_data}")
            return True
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_inference()
    sys.exit(0 if success else 1)
