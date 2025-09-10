#!/usr/bin/env python3
"""
Test MiniCPM-V-4 Image Processing Capabilities
Creates a simple test image and tests the model's image understanding.
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os

def create_test_image():
    """Create a simple test image with text"""
    # Create a simple image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), "TEST IMAGE", fill='black', font=font)
    draw.text((50, 100), "This is a test image", fill='blue', font=font)
    draw.text((50, 150), "for MiniCPM-V-4", fill='red', font=font)
    
    # Add a simple shape
    draw.rectangle([300, 50, 350, 100], outline='green', width=3)
    draw.ellipse([300, 120, 350, 170], outline='purple', width=3)
    
    return img

def image_to_base64(img):
    """Convert PIL image to base64"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def test_image_processing():
    """Test image processing with MiniCPM-V-4"""
    base_url = "http://192.168.0.20:8000"
    
    print("🎨 Creating test image...")
    test_img = create_test_image()
    
    print("🔄 Converting image to base64...")
    img_base64 = image_to_base64(test_img)
    print(f"✅ Image encoded: {len(img_base64)} characters")
    
    # Test different formats for sending images
    test_formats = [
        {
            "name": "OpenAI Vision Format",
            "payload": {
                "model": "/app/models/multimodal/minicpm-v-4",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe what you see in this image."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
        },
        {
            "name": "Alternative Format",
            "payload": {
                "model": "/app/models/multimodal/minicpm-v-4",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Describe what you see in this image: data:image/png;base64,{img_base64}"
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
        },
        {
            "name": "Simple Text Test",
            "payload": {
                "model": "/app/models/multimodal/minicpm-v-4",
                "messages": [
                    {
                        "role": "user",
                        "content": "Can you see any images? Describe what you see."
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
        }
    ]
    
    print("\n🧪 Testing image processing capabilities...")
    
    for i, test in enumerate(test_formats):
        print(f"\n📋 Test {i+1}: {test['name']}")
        try:
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=test["payload"],
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ Success: {len(content)} characters")
                print(f"📝 Response: {content[:200]}...")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"📝 Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    # Save test image for reference
    test_img.save("test_image.png")
    print(f"\n💾 Test image saved as: test_image.png")

if __name__ == "__main__":
    test_image_processing()
