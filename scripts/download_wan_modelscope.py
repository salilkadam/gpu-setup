#!/usr/bin/env python3
"""
WAN Model Download Script using ModelScope
Downloads WAN models using ModelScope in a Docker container
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# WAN Models available on ModelScope
WAN_MODELS = {
    "Wan2.2-T2V-A14B": {
        "name": "Wan Text-to-Video 14B",
        "description": "Text-to-video generation model",
        "size": "~28GB",
        "modelscope_id": "Wan-AI/Wan2.2-T2V-A14B",
        "local_dir": "Wan2.2-T2V-A14B"
    },
    "Wan2.2-I2V-A14B": {
        "name": "Wan Image-to-Video 14B", 
        "description": "Image-to-video generation model",
        "size": "~28GB",
        "modelscope_id": "Wan-AI/Wan2.2-I2V-A14B",
        "local_dir": "Wan2.2-I2V-A14B"
    },
    "Wan2.2-TI2V-5B": {
        "name": "Wan Text-Image-to-Video 5B",
        "description": "Text and image to video generation model", 
        "size": "~10GB",
        "modelscope_id": "Wan-AI/Wan2.2-TI2V-5B",
        "local_dir": "Wan2.2-TI2V-5B"
    },
    "Wan2.2-Animate-14B": {
        "name": "Wan Animation 14B",
        "description": "Animation generation model",
        "size": "~28GB", 
        "modelscope_id": "Wan-AI/Wan2.2-Animate-14B",
        "local_dir": "Wan2.2-Animate-14B"
    },
    "Wan2.2-S2V-14B": {
        "name": "Wan Speech-to-Video 14B",
        "description": "Speech-to-video generation model",
        "size": "~28GB",
        "modelscope_id": "Wan-AI/Wan2.2-S2V-14B", 
        "local_dir": "Wan2.2-S2V-14B"
    }
}

def run_docker_download(model_id, local_dir, target_dir="/opt/ai-models-extended/wan"):
    """Run ModelScope download in Docker container"""
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Docker command to download model
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{target_dir}:/workspace",
        "python:3.11-slim",
        "bash", "-c",
        f"""
        pip install modelscope >/dev/null 2>&1 && \
        cd /workspace && \
        echo "Downloading {model_id} to {local_dir}..." && \
        modelscope download {model_id} --local_dir ./{local_dir} && \
        echo "Download completed for {model_id}"
        """
    ]
    
    print(f"Starting download for {model_id}...")
    print(f"Command: {' '.join(docker_cmd)}")
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode == 0:
            print(f"✅ Successfully downloaded {model_id}")
            print(f"Output: {result.stdout}")
            return True
        else:
            print(f"❌ Failed to download {model_id}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Download timeout for {model_id}")
        return False
    except Exception as e:
        print(f"❌ Error downloading {model_id}: {e}")
        return False

def check_model_exists(model_dir, target_dir="/opt/ai-models-extended/wan"):
    """Check if model directory exists and has content"""
    full_path = os.path.join(target_dir, model_dir)
    if os.path.exists(full_path) and os.path.isdir(full_path):
        files = os.listdir(full_path)
        if files:
            return True
    return False

def list_available_models():
    """List all available WAN models"""
    print("Available WAN Models on ModelScope:")
    print("=" * 50)
    for model_id, info in WAN_MODELS.items():
        status = "✅ Installed" if check_model_exists(info["local_dir"]) else "❌ Not installed"
        print(f"{model_id}: {info['name']}")
        print(f"  Description: {info['description']}")
        print(f"  Size: {info['size']}")
        print(f"  ModelScope ID: {info['modelscope_id']}")
        print(f"  Status: {status}")
        print()

def download_model(model_id):
    """Download a specific model"""
    if model_id not in WAN_MODELS:
        print(f"❌ Unknown model: {model_id}")
        print("Available models:", list(WAN_MODELS.keys()))
        return False
    
    model_info = WAN_MODELS[model_id]
    
    # Check if already installed
    if check_model_exists(model_info["local_dir"]):
        print(f"✅ Model {model_id} is already installed")
        return True
    
    return run_docker_download(model_info["modelscope_id"], model_info["local_dir"])

def download_all_models():
    """Download all available models"""
    print("Starting download of all WAN models...")
    print("=" * 50)
    
    results = {}
    for model_id, model_info in WAN_MODELS.items():
        print(f"\n📥 Downloading {model_id}...")
        success = download_model(model_id)
        results[model_id] = success
        
        if success:
            print(f"✅ {model_id} downloaded successfully")
        else:
            print(f"❌ {model_id} download failed")
    
    print("\n" + "=" * 50)
    print("Download Summary:")
    for model_id, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{model_id}: {status}")
    
    return results

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python download_wan_modelscope.py [command]")
        print("Commands:")
        print("  --list          List available models")
        print("  --download <id> Download specific model")
        print("  --all           Download all models")
        print("  --installed     Show installed models")
        return
    
    command = sys.argv[1]
    
    if command == "--list":
        list_available_models()
    elif command == "--download" and len(sys.argv) > 2:
        model_id = sys.argv[2]
        download_model(model_id)
    elif command == "--all":
        download_all_models()
    elif command == "--installed":
        print("Installed WAN Models:")
        print("=" * 30)
        for model_id, info in WAN_MODELS.items():
            if check_model_exists(info["local_dir"]):
                print(f"✅ {model_id}: {info['name']}")
            else:
                print(f"❌ {model_id}: Not installed")
    else:
        print("❌ Invalid command. Use --help for usage information.")

if __name__ == "__main__":
    main()
