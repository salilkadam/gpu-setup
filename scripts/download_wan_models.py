#!/usr/bin/env python3
"""
Download Wan Video Generation Models
Downloads and organizes Wan models for video generation tasks
"""

import os
import sys
import argparse
import logging
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configurations
WAN_MODELS = {
    "t2v-A14B": {
        "name": "Wan Text-to-Video 14B",
        "description": "Text-to-video generation model",
        "size": "~28GB",
        "url": "https://huggingface.co/Wan-Video/Wan2.2/resolve/main/checkpoints/t2v-A14B.tar.gz",
        "filename": "t2v-A14B.tar.gz",
        "extract_to": "t2v-A14B"
    },
    "i2v-A14B": {
        "name": "Wan Image-to-Video 14B", 
        "description": "Image-to-video generation model",
        "size": "~28GB",
        "url": "https://huggingface.co/Wan-Video/Wan2.2/resolve/main/checkpoints/i2v-A14B.tar.gz",
        "filename": "i2v-A14B.tar.gz",
        "extract_to": "i2v-A14B"
    },
    "ti2v-5B": {
        "name": "Wan Text-Image-to-Video 5B",
        "description": "Text and image to video generation model", 
        "size": "~10GB",
        "url": "https://huggingface.co/Wan-Video/Wan2.2/resolve/main/checkpoints/ti2v-5B.tar.gz",
        "filename": "ti2v-5B.tar.gz",
        "extract_to": "ti2v-5B"
    },
    "animate-14B": {
        "name": "Wan Animation 14B",
        "description": "Animation generation model",
        "size": "~28GB", 
        "url": "https://huggingface.co/Wan-Video/Wan2.2/resolve/main/checkpoints/animate-14B.tar.gz",
        "filename": "animate-14B.tar.gz",
        "extract_to": "animate-14B"
    },
    "s2v-14B": {
        "name": "Wan Speech-to-Video 14B",
        "description": "Speech-to-video generation model",
        "size": "~28GB",
        "url": "https://huggingface.co/Wan-Video/Wan2.2/resolve/main/checkpoints/s2v-14B.tar.gz", 
        "filename": "s2v-14B.tar.gz",
        "extract_to": "s2v-14B"
    }
}

def get_models_dir() -> Path:
    """Get the models directory path"""
    models_dir = os.getenv("MODELS_DIR", "/opt/ai-models")
    wan_dir = Path(models_dir) / "wan"
    wan_dir.mkdir(parents=True, exist_ok=True)
    return wan_dir

def download_file(url: str, filepath: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress tracking"""
    try:
        logger.info(f"Downloading {url} to {filepath}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print()  # New line after progress
        logger.info(f"Downloaded {filepath.name} successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download {url}: {str(e)}")
        return False

def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """Extract archive file"""
    try:
        logger.info(f"Extracting {archive_path} to {extract_to}")
        
        if archive_path.suffix == '.tar.gz' or archive_path.suffix == '.tgz':
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_to.parent)
        elif archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to.parent)
        else:
            logger.error(f"Unsupported archive format: {archive_path.suffix}")
            return False
        
        logger.info(f"Extracted {archive_path.name} successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract {archive_path}: {str(e)}")
        return False

def verify_model(model_key: str, model_path: Path) -> bool:
    """Verify that the model is properly extracted"""
    try:
        # Check if the model directory exists and has content
        if not model_path.exists():
            return False
        
        # Look for common model files
        model_files = list(model_path.glob("*.bin")) + list(model_path.glob("*.safetensors")) + list(model_path.glob("*.pt"))
        config_files = list(model_path.glob("*.json")) + list(model_path.glob("config.yaml"))
        
        if len(model_files) > 0 and len(config_files) > 0:
            logger.info(f"Model {model_key} verified successfully")
            return True
        else:
            logger.warning(f"Model {model_key} may be incomplete - found {len(model_files)} model files and {len(config_files)} config files")
            return False
            
    except Exception as e:
        logger.error(f"Failed to verify model {model_key}: {str(e)}")
        return False

def download_model(model_key: str, models_dir: Path, force: bool = False) -> bool:
    """Download and extract a specific model"""
    if model_key not in WAN_MODELS:
        logger.error(f"Unknown model: {model_key}")
        return False
    
    model_info = WAN_MODELS[model_key]
    model_path = models_dir / model_info["extract_to"]
    
    # Check if model already exists
    if model_path.exists() and not force:
        logger.info(f"Model {model_key} already exists at {model_path}")
        if verify_model(model_key, model_path):
            return True
        else:
            logger.warning(f"Model {model_key} exists but appears incomplete, re-downloading...")
    
    # Download the model
    archive_path = models_dir / model_info["filename"]
    
    # Remove existing files if force download
    if force:
        if model_path.exists():
            shutil.rmtree(model_path)
        if archive_path.exists():
            archive_path.unlink()
    
    # Download archive
    if not download_file(model_info["url"], archive_path):
        return False
    
    # Extract archive
    if not extract_archive(archive_path, model_path):
        return False
    
    # Verify extraction
    if not verify_model(model_key, model_path):
        return False
    
    # Clean up archive file
    try:
        archive_path.unlink()
        logger.info(f"Cleaned up archive file: {archive_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up archive file {archive_path}: {str(e)}")
    
    return True

def list_available_models():
    """List all available Wan models"""
    print("\nAvailable Wan Models:")
    print("=" * 80)
    
    for key, info in WAN_MODELS.items():
        print(f"Model: {key}")
        print(f"  Name: {info['name']}")
        print(f"  Description: {info['description']}")
        print(f"  Size: {info['size']}")
        print(f"  URL: {info['url']}")
        print()

def list_installed_models():
    """List installed Wan models"""
    models_dir = get_models_dir()
    
    print("\nInstalled Wan Models:")
    print("=" * 50)
    
    installed_count = 0
    for key, info in WAN_MODELS.items():
        model_path = models_dir / info["extract_to"]
        if model_path.exists():
            if verify_model(key, model_path):
                print(f"✓ {key} - {info['name']}")
                installed_count += 1
            else:
                print(f"⚠ {key} - {info['name']} (incomplete)")
        else:
            print(f"✗ {key} - {info['name']} (not installed)")
    
    print(f"\nTotal installed: {installed_count}/{len(WAN_MODELS)}")
    print(f"Models directory: {models_dir}")

def main():
    parser = argparse.ArgumentParser(description="Download Wan video generation models")
    parser.add_argument("--model", "-m", type=str, help="Specific model to download")
    parser.add_argument("--all", "-a", action="store_true", help="Download all models")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    parser.add_argument("--installed", "-i", action="store_true", help="List installed models")
    parser.add_argument("--force", "-f", action="store_true", help="Force re-download even if model exists")
    parser.add_argument("--models-dir", type=str, help="Override models directory")
    
    args = parser.parse_args()
    
    # Override models directory if specified
    if args.models_dir:
        os.environ["MODELS_DIR"] = args.models_dir
    
    models_dir = get_models_dir()
    logger.info(f"Using models directory: {models_dir}")
    
    if args.list:
        list_available_models()
        return
    
    if args.installed:
        list_installed_models()
        return
    
    if args.all:
        logger.info("Downloading all Wan models...")
        success_count = 0
        for model_key in WAN_MODELS.keys():
            if download_model(model_key, models_dir, args.force):
                success_count += 1
            else:
                logger.error(f"Failed to download {model_key}")
        
        logger.info(f"Successfully downloaded {success_count}/{len(WAN_MODELS)} models")
        
    elif args.model:
        if args.model not in WAN_MODELS:
            logger.error(f"Unknown model: {args.model}")
            logger.info("Available models:")
            for key in WAN_MODELS.keys():
                logger.info(f"  - {key}")
            return
        
        if download_model(args.model, models_dir, args.force):
            logger.info(f"Successfully downloaded {args.model}")
        else:
            logger.error(f"Failed to download {args.model}")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
