#!/usr/bin/env python3
"""
Test script to compare MiniCPM-V-4 vs MiniCPM-V-4.5 capabilities
Focus on video processing and temporal context understanding
"""

import requests
import json
import base64
import time
from pathlib import Path

def test_model_capabilities(model_name, base_url, test_cases):
    """Test model capabilities with various inputs"""
    print(f"\n🧪 Testing {model_name}")
    print("=" * 50)
    
    results = {}
    
    for test_name, test_data in test_cases.items():
        print(f"\n📋 Test: {test_name}")
        print("-" * 30)
        
        try:
            # Prepare the request
            payload = {
                "model": model_name,
                "messages": test_data["messages"],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Add image if present
            if "image" in test_data:
                payload["messages"][0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{test_data['image']}"}
                })
            
            # Make the request
            start_time = time.time()
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                response_time = end_time - start_time
                
                print(f"✅ Response ({response_time:.2f}s):")
                print(f"   {content[:200]}{'...' if len(content) > 200 else ''}")
                
                results[test_name] = {
                    "status": "success",
                    "response": content,
                    "response_time": response_time,
                    "tokens": result.get("usage", {}).get("total_tokens", 0)
                }
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                results[test_name] = {
                    "status": "error",
                    "error": f"{response.status_code}: {response.text}"
                }
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results[test_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

def create_test_image():
    """Create a simple test image"""
    # Create a simple 100x100 red square as base64
    from PIL import Image
    import io
    
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def main():
    print("🚀 MiniCPM-V-4 vs V-4.5 Capability Comparison Test")
    print("=" * 60)
    
    # Test configurations
    models = {
        "MiniCPM-V-4": "http://192.168.0.20:8000",
        "MiniCPM-V-4.5": "http://192.168.0.20:8004"  # Running on port 8004
    }
    
    # Create test image
    print("📸 Creating test image...")
    test_image = create_test_image()
    
    # Test cases focusing on video/temporal understanding
    test_cases = {
        "text_reasoning": {
            "messages": [{
                "role": "user",
                "content": "Explain the concept of temporal context in video processing. How does it differ from frame-by-frame analysis?"
            }]
        },
        
        "image_analysis": {
            "messages": [{
                "role": "user", 
                "content": "Describe what you see in this image. Focus on any temporal or motion-related aspects you can infer."
            }],
            "image": test_image
        },
        
        "video_scenario": {
            "messages": [{
                "role": "user",
                "content": "Imagine you're analyzing a video sequence where a person walks from left to right across the frame, then turns around and walks back. How would you approach understanding this temporal sequence? What information would you extract from each frame and how would you connect them?"
            }]
        },
        
        "technical_understanding": {
            "messages": [{
                "role": "user",
                "content": "What are the key differences between 2D and 3D convolutions in video processing? How do they handle temporal information differently?"
            }]
        },
        
        "practical_application": {
            "messages": [{
                "role": "user",
                "content": "If you were building a video understanding system that needs to track objects across multiple frames, what would be your approach? Describe the architecture and key components."
            }]
        }
    }
    
    # Test both models
    all_results = {}
    
    for model_name, base_url in models.items():
        print(f"\n🔍 Testing {model_name} at {base_url}")
        
        # Check if model is available
        try:
            health_response = requests.get(f"{base_url}/health", timeout=10)
            if health_response.status_code != 200:
                print(f"⚠️  {model_name} not available at {base_url}")
                continue
        except:
            print(f"⚠️  {model_name} not available at {base_url}")
            continue
        
        results = test_model_capabilities(model_name, base_url, test_cases)
        all_results[model_name] = results
    
    # Generate comparison report
    print("\n" + "=" * 60)
    print("📊 COMPARISON REPORT")
    print("=" * 60)
    
    for test_name in test_cases.keys():
        print(f"\n🧪 Test: {test_name}")
        print("-" * 40)
        
        for model_name, results in all_results.items():
            if test_name in results:
                result = results[test_name]
                if result["status"] == "success":
                    print(f"✅ {model_name}: {result['response_time']:.2f}s, {result['tokens']} tokens")
                    print(f"   Response: {result['response'][:100]}...")
                else:
                    print(f"❌ {model_name}: {result['error']}")
            else:
                print(f"⚠️  {model_name}: Not tested")
    
    # Save detailed results
    with open('/home/skadam/gpu-setup/test_results_minicpm_comparison.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: test_results_minicpm_comparison.json")

if __name__ == "__main__":
    main()
