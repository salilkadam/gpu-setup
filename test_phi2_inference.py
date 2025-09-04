#!/usr/bin/env python3
import time
import requests
import json

def check_model_status():
    """Check if phi-2 model is ready."""
    try:
        response = requests.get("http://localhost:8000/v2/models/phi-2/ready", timeout=5)
        return response.status_code == 200
    except:
        return False

def make_inference_request():
    """Make an inference request to phi-2."""
    payload = {
        "inputs": [
            {
                "name": "text_input",
                "shape": [1],
                "datatype": "BYTES",
                "data": ["Hello, how are you?"]
            }
        ],
        "outputs": [
            {
                "name": "text_output",
                "shape": [1],
                "datatype": "BYTES"
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v2/models/phi-2/infer",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def main():
    print("🔄 Monitoring Phi-2 model status...")
    
    # Wait for model to be ready
    max_wait = 60  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if check_model_status():
            print("✅ Phi-2 model is READY!")
            break
        print("⏳ Waiting for model to be ready...")
        time.sleep(2)
    else:
        print("❌ Model did not become ready within timeout")
        return
    
    # Make inference request
    print("🚀 Making inference request...")
    status_code, response_text = make_inference_request()
    
    if status_code == 200:
        print(f"✅ Inference successful! Status: {status_code}")
        print(f"📝 Response: {response_text}")
    else:
        print(f"❌ Inference failed! Status: {status_code}")
        print(f"📝 Response: {response_text}")

if __name__ == "__main__":
    main()
