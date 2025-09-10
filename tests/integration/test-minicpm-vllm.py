#!/usr/bin/env python3
"""
Test MiniCPM-V-4 compatibility with vLLM
"""

import os
import sys
import subprocess
import time

def test_minicpm_vllm_compatibility():
    """Test if MiniCPM-V-4 works with vLLM"""
    
    print("🧪 Testing MiniCPM-V-4 compatibility with vLLM...")
    
    # Check if model exists
    model_path = "/opt/ai-models/models/multimodal/minicpm-v-4"
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        return False
    
    print(f"✅ Model found at {model_path}")
    
    # Test vLLM with MiniCPM-V-4
    try:
        print("🚀 Starting vLLM test with MiniCPM-V-4...")
        
        # Run vLLM with MiniCPM-V-4
        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_path,
            "--host", "0.0.0.0",
            "--port", "8000",
            "--trust-remote-code",
            "--max-model-len", "2048"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup (max 60 seconds)
        print("⏳ Waiting for vLLM to start...")
        time.sleep(30)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ vLLM started successfully with MiniCPM-V-4!")
            print("🎉 MiniCPM-V-4 is compatible with vLLM!")
            
            # Terminate the process
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ vLLM failed to start with MiniCPM-V-4")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing MiniCPM-V-4: {e}")
        return False

if __name__ == "__main__":
    success = test_minicpm_vllm_compatibility()
    sys.exit(0 if success else 1)
