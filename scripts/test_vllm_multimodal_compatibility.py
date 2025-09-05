#!/usr/bin/env python3
"""
Test vLLM Compatibility for Multimodal Models

This script tests specific multimodal models to verify they actually work with vLLM
before we download them for the Avatar, Multimodal, and Video use cases.
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Models to test for vLLM compatibility
MULTIMODAL_MODELS_TO_TEST = [
    {
        "name": "LLaVA-1.5-7B",
        "repo_id": "llava-hf/llava-1.5-7b-hf",
        "use_cases": ["avatar", "multimodal", "video"],
        "size_gb": 7,
        "architecture": "LlavaLlamaForCausalLM"
    },
    {
        "name": "LLaVA-v1.6-Mistral-7B", 
        "repo_id": "llava-hf/llava-v1.6-mistral-7b-hf",
        "use_cases": ["avatar", "multimodal", "video"],
        "size_gb": 7,
        "architecture": "LlavaNextForCausalLM"
    },
    {
        "name": "LLaVA-OneVision-Qwen2-0.5B",
        "repo_id": "llava-hf/llava-onevision-qwen2-0.5b-ov-hf",
        "use_cases": ["avatar", "multimodal", "video"],
        "size_gb": 0.5,
        "architecture": "LlavaOneVisionForCausalLM"
    }
]

def test_model_with_vllm(model_info):
    """Test a model with vLLM to verify compatibility."""
    name = model_info["name"]
    repo_id = model_info["repo_id"]
    use_cases = model_info["use_cases"]
    size_gb = model_info["size_gb"]
    architecture = model_info["architecture"]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {name} for vLLM compatibility")
    logger.info(f"{'='*60}")
    logger.info(f"Repository: {repo_id}")
    logger.info(f"Use cases: {', '.join(use_cases)}")
    logger.info(f"Size: {size_gb} GB")
    logger.info(f"Architecture: {architecture}")
    
    # Create a temporary test script
    test_script = f"""
import sys
import os
sys.path.append('/usr/local/lib/python3.12/dist-packages')

try:
    from vllm import LLM
    print("✅ vLLM import successful")
    
    # Try to initialize the model
    print(f"🔄 Testing {repo_id} with vLLM...")
    llm = LLM(model="{repo_id}", task="generate", max_model_len=2048)
    print("✅ Model initialization successful")
    
    # Try a simple text generation
    print("🔄 Testing text generation...")
    outputs = llm.generate("Hello, how are you?")
    print("✅ Text generation successful")
    print(f"Output: {outputs[0].outputs[0].text}")
    
    print("🎉 {name} is vLLM compatible!")
    
except Exception as e:
    print(f"❌ {name} failed vLLM compatibility test: {{str(e)}}")
    sys.exit(1)
"""
    
    # Write test script to temporary file
    test_file = f"/tmp/test_{name.replace('-', '_').replace('.', '_').lower()}.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    try:
        # Run the test
        logger.info(f"🔄 Running vLLM compatibility test...")
        result = subprocess.run([
            "python3", test_file
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            logger.info(f"✅ {name} is vLLM compatible!")
            logger.info("Test output:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
            return True, "vLLM compatible"
        else:
            logger.error(f"❌ {name} failed vLLM compatibility test")
            logger.error("Error output:")
            for line in result.stderr.strip().split('\n'):
                logger.error(f"  {line}")
            return False, f"vLLM test failed: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {name} test timed out (5 minutes)")
        return False, "Test timed out"
    except Exception as e:
        logger.error(f"❌ {name} test failed with exception: {str(e)}")
        return False, f"Exception: {str(e)}"
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """Main testing function."""
    logger.info("🧪 Testing vLLM compatibility for multimodal models...")
    logger.info("This will help us find working models for Avatar, Multimodal, and Video use cases")
    
    compatible_models = []
    incompatible_models = []
    
    for model_info in MULTIMODAL_MODELS_TO_TEST:
        is_compatible, reason = test_model_with_vllm(model_info)
        
        if is_compatible:
            compatible_models.append((model_info, reason))
        else:
            incompatible_models.append((model_info, reason))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"VLLM MULTIMODAL COMPATIBILITY RESULTS")
    logger.info(f"{'='*60}")
    
    logger.info(f"✅ Compatible Models ({len(compatible_models)}):")
    for model_info, reason in compatible_models:
        logger.info(f"  - {model_info['name']}: {reason}")
        logger.info(f"    Use cases: {', '.join(model_info['use_cases'])}")
        logger.info(f"    Size: {model_info['size_gb']} GB")
    
    logger.info(f"\n❌ Incompatible Models ({len(incompatible_models)}):")
    for model_info, reason in incompatible_models:
        logger.info(f"  - {model_info['name']}: {reason}")
    
    # Use case coverage
    logger.info(f"\n📋 USE CASE COVERAGE:")
    working_use_cases = set()
    for model_info, _ in compatible_models:
        working_use_cases.update(model_info['use_cases'])
    
    use_cases = ["avatar", "multimodal", "video"]
    for use_case in use_cases:
        if use_case in working_use_cases:
            logger.info(f"✅ {use_case.title()}: Working models available")
        else:
            logger.info(f"❌ {use_case.title()}: No working models found")
    
    if len(compatible_models) == 0:
        logger.error("❌ NO MULTIMODAL MODELS ARE vLLM COMPATIBLE!")
        logger.error("We need to find alternative approaches for Avatar, Multimodal, and Video use cases")
        return 1
    else:
        logger.info(f"🎉 Found {len(compatible_models)} vLLM-compatible multimodal models!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
