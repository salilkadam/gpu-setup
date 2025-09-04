#!/usr/bin/env python3
"""
vLLM Compatible Models Test Script
=================================

This script tests models that are actually compatible with vLLM.
Based on testing, multimodal models like LLaVA are not supported.
Focus on text-only models that work with vLLM.
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VLLMCompatibleTester:
    """Tests vLLM compatible models"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.models_dir = Path("/opt/ai-models/models")
        self.test_results = {}
        
        # Define vLLM compatible models (text-only)
        self.compatible_models = {
            "AGENTS": [
                "phi-2",           # ✅ Tested and working
                "bert-base-uncased", # Text classification
                "video-chatgpt"    # Text generation
            ],
            "STT": [
                "whisper-large-v3", # Speech-to-text (may need special handling)
                "whisperlive"      # Real-time STT
            ],
            "TTS": [
                "bark",            # Text-to-speech (may need special handling)
                "coqui-tts"        # TTS
            ]
        }
        
        # Models that are NOT compatible with vLLM
        self.incompatible_models = {
            "MULTIMODAL": [
                "llava-1.5-13b",   # ❌ LlavaLlamaForCausalLM not supported
                "instructblip-7b"  # ❌ Likely not supported
            ],
            "AVATARS": [
                "sadtalker",       # ❌ Not a language model
                "animatediff"      # ❌ Not a language model
            ],
            "VIDEO": [
                "video-chatgpt"    # ❌ May not be compatible
            ]
        }
    
    def check_vllm_status(self) -> bool:
        """Check if vLLM service is running"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"vLLM service not available: {e}")
            return False
    
    def test_model_switch(self, model_path: str) -> Dict:
        """Test switching to a different model"""
        logger.info(f"Testing model switch to: {model_path}")
        
        # Check if model directory exists
        model_dir = self.models_dir / model_path
        if not model_dir.exists():
            return {"status": "error", "message": f"Model directory not found: {model_dir}"}
        
        # Check for model files
        model_files = list(model_dir.glob("*.safetensors")) + list(model_dir.glob("*.bin")) + list(model_dir.glob("*.pt"))
        if not model_files:
            return {"status": "error", "message": f"No model files found in {model_dir}"}
        
        try:
            # Stop current vLLM service
            logger.info("Stopping current vLLM service...")
            subprocess.run(["docker-compose", "stop", "vllm-inference-server"], check=True)
            
            # Update docker-compose to use new model
            docker_compose_file = Path("docker-compose.yml")
            content = docker_compose_file.read_text()
            content = content.replace(
                '--model", "/app/models/phi-2"',
                f'--model", "/app/models/{model_path}"'
            )
            docker_compose_file.write_text(content)
            
            # Start vLLM with new model
            logger.info(f"Starting vLLM with model: {model_path}")
            subprocess.run(["docker-compose", "up", "-d", "vllm-inference-server"], check=True)
            
            # Wait for service to start
            logger.info("Waiting for model to load...")
            time.sleep(60)  # Give more time for model loading
            
            # Test if service is responding
            try:
                response = requests.get(f"{self.base_url}/v1/models", timeout=30)
                if response.status_code == 200:
                    models = response.json()
                    if models.get("data") and len(models["data"]) > 0:
                        model_id = models["data"][0]["id"]
                        return {
                            "status": "success", 
                            "message": f"Model loaded successfully: {model_id}",
                            "model_id": model_id
                        }
                    else:
                        return {"status": "error", "message": "No models found in response"}
                else:
                    return {"status": "error", "message": f"Service not responding: {response.status_code}"}
            except Exception as e:
                return {"status": "error", "message": f"Service test failed: {e}"}
                
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Command failed: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}
    
    def test_model_inference(self, model_path: str) -> Dict:
        """Test model inference capabilities"""
        logger.info(f"Testing model inference: {model_path}")
        
        try:
            # Test text completion
            payload = {
                "model": f"/app/models/{model_path}",
                "prompt": "What is machine learning?",
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return {
                        "status": "success", 
                        "message": "Inference successful",
                        "response": result["choices"][0]["text"][:200] + "...",
                        "usage": result.get("usage", {})
                    }
                else:
                    return {"status": "error", "message": "No response generated"}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Inference test failed: {e}"}
    
    def test_use_case_models(self, category: str, models: List[str]) -> Dict:
        """Test all models in a use case category"""
        logger.info(f"Testing {category} models: {models}")
        
        category_results = {}
        
        for model in models:
            logger.info(f"Testing {category}/{model}")
            
            # Test model loading
            load_result = self.test_model_switch(model)
            category_results[f"{model}_loading"] = load_result
            
            if load_result["status"] == "success":
                # Test inference
                inference_result = self.test_model_inference(model)
                category_results[f"{model}_inference"] = inference_result
            else:
                category_results[f"{model}_inference"] = {"status": "skipped", "message": "Loading failed"}
        
        return category_results
    
    def run_compatible_tests(self) -> Dict:
        """Run tests for vLLM compatible models only"""
        logger.info("Starting vLLM compatible model testing")
        
        # Check vLLM service status
        if not self.check_vllm_status():
            logger.error("vLLM service is not running. Please start it first.")
            return {"status": "error", "message": "vLLM service not available"}
        
        all_results = {}
        
        for category, models in self.compatible_models.items():
            logger.info(f"Testing {category} category with {len(models)} models")
            category_results = self.test_use_case_models(category, models)
            all_results[category] = category_results
            
            # Brief pause between categories
            time.sleep(10)
        
        return all_results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("vLLM COMPATIBLE MODEL TESTING REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category, category_results in results.items():
            report.append(f"📁 {category} CATEGORY")
            report.append("-" * 40)
            
            for test_name, test_result in category_results.items():
                total_tests += 1
                status = test_result["status"]
                message = test_result["message"]
                
                if status == "success":
                    passed_tests += 1
                    report.append(f"✅ {test_name}: {message}")
                elif status == "error":
                    failed_tests += 1
                    report.append(f"❌ {test_name}: {message}")
                else:
                    report.append(f"⏭️  {test_name}: {message}")
            
            report.append("")
        
        # Add incompatible models section
        report.append("=" * 80)
        report.append("INCOMPATIBLE MODELS (Not tested with vLLM)")
        report.append("=" * 80)
        
        for category, models in self.incompatible_models.items():
            report.append(f"📁 {category} CATEGORY")
            report.append("-" * 40)
            for model in models:
                report.append(f"❌ {model}: Not compatible with vLLM")
            report.append("")
        
        # Summary
        report.append("=" * 80)
        report.append("SUMMARY")
        report.append("=" * 80)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        return "\n".join(report)

def main():
    """Main function"""
    tester = VLLMCompatibleTester()
    
    logger.info("Starting vLLM compatible model testing")
    
    # Run compatible tests
    results = tester.run_compatible_tests()
    
    # Generate and save report
    report = tester.generate_report(results)
    
    # Save report to file
    report_file = Path("vllm_compatible_test_report.txt")
    with open(report_file, "w") as f:
        f.write(report)
    
    # Print report
    print(report)
    
    logger.info(f"Test report saved to: {report_file}")
    
    # Return appropriate exit code
    if any("error" in str(results).lower() for results in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
