#!/usr/bin/env python3
"""
Download Missing Models for All 6 Use Cases

This script downloads the required models to support all 6 use cases:
1. Agent - Qwen2.5-7B-Instruct (already have)
2. Avatar - Qwen2.5-VL-7B-Instruct (missing)
3. STT - Qwen2-Audio-7B (missing) 
4. TTS - Qwen2-Audio-7B (missing)
5. Multimodal - Qwen2.5-VL-7B-Instruct (missing)
6. Video - Qwen2.5-VL-7B-Instruct (missing)

Plus investigate MiniCPM-V-4_5 as alternative multimodal model.
"""

import os
import sys
import time
from pathlib import Path
from huggingface_hub import snapshot_download
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configurations
MODELS_TO_DOWNLOAD = {
    "qwen2.5-vl-7b-instruct": {
        "repo_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "use_cases": ["avatar", "multimodal", "video"],
        "size_gb": 7,
        "description": "Multimodal vision-language model for avatar, multimodal RAG, and video understanding"
    },
    "qwen2-audio-7b": {
        "repo_id": "Qwen/Qwen2-Audio-7B", 
        "use_cases": ["stt", "tts"],
        "size_gb": 7,
        "description": "Audio processing model for speech-to-text and text-to-speech"
    },
    "minicpm-v-4_5": {
        "repo_id": "openbmb/MiniCPM-V-4_5",
        "use_cases": ["multimodal", "video", "avatar"],
        "size_gb": 8.7,
        "description": "Alternative multimodal model with vision, OCR, document parsing, and video capabilities"
    }
}

def check_disk_space():
    """Check available disk space."""
    import shutil
    total, used, free = shutil.disk_usage("/opt/ai-models")
    free_gb = free // (1024**3)
    logger.info(f"Available disk space: {free_gb} GB")
    return free_gb

def download_model(model_name, config):
    """Download a single model."""
    repo_id = config["repo_id"]
    use_cases = config["use_cases"]
    size_gb = config["size_gb"]
    description = config["description"]
    
    logger.info(f"Downloading {model_name}...")
    logger.info(f"Repository: {repo_id}")
    logger.info(f"Use cases: {', '.join(use_cases)}")
    logger.info(f"Size: {size_gb} GB")
    logger.info(f"Description: {description}")
    
    # Check if model already exists
    model_path = Path(f"/opt/ai-models/models/{model_name}")
    if model_path.exists():
        logger.info(f"Model {model_name} already exists at {model_path}")
        return True
    
    try:
        # Download model
        start_time = time.time()
        snapshot_download(
            repo_id=repo_id,
            local_dir=model_path,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        download_time = time.time() - start_time
        logger.info(f"✅ Successfully downloaded {model_name} in {download_time:.1f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {model_name}: {str(e)}")
        return False

def main():
    """Main download function."""
    logger.info("🚀 Starting download of missing models for all 6 use cases...")
    
    # Check disk space
    free_space = check_disk_space()
    total_required = sum(config["size_gb"] for config in MODELS_TO_DOWNLOAD.values())
    
    if free_space < total_required:
        logger.warning(f"⚠️  Warning: Only {free_space} GB free, but {total_required} GB required")
        logger.warning("Consider freeing up space or downloading models individually")
    
    # Create models directory
    os.makedirs("/opt/ai-models/models", exist_ok=True)
    
    # Download each model
    success_count = 0
    total_count = len(MODELS_TO_DOWNLOAD)
    
    for model_name, config in MODELS_TO_DOWNLOAD.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading {model_name} ({success_count + 1}/{total_count})")
        logger.info(f"{'='*60}")
        
        if download_model(model_name, config):
            success_count += 1
        else:
            logger.error(f"Failed to download {model_name}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"DOWNLOAD SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Successfully downloaded: {success_count}/{total_count} models")
    
    if success_count == total_count:
        logger.info("🎉 All models downloaded successfully!")
        logger.info("\n📋 Use Case Coverage:")
        logger.info("✅ Agent: qwen2.5-7b-instruct (already had)")
        logger.info("✅ Avatar: qwen2.5-vl-7b-instruct + minicpm-v-4_5")
        logger.info("✅ STT: qwen2-audio-7b")
        logger.info("✅ TTS: qwen2-audio-7b") 
        logger.info("✅ Multimodal: qwen2.5-vl-7b-instruct + minicpm-v-4_5")
        logger.info("✅ Video: qwen2.5-vl-7b-instruct + minicpm-v-4_5")
    else:
        logger.error(f"❌ Only {success_count}/{total_count} models downloaded successfully")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
