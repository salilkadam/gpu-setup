#!/bin/bash
# FramePack Setup Script
# Installs FramePack and dependencies for video processing

set -e

echo "🚀 Setting up FramePack for video processing..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers diffusers
pip install opencv-python pillow
pip install numpy scipy
pip install fastapi uvicorn

# Try to install FramePack (if available)
echo "🎬 Attempting to install FramePack..."
pip install framepack-ai || echo "⚠️ FramePack package not found, will need manual installation"

# Create FramePack service directory
echo "📁 Creating FramePack service directory..."
mkdir -p /opt/framepack
mkdir -p /opt/framepack/models
mkdir -p /opt/framepack/cache

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R $USER:$USER /opt/framepack

echo "✅ FramePack setup completed!"
echo "📋 Next steps:"
echo "  1. Research FramePack official repositories"
echo "  2. Download FramePack models"
echo "  3. Test basic functionality"
echo "  4. Integrate with MiniCPM-V-4.5"
