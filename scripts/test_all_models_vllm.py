#!/usr/bin/env python3
"""
Comprehensive Model Testing Script for vLLM
===========================================

This script tests all downloaded models with vLLM to ensure they can:
1. Load successfully
2. Perform inference
3. Unload cleanly

Tests are organized by use case categories.
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

class ModelTester:
    """Tests all downloaded models with vLLM"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.models_dir = Path("/opt/ai-models/models")
        self.test_results = {}
        
        # Define test models by category
        self.test_models = {
            "AGENTS": [
                "phi-2",
                "bert-base-uncased", 
                "video-chatgpt"
            ],
            "MULTIMODAL": [
                "llava-1.5-13b",
                "instructblip-7b"
            ],
            "STT": [
                "whisper-large-v3",
                "whisperlive",
                "m2m100"
            ],
            "TTS": [
                "bark",
                "coqui-tts"
            ],
            "AVATARS": [
                "sadtalker",
                "animatediff"
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
    
    def test_model_loading(self, model_path: str) -> Dict:
        """Test if a model can be loaded in vLLM"""
        logger.info(f"Testing model loading: {model_path}")
        
        # Check if model directory exists and has required files
        model_dir = self.models_dir / model_path
        if not model_dir.exists():
            return {"status": "error", "message": f"Model directory not found: {model_dir}"}
        
        # Check for model files
        model_files = list(model_dir.glob("*.safetensors")) + list(model_dir.glob("*.bin")) + list(model_dir.glob("*.pt"))
        if not model_files:
            return {"status": "error", "message": f"No model files found in {model_dir}"}
        
        # Try to start vLLM with this model
        try:
            # Stop current vLLM service
            subprocess.run(["docker-compose", "stop", "vllm-inference-server"], check=True)
            
            # Start vLLM with new model
            cmd = [
                "docker", "run", "--rm", "-d",
                "--name", "vllm-test",
                "--gpus", "all",
                "-p", "8000:8000",
                "-v", f"{model_dir}:/app/models:ro",
                "vllm/vllm-openai:latest",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--model", f"/app/models"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return {"status": "error", "message": f"Failed to start vLLM: {result.stderr}"}
            
            # Wait for service to start
            time.sleep(30)
            
            # Test if service is responding
            try:
                response = requests.get(f"{self.base_url}/v1/models", timeout=10)
                if response.status_code == 200:
                    return {"status": "success", "message": f"Model loaded successfully"}
                else:
                    return {"status": "error", "message": f"Service not responding: {response.status_code}"}
            except Exception as e:
                return {"status": "error", "message": f"Service test failed: {e}"}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Model loading timeout"}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}
        finally:
            # Clean up test container
            subprocess.run(["docker", "stop", "vllm-test"], capture_output=True)
            subprocess.run(["docker", "rm", "vllm-test"], capture_output=True)
    
    def test_model_inference(self, model_path: str) -> Dict:
        """Test model inference capabilities"""
        logger.info(f"Testing model inference: {model_path}")
        
        try:
            # Test text completion
            payload = {
                "model": f"/app/models",
                "prompt": "Hello, how are you?",
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return {
                        "status": "success", 
                        "message": "Inference successful",
                        "response": result["choices"][0]["text"][:100] + "..."
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
            load_result = self.test_model_loading(model)
            category_results[f"{model}_loading"] = load_result
            
            if load_result["status"] == "success":
                # Test inference
                inference_result = self.test_model_inference(model)
                category_results[f"{model}_inference"] = inference_result
            else:
                category_results[f"{model}_inference"] = {"status": "skipped", "message": "Loading failed"}
        
        return category_results
    
    def run_all_tests(self) -> Dict:
        """Run tests for all use case categories"""
        logger.info("Starting comprehensive model testing")
        
        # Check vLLM service status
        if not self.check_vllm_status():
            logger.error("vLLM service is not running. Please start it first.")
            return {"status": "error", "message": "vLLM service not available"}
        
        all_results = {}
        
        for category, models in self.test_models.items():
            logger.info(f"Testing {category} category with {len(models)} models")
            category_results = self.test_use_case_models(category, models)
            all_results[category] = category_results
            
            # Brief pause between categories
            time.sleep(5)
        
        return all_results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("vLLM MODEL TESTING REPORT")
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
    tester = ModelTester()
    
    logger.info("Starting comprehensive model testing with vLLM")
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Generate and save report
    report = tester.generate_report(results)
    
    # Save report to file
    report_file = Path("model_test_report.txt")
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
