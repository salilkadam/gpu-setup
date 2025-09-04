#!/usr/bin/env python3
"""
vLLM Model Download Script for Blackwell GPUs
Downloads and prepares models for vLLM inference
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Add the parent directory to the path to import vllm
sys.path.append(str(Path(__file__).parent.parent))

def download_model(model_name, model_path):
    """Download a model using vLLM's model downloader"""
    try:
        print(f"📥 Downloading {model_name} to {model_path}...")
        
        # Use vLLM's built-in model downloader
        cmd = [
            "python3", "-m", "vllm.model_executor.models.llama.convert_hf_checkpoint",
            "--model-name", model_name,
            "--output-dir", model_path,
            "--num-shards", "1"  # Single shard for testing
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully downloaded {model_name}")
            return True
        else:
            print(f"❌ Failed to download {model_name}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        return False

def download_huggingface_model(model_name, model_path):
    """Download a model directly from Hugging Face using Python API"""
    try:
        print(f"📥 Downloading {model_name} from Hugging Face to {model_path}...")
        
        # Import huggingface_hub
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            print("❌ huggingface_hub not available. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "huggingface_hub"], check=True)
            from huggingface_hub import snapshot_download
        
        # Download the model
        snapshot_download(
            repo_id=model_name,
            local_dir=model_path,
            local_dir_use_symlinks=False
        )
        
        print(f"✅ Successfully downloaded {model_name}")
        return True
            
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        return False

def setup_model_directory():
    """Setup the model directory structure"""
    models_dir = Path("/opt/ai-models/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for different model types
    (models_dir / "phi-2").mkdir(exist_ok=True)
    (models_dir / "llama-2-7b").mkdir(exist_ok=True)
    (models_dir / "mistral-7b").mkdir(exist_ok=True)
    
    return models_dir

def main():
    """Main function to download models"""
    print("🚀 Starting vLLM Model Download for Blackwell GPUs")
    print("=" * 60)
    
    # Setup model directory
    models_dir = setup_model_directory()
    print(f"📁 Model directory: {models_dir}")
    
    # Define models to download
    models = [
        {
            "name": "microsoft/phi-2",
            "path": models_dir / "phi-2",
            "type": "huggingface"
        },
        {
            "name": "meta-llama/Llama-2-7b-hf",
            "path": models_dir / "llama-2-7b",
            "type": "huggingface"
        },
        {
            "name": "mistralai/Mistral-7B-v0.1",
            "path": models_dir / "mistral-7b",
            "type": "huggingface"
        }
    ]
    
    successful_downloads = 0
    total_models = len(models)
    
    for model in models:
        print(f"\n🔍 Processing {model['name']}...")
        
        if model['type'] == 'huggingface':
            if download_huggingface_model(model['name'], str(model['path'])):
                successful_downloads += 1
        else:
            if download_model(model['name'], str(model['path'])):
                successful_downloads += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Download Results: {successful_downloads}/{total_models} models downloaded successfully")
    
    if successful_downloads == total_models:
        print("🎉 All models downloaded successfully!")
        print("\n🚀 Next steps:")
        print("1. Build vLLM Docker image: ./scripts/build-vllm.sh")
        print("2. Start services: docker-compose up -d")
        print("3. Test inference: python3 test_vllm_inference.py")
    else:
        print("❌ Some models failed to download. Please check the errors above.")
    
    return 0 if successful_downloads == total_models else 1

if __name__ == "__main__":
    sys.exit(main())
