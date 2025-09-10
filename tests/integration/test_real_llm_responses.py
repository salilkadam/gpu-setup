#!/usr/bin/env python3
"""
Comprehensive Test Script for Real LLM Responses
Tests all AI services to ensure we're getting actual model outputs, not mock responses.
"""

import requests
import json
import time
import base64
import io
import wave
import numpy as np
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealLLMTester:
    def __init__(self, base_url: str = "http://192.168.0.20"):
        self.base_url = base_url
        self.results = {}
        
    def test_vllm_text_generation(self) -> Dict[str, Any]:
        """Test vLLM text generation with specific prompts to verify real responses"""
        logger.info("🧠 Testing vLLM Text Generation...")
        
        test_cases = [
            {
                "name": "mathematical_reasoning",
                "prompt": "What is 15 * 23 + 47? Show your work step by step.",
                "expected_keywords": ["345", "392", "15", "23", "47"]
            },
            {
                "name": "current_events_awareness",
                "prompt": "What is the current year and what major events happened in 2024?",
                "expected_keywords": ["2024", "2025"]
            },
            {
                "name": "code_generation",
                "prompt": "Write a Python function to calculate fibonacci numbers recursively.",
                "expected_keywords": ["def", "fibonacci", "return", "if", "else"]
            },
            {
                "name": "creative_writing",
                "prompt": "Write a short story about a robot learning to paint. Include specific details about colors and techniques.",
                "expected_keywords": ["robot", "paint", "color", "brush", "canvas"]
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                logger.info(f"  Testing: {test_case['name']}")
                
                response = requests.post(
                    f"{self.base_url}:8000/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "/app/models/text_generation/qwen2.5-7b-instruct",
                        "messages": [
                            {"role": "user", "content": test_case["prompt"]}
                        ],
                        "max_tokens": 200,
                        "temperature": 0.7
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Check for expected keywords
                    found_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() in content.lower()]
                    
                    results[test_case["name"]] = {
                        "status": "success",
                        "response_length": len(content),
                        "found_keywords": found_keywords,
                        "keyword_match_rate": len(found_keywords) / len(test_case["expected_keywords"]),
                        "response_preview": content[:200] + "..." if len(content) > 200 else content,
                        "full_response": content
                    }
                    
                    logger.info(f"    ✅ {test_case['name']}: {len(found_keywords)}/{len(test_case['expected_keywords'])} keywords found")
                else:
                    results[test_case["name"]] = {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    logger.error(f"    ❌ {test_case['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                results[test_case["name"]] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"    ❌ {test_case['name']}: {e}")
                
            time.sleep(1)  # Rate limiting
            
        return results
    
    def test_model_consistency(self) -> Dict[str, Any]:
        """Test that the same prompt gives different responses (proving it's not cached/mocked)"""
        logger.info("🔄 Testing Model Consistency (Same prompt, different responses)...")
        
        prompt = "Generate a random 5-digit number and explain why you chose it."
        responses = []
        
        for i in range(3):
            try:
                response = requests.post(
                    f"{self.base_url}:8000/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "/app/models/text_generation/qwen2.5-7b-instruct",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 100,
                        "temperature": 0.8  # Higher temperature for more variation
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    responses.append(content)
                    logger.info(f"  Response {i+1}: {content[:50]}...")
                else:
                    logger.error(f"  Response {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"  Response {i+1}: {e}")
                
            time.sleep(2)
            
        # Check if responses are different
        unique_responses = len(set(responses))
        is_consistent = unique_responses == 1
        is_varied = unique_responses > 1
        
        return {
            "total_responses": len(responses),
            "unique_responses": unique_responses,
            "is_consistent": is_consistent,
            "is_varied": is_varied,
            "responses": responses,
            "conclusion": "REAL MODEL" if is_varied else "POSSIBLY MOCKED/CACHED"
        }
    
    def test_stt_service(self) -> Dict[str, Any]:
        """Test STT service with generated audio"""
        logger.info("🎤 Testing STT Service...")
        
        # Generate a simple test audio file (sine wave)
        sample_rate = 16000
        duration = 2  # seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_buffer.seek(0)
        
        try:
            # Test STT with the generated audio
            files = {'file': ('test_audio.wav', wav_buffer, 'audio/wav')}
            response = requests.post(
                f"{self.base_url}:8002/transcribe",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "transcription": data.get("transcription", ""),
                    "language": data.get("language", ""),
                    "model": data.get("model", ""),
                    "confidence": data.get("confidence", 0),
                    "note": "Generated sine wave audio - should produce minimal transcription"
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def test_tts_service(self) -> Dict[str, Any]:
        """Test TTS service"""
        logger.info("🔊 Testing TTS Service...")
        
        test_text = "Hello, this is a test of the text to speech service. The current time is approximately " + str(int(time.time()))
        
        try:
            response = requests.post(
                f"{self.base_url}:8003/synthesize",
                headers={"Content-Type": "application/json"},
                json={
                    "text": test_text,
                    "language": "en",
                    "voice": "female"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                # Check if we got audio data back
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                return {
                    "status": "success",
                    "content_type": content_type,
                    "content_length": content_length,
                    "has_audio_data": content_length > 1000,  # Expecting substantial audio data
                    "response_preview": response.content[:100] if content_length > 0 else "No content"
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def test_model_metadata(self) -> Dict[str, Any]:
        """Test model metadata to verify real model information"""
        logger.info("📊 Testing Model Metadata...")
        
        try:
            response = requests.get(f"{self.base_url}:8000/v1/models", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                
                if models:
                    model = models[0]
                    return {
                        "status": "success",
                        "model_id": model.get("id", ""),
                        "max_model_len": model.get("max_model_len", 0),
                        "created": model.get("created", 0),
                        "owned_by": model.get("owned_by", ""),
                        "permissions": len(model.get("permission", [])),
                        "is_real_model": model.get("max_model_len", 0) > 1000  # Real models have large context
                    }
                else:
                    return {
                        "status": "error",
                        "error": "No models found in response"
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def test_routing_api(self) -> Dict[str, Any]:
        """Test routing API health and endpoint status"""
        logger.info("🛣️ Testing Routing API...")
        
        try:
            response = requests.get(f"{self.base_url}:8001/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get("model_endpoints", {})
                
                healthy_endpoints = sum(1 for ep in endpoints.values() if ep.get("status") == "healthy")
                total_endpoints = len(endpoints)
                
                return {
                    "status": "success",
                    "total_endpoints": total_endpoints,
                    "healthy_endpoints": healthy_endpoints,
                    "health_rate": healthy_endpoints / total_endpoints if total_endpoints > 0 else 0,
                    "endpoints": endpoints
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("🚀 Starting Comprehensive LLM Response Testing...")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        self.results = {
            "test_timestamp": time.time(),
            "base_url": self.base_url,
            "vllm_text_generation": self.test_vllm_text_generation(),
            "model_consistency": self.test_model_consistency(),
            "model_metadata": self.test_model_metadata(),
            "stt_service": self.test_stt_service(),
            "tts_service": self.test_tts_service(),
            "routing_api": self.test_routing_api()
        }
        
        end_time = time.time()
        self.results["total_test_time"] = end_time - start_time
        
        # Generate summary
        self.generate_summary_report()
        
        return self.results
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 COMPREHENSIVE TEST SUMMARY REPORT")
        logger.info("=" * 60)
        
        # Overall assessment
        total_tests = 0
        successful_tests = 0
        
        for test_name, test_result in self.results.items():
            if test_name in ["test_timestamp", "base_url", "total_test_time"]:
                continue
                
            total_tests += 1
            if isinstance(test_result, dict) and test_result.get("status") == "success":
                successful_tests += 1
        
        logger.info(f"📊 Overall Test Results: {successful_tests}/{total_tests} tests passed")
        logger.info(f"⏱️ Total Test Time: {self.results['total_test_time']:.2f} seconds")
        
        # Detailed results
        logger.info("\n🔍 DETAILED TEST RESULTS:")
        logger.info("-" * 40)
        
        # vLLM Text Generation
        vllm_results = self.results.get("vllm_text_generation", {})
        if vllm_results:
            logger.info("\n🧠 vLLM Text Generation Tests:")
            for test_name, result in vllm_results.items():
                if result.get("status") == "success":
                    keyword_rate = result.get("keyword_match_rate", 0)
                    logger.info(f"  ✅ {test_name}: {keyword_rate:.1%} keyword match rate")
                else:
                    logger.info(f"  ❌ {test_name}: {result.get('error', 'Unknown error')}")
        
        # Model Consistency
        consistency = self.results.get("model_consistency", {})
        if consistency:
            logger.info(f"\n🔄 Model Consistency: {consistency.get('conclusion', 'Unknown')}")
            logger.info(f"  Unique responses: {consistency.get('unique_responses', 0)}/{consistency.get('total_responses', 0)}")
        
        # Model Metadata
        metadata = self.results.get("model_metadata", {})
        if metadata.get("status") == "success":
            logger.info(f"\n📊 Model Metadata:")
            logger.info(f"  Model ID: {metadata.get('model_id', 'Unknown')}")
            logger.info(f"  Max Context: {metadata.get('max_model_len', 0):,} tokens")
            logger.info(f"  Real Model: {'✅ Yes' if metadata.get('is_real_model') else '❌ No'}")
        
        # Service Tests
        services = ["stt_service", "tts_service", "routing_api"]
        for service in services:
            result = self.results.get(service, {})
            if result.get("status") == "success":
                logger.info(f"\n✅ {service.replace('_', ' ').title()}: Working")
            else:
                logger.info(f"\n❌ {service.replace('_', ' ').title()}: {result.get('error', 'Unknown error')}")
        
        # Final Assessment
        logger.info("\n" + "=" * 60)
        logger.info("🎯 FINAL ASSESSMENT")
        logger.info("=" * 60)
        
        if successful_tests >= total_tests * 0.8:  # 80% success rate
            logger.info("✅ CONCLUSION: REAL LLM RESPONSES DETECTED")
            logger.info("   The services are providing genuine AI model outputs.")
        else:
            logger.info("❌ CONCLUSION: POSSIBLE MOCK/CACHED RESPONSES")
            logger.info("   Some services may not be working correctly.")
        
        logger.info(f"\n📄 Full test results saved to: test_results_{int(time.time())}.json")

def main():
    """Main function to run the tests"""
    tester = RealLLMTester()
    results = tester.run_all_tests()
    
    # Save results to file
    timestamp = int(time.time())
    filename = f"test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Test results saved to: {filename}")
    
    return results

if __name__ == "__main__":
    main()
