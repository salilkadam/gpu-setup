#!/usr/bin/env python3
"""
Test MiniCPM-V-4 Video Processing Capabilities
Downloads a sample video and tests the model's video understanding capabilities.
"""

import requests
import json
import base64
import os
import tempfile
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoProcessorTester:
    def __init__(self, base_url: str = "http://192.168.0.20:8000"):
        self.base_url = base_url
        
    def download_sample_video(self) -> str:
        """Download a sample video for testing"""
        logger.info("📥 Downloading sample video...")
        
        # Use a small, free sample video
        video_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
        
        try:
            response = requests.get(video_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_file.write(response.content)
            temp_file.close()
            
            logger.info(f"✅ Video downloaded: {temp_file.name} ({len(response.content)} bytes)")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"❌ Failed to download video: {e}")
            # Create a simple test video using ffmpeg if available
            return self.create_test_video()
    
    def create_test_video(self) -> str:
        """Create a simple test video using ffmpeg"""
        logger.info("🎬 Creating test video...")
        
        try:
            import subprocess
            
            # Create a simple 5-second test video with text
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_file.close()
            
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=5:size=320x240:rate=1',
                '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=5',
                '-c:v', 'libx264', '-c:a', 'aac', '-shortest',
                '-y', temp_file.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Test video created: {temp_file.name}")
                return temp_file.name
            else:
                logger.error(f"❌ Failed to create test video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating test video: {e}")
            return None
    
    def encode_video_to_base64(self, video_path: str) -> str:
        """Encode video file to base64"""
        try:
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()
                base64_data = base64.b64encode(video_data).decode('utf-8')
                logger.info(f"✅ Video encoded to base64: {len(base64_data)} characters")
                return base64_data
        except Exception as e:
            logger.error(f"❌ Failed to encode video: {e}")
            return None
    
    def test_video_captioning(self, video_base64: str) -> dict:
        """Test video captioning with MiniCPM-V-4"""
        logger.info("🎬 Testing video captioning...")
        
        # Test different prompt formats for video processing
        test_prompts = [
            {
                "name": "simple_caption",
                "prompt": "Please describe what you see in this video. Provide a detailed caption."
            },
            {
                "name": "scene_analysis", 
                "prompt": "Analyze this video and describe the scenes, objects, and activities you observe."
            },
            {
                "name": "temporal_understanding",
                "prompt": "Describe the sequence of events in this video from start to finish."
            }
        ]
        
        results = {}
        
        for test in test_prompts:
            try:
                logger.info(f"  Testing: {test['name']}")
                
                # Try different API formats
                payloads = [
                    # Format 1: Standard chat with video data
                    {
                        "model": "/app/models/multimodal/minicpm-v-4",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": test["prompt"]},
                                    {"type": "video", "video": {"data": video_base64}}
                                ]
                            }
                        ],
                        "max_tokens": 300,
                        "temperature": 0.7
                    },
                    # Format 2: Alternative format
                    {
                        "model": "/app/models/multimodal/minicpm-v-4",
                        "messages": [
                            {
                                "role": "user", 
                                "content": f"{test['prompt']}\n\nVideo data: {video_base64[:100]}..."
                            }
                        ],
                        "max_tokens": 300,
                        "temperature": 0.7
                    },
                    # Format 3: Simple text prompt (fallback)
                    {
                        "model": "/app/models/multimodal/minicpm-v-4",
                        "messages": [
                            {
                                "role": "user",
                                "content": test["prompt"]
                            }
                        ],
                        "max_tokens": 300,
                        "temperature": 0.7
                    }
                ]
                
                for i, payload in enumerate(payloads):
                    try:
                        response = requests.post(
                            f"{self.base_url}:8000/v1/chat/completions",
                            headers={"Content-Type": "application/json"},
                            json=payload,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            content = data["choices"][0]["message"]["content"]
                            
                            results[f"{test['name']}_format_{i+1}"] = {
                                "status": "success",
                                "response": content,
                                "response_length": len(content),
                                "format": f"format_{i+1}"
                            }
                            
                            logger.info(f"    ✅ Format {i+1}: {len(content)} characters")
                            break  # Stop on first successful format
                        else:
                            logger.warning(f"    ⚠️ Format {i+1}: HTTP {response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"    ⚠️ Format {i+1}: {e}")
                
                if not any(f"{test['name']}_format_" in results for f in [1, 2, 3]):
                    results[f"{test['name']}_all_formats"] = {
                        "status": "error",
                        "error": "All formats failed"
                    }
                    
            except Exception as e:
                results[test["name"]] = {
                    "status": "error", 
                    "error": str(e)
                }
                logger.error(f"    ❌ {test['name']}: {e}")
        
        return results
    
    def test_model_capabilities(self) -> dict:
        """Test what the model actually reports about its capabilities"""
        logger.info("🔍 Testing model capability reporting...")
        
        capability_tests = [
            "What are your capabilities? Can you process images and videos?",
            "Are you a multimodal model? What types of input can you handle?",
            "Can you analyze video content and generate captions?",
            "What is your architecture? Are you MiniCPM-V-4?"
        ]
        
        results = {}
        
        for i, prompt in enumerate(capability_tests):
            try:
                response = requests.post(
                    f"{self.base_url}:8000/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "/app/models/multimodal/minicpm-v-4",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                        "temperature": 0.7
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    results[f"capability_test_{i+1}"] = {
                        "status": "success",
                        "prompt": prompt,
                        "response": content
                    }
                    
                    logger.info(f"  ✅ Capability test {i+1}: {len(content)} characters")
                else:
                    results[f"capability_test_{i+1}"] = {
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }
                    
            except Exception as e:
                results[f"capability_test_{i+1}"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def run_comprehensive_test(self) -> dict:
        """Run comprehensive video processing test"""
        logger.info("🚀 Starting Comprehensive Video Processing Test...")
        logger.info("=" * 60)
        
        results = {
            "test_timestamp": __import__('time').time(),
            "base_url": self.base_url
        }
        
        # Test 1: Model capability reporting
        logger.info("\n🔍 Phase 1: Testing Model Capabilities")
        results["model_capabilities"] = self.test_model_capabilities()
        
        # Test 2: Download/create test video
        logger.info("\n📥 Phase 2: Preparing Test Video")
        video_path = self.download_sample_video()
        
        if video_path and os.path.exists(video_path):
            # Test 3: Encode video
            logger.info("\n🔄 Phase 3: Encoding Video")
            video_base64 = self.encode_video_to_base64(video_path)
            
            if video_base64:
                # Test 4: Video processing
                logger.info("\n🎬 Phase 4: Testing Video Processing")
                results["video_processing"] = self.test_video_captioning(video_base64)
            
            # Cleanup
            try:
                os.unlink(video_path)
                logger.info("🧹 Cleaned up temporary video file")
            except:
                pass
        else:
            results["video_processing"] = {"error": "Could not create test video"}
        
        # Generate summary
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results: dict):
        """Generate summary report"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 VIDEO PROCESSING TEST SUMMARY")
        logger.info("=" * 60)
        
        # Model capabilities
        capabilities = results.get("model_capabilities", {})
        logger.info("\n🔍 Model Capability Reports:")
        for test_name, result in capabilities.items():
            if result.get("status") == "success":
                response = result.get("response", "")[:100]
                logger.info(f"  ✅ {test_name}: {response}...")
            else:
                logger.info(f"  ❌ {test_name}: {result.get('error', 'Unknown error')}")
        
        # Video processing results
        video_results = results.get("video_processing", {})
        if video_results:
            logger.info("\n🎬 Video Processing Results:")
            successful_tests = sum(1 for r in video_results.values() if r.get("status") == "success")
            total_tests = len(video_results)
            logger.info(f"  Success Rate: {successful_tests}/{total_tests}")
            
            for test_name, result in video_results.items():
                if result.get("status") == "success":
                    response = result.get("response", "")[:100]
                    logger.info(f"  ✅ {test_name}: {response}...")
                else:
                    logger.info(f"  ❌ {test_name}: {result.get('error', 'Unknown error')}")
        
        # Final assessment
        logger.info("\n🎯 FINAL ASSESSMENT:")
        if any(r.get("status") == "success" for r in video_results.values()):
            logger.info("✅ Video processing capabilities detected")
        else:
            logger.info("❌ No video processing capabilities detected")
            logger.info("   The model may be running in text-only mode")

def main():
    """Main function"""
    tester = VideoProcessorTester()
    results = tester.run_comprehensive_test()
    
    # Save results
    timestamp = int(__import__('time').time())
    filename = f"video_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Test results saved to: {filename}")

if __name__ == "__main__":
    main()
