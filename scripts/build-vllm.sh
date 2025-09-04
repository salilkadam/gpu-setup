#!/bin/bash

# vLLM Build Script for Blackwell GPUs
# This script builds vLLM from source using Docker

set -e

echo "🚀 Starting vLLM build for Blackwell GPUs..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if NVIDIA Docker runtime is available
echo "🔍 Checking NVIDIA Docker runtime..."
if ! docker run --rm --gpus all nvidia/cuda:12.9.0-cudnn-runtime-ubuntu24.04 nvidia-smi > /dev/null 2>&1; then
    echo "❌ NVIDIA Docker runtime is not available. Please check your Docker GPU setup."
    exit 1
fi

echo "✅ NVIDIA Docker runtime is available"

# Build the vLLM image
echo "🔨 Building vLLM Docker image..."
echo "📦 Using CUDA 12.9 with cuDNN for Blackwell GPU compatibility"
docker build -f Dockerfile.vllm -t vllm-blackwell:latest .

if [ $? -eq 0 ]; then
    echo "✅ vLLM build completed successfully!"
    echo "📦 Image tagged as: vllm-blackwell:latest"
    
    # Test the build
    echo "🧪 Testing vLLM installation..."
    docker run --rm --gpus all vllm-blackwell:latest python -c "
import vllm
print('✅ vLLM imported successfully')
print(f'vLLM version: {vllm.__version__}')
print('🎉 Build verification complete!')
"
    
    if [ $? -eq 0 ]; then
        echo "✅ vLLM verification successful!"
        echo ""
        echo "🚀 Next steps:"
        echo "1. Download models: python3 scripts/download_vllm_models.py"
        echo "2. Start services: docker-compose up -d"
        echo "3. Test inference: python3 test_vllm_inference.py"
    else
        echo "❌ vLLM verification failed!"
        exit 1
    fi
else
    echo "❌ vLLM build failed!"
    exit 1
fi
