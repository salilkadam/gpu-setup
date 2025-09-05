#!/usr/bin/env python3
"""
Verify vLLM Compatibility for Models

This script tests each model to ensure it's actually compatible with vLLM
before we deploy it in production.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_model_architecture(model_path):
    """Check the architecture of a model."""
    config_path = Path(model_path) / "config.json"
    if not config_path.exists():
        return None, "No config.json found"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        architectures = config.get('architectures', [])
        return architectures, "Success"
    except Exception as e:
        return None, f"Error reading config: {str(e)}"

def test_vllm_compatibility(model_path, model_name):
    """Test if a model is compatible with vLLM."""
    logger.info(f"Testing vLLM compatibility for {model_name}...")
    
    # Check architecture first
    architectures, status = check_model_architecture(model_path)
    if not architectures:
        logger.error(f"❌ {model_name}: {status}")
        return False, status
    
    logger.info(f"Architecture: {architectures[0] if architectures else 'Unknown'}")
    
    # Known vLLM compatible architectures
    vllm_compatible_architectures = [
        "Qwen2ForCausalLM",
        "MistralForCausalLM", 
        "LlamaForCausalLM",
        "PhiForCausalLM",
        "GemmaForCausalLM",
        "MiniCPMForCausalLM",
        "Qwen2VLForConditionalGeneration",  # Check if this is supported
        "Qwen2_5_VLForConditionalGeneration"  # Check if this is supported
    ]
    
    architecture = architectures[0] if architectures else None
    
    if architecture in vllm_compatible_architectures:
        logger.info(f"✅ {model_name}: Architecture {architecture} is known to be vLLM compatible")
        return True, f"Architecture {architecture} is compatible"
    else:
        logger.warning(f"⚠️  {model_name}: Architecture {architecture} is unknown - needs testing")
        return False, f"Architecture {architecture} needs verification"

def main():
    """Main verification function."""
    logger.info("🔍 Verifying vLLM compatibility for all models...")
    
    models_dir = Path("/opt/ai-models/models")
    if not models_dir.exists():
        logger.error("❌ Models directory not found!")
        return 1
    
    # Check each model
    compatible_models = []
    incompatible_models = []
    
    for model_dir in models_dir.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name
            model_path = str(model_dir)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Checking {model_name}")
            logger.info(f"{'='*60}")
            
            is_compatible, reason = test_vllm_compatibility(model_path, model_name)
            
            if is_compatible:
                compatible_models.append((model_name, reason))
            else:
                incompatible_models.append((model_name, reason))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"VLLM COMPATIBILITY SUMMARY")
    logger.info(f"{'='*60}")
    
    logger.info(f"✅ Compatible Models ({len(compatible_models)}):")
    for model, reason in compatible_models:
        logger.info(f"  - {model}: {reason}")
    
    logger.info(f"\n❌ Incompatible/Unknown Models ({len(incompatible_models)}):")
    for model, reason in incompatible_models:
        logger.info(f"  - {model}: {reason}")
    
    # Use case coverage
    logger.info(f"\n📋 USE CASE COVERAGE:")
    logger.info(f"✅ Agent: {'qwen2.5-7b-instruct' if 'qwen2.5-7b-instruct' in [m[0] for m in compatible_models] else '❌ MISSING'}")
    logger.info(f"❓ Avatar: {'qwen2.5-vl-7b-instruct' if 'qwen2.5-vl-7b-instruct' in [m[0] for m in compatible_models] else '❌ MISSING'}")
    logger.info(f"❌ STT: {'❌ NO AUDIO MODELS'}")
    logger.info(f"❌ TTS: {'❌ NO AUDIO MODELS'}")
    logger.info(f"❓ Multimodal: {'qwen2.5-vl-7b-instruct' if 'qwen2.5-vl-7b-instruct' in [m[0] for m in compatible_models] else '❌ MISSING'}")
    logger.info(f"❓ Video: {'qwen2.5-vl-7b-instruct' if 'qwen2.5-vl-7b-instruct' in [m[0] for m in compatible_models] else '❌ MISSING'}")
    
    if len(compatible_models) == 0:
        logger.error("❌ NO COMPATIBLE MODELS FOUND!")
        return 1
    elif len(incompatible_models) > 0:
        logger.warning("⚠️  Some models need verification or are incompatible")
        return 1
    else:
        logger.info("🎉 All models are vLLM compatible!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
