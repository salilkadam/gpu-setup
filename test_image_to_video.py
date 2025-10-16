#!/usr/bin/env python3
"""
Test script for image-to-video generation using the Wan service
"""

import requests
import json
import base64
import time

def test_image_to_video():
    """Test the image-to-video generation endpoint"""
    
    # Service URL
    base_url = "http://localhost:8004"
    
    # Read the sample image and encode it
    with open("/app/sample_image.jpg", "rb") as f:
        image_data = f.read()
    
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare the request payload
    payload = {
        "task": "ti2v-5B",  # Text-Image-to-Video model
        "prompt": "A beautiful mountain landscape with flowing water and gentle movement",
        "image_path": "/app/sample_image.jpg",  # Path to the image file
        "size": "1280x704",  # Supported size for ti2v-5B
        "frame_num": 25,  # Reduced for faster testing
        "sample_steps": 20,  # Reduced for faster testing
        "sample_guide_scale": 5.0,
        "base_seed": 42,
        "save_file": "true"  # String, not boolean
    }
    
    print("🚀 Testing image-to-video generation...")
    print(f"📝 Prompt: {payload['prompt']}")
    print(f"🖼️  Image size: {len(image_data)} bytes")
    print(f"📐 Output size: {payload['size']}")
    print(f"🎬 Frames: {payload['frame_num']}")
    print(f"⚡ Steps: {payload['sample_steps']}")
    
    try:
        # Make the request
        print("\n📡 Sending request to /generate/image-to-video...")
        response = requests.post(
            f"{base_url}/generate/image-to-video",
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"🎯 Task ID: {result.get('task_id', 'N/A')}")
            print(f"⏱️  Generation time: {result.get('generation_time', 'N/A')} seconds")
            print(f"📁 Output file: {result.get('output_file', 'N/A')}")
            print(f"📏 Video size: {result.get('video_size', 'N/A')}")
            return True
        else:
            print("❌ Error!")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes)")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the service running?")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_image_to_video()
    if success:
        print("\n🎉 Image-to-video generation test completed successfully!")
    else:
        print("\n😞 Image-to-video generation test failed!")
