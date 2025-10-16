#!/usr/bin/env python3
"""
Test Wan Video Generation Service
Tests the Wan video generation API endpoints and functionality
"""

import os
import sys
import time
import json
import requests
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import base64
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WanServiceTester:
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minutes timeout for video generation
        
    def health_check(self) -> bool:
        """Check if the Wan service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            logger.info(f"Health check passed: {data}")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            models = response.json()
            logger.info(f"Available models: {list(models.keys())}")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return {}
    
    def list_videos(self) -> Dict[str, Any]:
        """List generated videos"""
        try:
            response = self.session.get(f"{self.base_url}/videos")
            response.raise_for_status()
            videos = response.json()
            logger.info(f"Found {len(videos.get('videos', []))} generated videos")
            return videos
        except Exception as e:
            logger.error(f"Failed to list videos: {str(e)}")
            return {}
    
    def create_test_image(self, filename: str = "test_image.jpg") -> str:
        """Create a test image for i2v and s2v tests"""
        try:
            # Create a simple test image
            img = Image.new('RGB', (512, 512), color='lightblue')
            
            # Add some simple content
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            draw.text((50, 200), "Test Image", fill='darkblue', font=font)
            draw.rectangle([100, 100, 400, 400], outline='red', width=5)
            
            # Save the image
            test_dir = Path("/tmp/wan_test")
            test_dir.mkdir(exist_ok=True)
            image_path = test_dir / filename
            img.save(image_path)
            
            logger.info(f"Created test image: {image_path}")
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Failed to create test image: {str(e)}")
            return ""
    
    def test_text_to_video(self, model: str = "t2v-A14B") -> bool:
        """Test text-to-video generation"""
        try:
            logger.info(f"Testing text-to-video generation with model: {model}")
            
            payload = {
                "task": model,
                "prompt": "A beautiful sunset over a calm ocean with gentle waves",
                "size": "1280*720",
                "frame_num": 17,  # 4n+1 format
                "sample_steps": 20,
                "sample_guide_scale": 7.5,
                "base_seed": 42
            }
            
            response = self.session.post(f"{self.base_url}/generate/text-to-video", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Text-to-video generation result: {result}")
            
            if result.get("success"):
                logger.info(f"✓ Text-to-video test passed. Video saved to: {result.get('video_path')}")
                return True
            else:
                logger.error(f"✗ Text-to-video test failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Text-to-video test failed with exception: {str(e)}")
            return False
    
    def test_image_to_video(self, model: str = "i2v-A14B") -> bool:
        """Test image-to-video generation"""
        try:
            logger.info(f"Testing image-to-video generation with model: {model}")
            
            # Create test image
            image_path = self.create_test_image("i2v_test.jpg")
            if not image_path:
                logger.error("Failed to create test image")
                return False
            
            payload = {
                "task": model,
                "prompt": "The image comes to life with gentle movement and animation",
                "image_path": image_path,
                "size": "1280*720",
                "frame_num": 17,
                "sample_steps": 20,
                "sample_guide_scale": 7.5,
                "base_seed": 42
            }
            
            response = self.session.post(f"{self.base_url}/generate/image-to-video", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Image-to-video generation result: {result}")
            
            if result.get("success"):
                logger.info(f"✓ Image-to-video test passed. Video saved to: {result.get('video_path')}")
                return True
            else:
                logger.error(f"✗ Image-to-video test failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Image-to-video test failed with exception: {str(e)}")
            return False
    
    def test_speech_to_video(self, model: str = "s2v-14B") -> bool:
        """Test speech-to-video generation"""
        try:
            logger.info(f"Testing speech-to-video generation with model: {model}")
            
            # Create test image
            image_path = self.create_test_image("s2v_test.jpg")
            if not image_path:
                logger.error("Failed to create test image")
                return False
            
            payload = {
                "task": model,
                "prompt": "A person speaking naturally with facial expressions",
                "image_path": image_path,
                "enable_tts": True,
                "tts_prompt_text": "Hello, this is a test of the TTS system.",
                "tts_text": "This is a test of the speech-to-video generation system.",
                "size": "1280*720",
                "frame_num": 17,
                "sample_steps": 20,
                "sample_guide_scale": 7.5,
                "base_seed": 42
            }
            
            response = self.session.post(f"{self.base_url}/generate/speech-to-video", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Speech-to-video generation result: {result}")
            
            if result.get("success"):
                logger.info(f"✓ Speech-to-video test passed. Video saved to: {result.get('video_path')}")
                return True
            else:
                logger.error(f"✗ Speech-to-video test failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Speech-to-video test failed with exception: {str(e)}")
            return False
    
    def test_animation(self, model: str = "animate-14B") -> bool:
        """Test animation generation"""
        try:
            logger.info(f"Testing animation generation with model: {model}")
            
            # For animation, we need a source path with processed data
            # This is a simplified test - in practice, you'd need proper animation data
            test_dir = Path("/tmp/wan_test/animation")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a dummy source structure (this would normally contain processed animation data)
            (test_dir / "processed").mkdir(exist_ok=True)
            (test_dir / "processed" / "dummy.txt").write_text("dummy animation data")
            
            payload = {
                "task": model,
                "prompt": "A character performing a simple animation",
                "src_root_path": str(test_dir),
                "replace_flag": False,
                "refert_num": 77,
                "frame_num": 17,
                "sample_steps": 20,
                "sample_guide_scale": 7.5,
                "base_seed": 42
            }
            
            response = self.session.post(f"{self.base_url}/generate/animation", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Animation generation result: {result}")
            
            if result.get("success"):
                logger.info(f"✓ Animation test passed. Video saved to: {result.get('video_path')}")
                return True
            else:
                logger.error(f"✗ Animation test failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Animation test failed with exception: {str(e)}")
            return False
    
    def test_video_download(self) -> bool:
        """Test video download functionality"""
        try:
            logger.info("Testing video download functionality")
            
            # First, list videos to get a filename
            videos = self.list_videos()
            video_list = videos.get("videos", [])
            
            if not video_list:
                logger.warning("No videos available for download test")
                return True  # Not a failure, just no videos to test
            
            # Test downloading the first video
            video_filename = video_list[0]["filename"]
            response = self.session.get(f"{self.base_url}/videos/{video_filename}")
            response.raise_for_status()
            
            # Check if we got video content
            content_type = response.headers.get('content-type', '')
            if 'video' in content_type:
                logger.info(f"✓ Video download test passed for {video_filename}")
                return True
            else:
                logger.error(f"✗ Video download test failed - unexpected content type: {content_type}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Video download test failed with exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run comprehensive tests on all available models"""
        results = {}
        
        logger.info("Starting comprehensive Wan service tests...")
        
        # Health check
        results["health_check"] = self.health_check()
        if not results["health_check"]:
            logger.error("Service is not healthy, skipping other tests")
            return results
        
        # List models
        models = self.list_models()
        available_models = {k: v for k, v in models.items() if v.get("available", False)}
        
        if not available_models:
            logger.warning("No models are available for testing")
            return results
        
        logger.info(f"Testing with available models: {list(available_models.keys())}")
        
        # Test each available model type
        for model_key, model_info in available_models.items():
            logger.info(f"Testing model: {model_key}")
            
            if "t2v" in model_key:
                results[f"t2v_{model_key}"] = self.test_text_to_video(model_key)
            elif "i2v" in model_key:
                results[f"i2v_{model_key}"] = self.test_image_to_video(model_key)
            elif "s2v" in model_key:
                results[f"s2v_{model_key}"] = self.test_speech_to_video(model_key)
            elif "animate" in model_key:
                results[f"animate_{model_key}"] = self.test_animation(model_key)
            elif "ti2v" in model_key:
                results[f"ti2v_{model_key}"] = self.test_image_to_video(model_key)
        
        # Test video download
        results["video_download"] = self.test_video_download()
        
        # List final videos
        self.list_videos()
        
        return results

def main():
    parser = argparse.ArgumentParser(description="Test Wan video generation service")
    parser.add_argument("--url", "-u", default="http://localhost:8004", help="Wan service URL")
    parser.add_argument("--test", "-t", choices=["health", "models", "t2v", "i2v", "s2v", "animate", "download", "all"], 
                       default="all", help="Specific test to run")
    parser.add_argument("--model", "-m", help="Specific model to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = WanServiceTester(args.url)
    
    if args.test == "health":
        success = tester.health_check()
        sys.exit(0 if success else 1)
    
    elif args.test == "models":
        models = tester.list_models()
        print(json.dumps(models, indent=2))
        sys.exit(0)
    
    elif args.test == "t2v":
        model = args.model or "t2v-A14B"
        success = tester.test_text_to_video(model)
        sys.exit(0 if success else 1)
    
    elif args.test == "i2v":
        model = args.model or "i2v-A14B"
        success = tester.test_image_to_video(model)
        sys.exit(0 if success else 1)
    
    elif args.test == "s2v":
        model = args.model or "s2v-14B"
        success = tester.test_speech_to_video(model)
        sys.exit(0 if success else 1)
    
    elif args.test == "animate":
        model = args.model or "animate-14B"
        success = tester.test_animation(model)
        sys.exit(0 if success else 1)
    
    elif args.test == "download":
        success = tester.test_video_download()
        sys.exit(0 if success else 1)
    
    elif args.test == "all":
        results = tester.run_comprehensive_test()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results.items():
            status = "PASS" if success else "FAIL"
            print(f"{test_name:30} {status}")
            if success:
                passed += 1
        
        print(f"\nPassed: {passed}/{total}")
        
        if passed == total:
            print("✓ All tests passed!")
            sys.exit(0)
        else:
            print("✗ Some tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()
