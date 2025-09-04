#!/bin/bash

# AI Model Management Script
# Manages models in centralized /opt/ai-models location

set -e

# Configuration
MODELS_DIR="/opt/ai-models"
CACHE_DIR="$MODELS_DIR/cache"
DOWNLOADS_DIR="$MODELS_DIR/downloads"
ACTIVE_DIR="$MODELS_DIR/active"
VERSIONS_DIR="$MODELS_DIR/versions"
MODELS_STORAGE="$MODELS_DIR/models"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root or with sudo"
    exit 1
fi

# Function to create directory structure
create_directory_structure() {
    print_status "Creating centralized model directory structure..."
    
    mkdir -p "$MODELS_DIR"/{cache,downloads,active,versions}
    mkdir -p "$MODELS_STORAGE"/{llama2,mistral,codellama,phi,qwen}
    
    # Set proper permissions
    chmod 755 "$MODELS_DIR"
    chown -R root:root "$MODELS_DIR"
    
    print_success "Directory structure created at $MODELS_DIR"
}

# Function to show current model status
show_model_status() {
    print_status "Current Model Status:"
    echo "=================================="
    
    # Show directory sizes
    echo "Storage Usage:"
    du -sh "$MODELS_DIR"/* 2>/dev/null | while read size path; do
        echo "  $size $path"
    done
    
    echo ""
    echo "Available Models:"
    
    # Check each category
    for category in llama2 mistral codellama phi qwen; do
        category_path="$MODELS_STORAGE/$category"
        if [ -d "$category_path" ]; then
            models=$(find "$category_path" -maxdepth 1 -type d -name "*" | wc -l)
            if [ "$models" -gt 1 ]; then  # -1 because of the category dir itself
                echo "  $category: $((models-1)) models"
                find "$category_path" -maxdepth 1 -type d -name "*" | grep -v "^$category_path$" | while read model; do
                    model_name=$(basename "$model")
                    size=$(du -sh "$model" 2>/dev/null | cut -f1)
                    echo "    - $model_name ($size)"
                done
            else
                echo "  $category: No models"
            fi
        fi
    done
    
    echo ""
    echo "Active Models:"
    if [ -d "$ACTIVE_DIR" ] && [ "$(ls -A "$ACTIVE_DIR" 2>/dev/null)" ]; then
        ls -la "$ACTIVE_DIR"
    else
        echo "  No active models"
    fi
}

# Function to download a specific model
download_model() {
    local model_name="$1"
    
    if [ -z "$model_name" ]; then
        print_error "Please specify a model name"
        echo "Usage: $0 download <model_name>"
        echo "Available models: llama2-7b, llama2-13b, mistral-7b, codellama-13b, phi-2, qwen-7b"
        exit 1
    fi
    
    print_status "Downloading model: $model_name"
    
    # Create download tracking file
    download_file="$DOWNLOADS_DIR/${model_name}.download"
    echo "Download started: $(date)" > "$download_file"
    echo "Model: $model_name" >> "$download_file"
    
    # Determine category and path
    case "$model_name" in
        llama2-*)
            category="llama2"
            ;;
        mistral-*)
            category="mistral"
            ;;
        codellama-*)
            category="codellama"
            ;;
        phi-*)
            category="phi"
            ;;
        qwen-*)
            category="qwen"
            ;;
        *)
            print_error "Unknown model category for $model_name"
            exit 1
            ;;
    esac
    
    target_dir="$MODELS_STORAGE/$category/$model_name"
    
    if [ -d "$target_dir" ]; then
        print_warning "Model $model_name already exists at $target_dir"
        echo "Skipping download..."
        return 0
    fi
    
    # Create category directory
    mkdir -p "$MODELS_STORAGE/$category"
    
    # Download using Python script
    print_status "Starting download to $target_dir..."
    
    # Create a temporary Python script for downloading
    cat > /tmp/download_model.py << 'PYTHON_EOF'
import os
import sys
import time
from huggingface_hub import snapshot_download

def download_model(model_name, target_dir):
    model_mapping = {
        "llama2-7b": "meta-llama/Llama-2-7b-chat-hf",
        "llama2-13b": "meta-llama/Llama-2-13b-chat-hf",
        "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.2",
        "codellama-13b": "codellama/CodeLlama-13b-Instruct-hf",
        "phi-2": "microsoft/phi-2",
        "qwen-7b": "Qwen/Qwen-7B-Chat"
    }
    
    if model_name not in model_mapping:
        print(f"Error: Model {model_name} not supported")
        return False
    
    try:
        print(f"Downloading {model_name} from {model_mapping[model_name]}...")
        snapshot_download(
            repo_id=model_mapping[model_name],
            local_dir=target_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ {model_name} downloaded successfully to {target_dir}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 download_model.py <model_name> <target_dir>")
        sys.exit(1)
    
    model_name = sys.argv[1]
    target_dir = sys.argv[2]
    
    success = download_model(model_name, target_dir)
    sys.exit(0 if success else 1)
PYTHON_EOF
    
    # Install huggingface-hub if not present
    if ! python3 -c "import huggingface_hub" 2>/dev/null; then
        print_status "Installing huggingface-hub..."
        pip3 install huggingface-hub
    fi
    
    # Run download
    if python3 /tmp/download_model.py "$model_name" "$target_dir"; then
        print_success "Model $model_name downloaded successfully!"
        
        # Create version metadata
        version_file="$VERSIONS_DIR/${model_name}.version"
        cat > "$version_file" << EOF
Model: $model_name
Category: $category
Downloaded: $(date)
Location: $target_dir
Size: $(du -sh "$target_dir" | cut -f1)
Status: Ready
EOF
        
        # Update download tracking
        echo "Download completed: $(date)" >> "$download_file"
        echo "Status: Success" >> "$download_file"
        
        # Clean up
        rm -f /tmp/download_model.py
        
        print_success "Model $model_name is ready for use!"
    else
        print_error "Failed to download model $model_name"
        echo "Download failed: $(date)" >> "$download_file"
        echo "Status: Failed" >> "$download_file"
        rm -f /tmp/download_model.py
        exit 1
    fi
}

# Function to list available models
list_models() {
    print_status "Available Models for Download:"
    echo "====================================="
    
    cat << 'EOF'
llama2-7b      - Meta's Llama2 7B Chat model (14GB, GPU 0)
llama2-13b     - Meta's Llama2 13B Chat model (26GB, GPU 1)
mistral-7b     - Mistral AI's 7B Instruct model (14GB, GPU 0)
codellama-13b  - Code generation model (26GB, GPU 1)
phi-2          - Microsoft's Phi-2 model (7GB, GPU 0)
qwen-7b        - Qwen's 7B Chat model (14GB, GPU 0)

Memory estimates are approximate and may vary based on configuration.
GPU recommendations are based on optimal performance.
EOF
}

# Function to clean up old downloads
cleanup_downloads() {
    print_status "Cleaning up download cache..."
    
    if [ -d "$CACHE_DIR" ]; then
        old_files=$(find "$CACHE_DIR" -type f -mtime +7 2>/dev/null | wc -l)
        if [ "$old_files" -gt 0 ]; then
            find "$CACHE_DIR" -type f -mtime +7 -delete 2>/dev/null
            print_success "Cleaned up $old_files old cache files"
        else
            print_status "No old cache files to clean up"
        fi
    fi
    
    if [ -d "$DOWNLOADS_DIR" ]; then
        old_downloads=$(find "$DOWNLOADS_DIR" -name "*.download" -mtime +1 2>/dev/null | wc -l)
        if [ "$old_downloads" -gt 0 ]; then
            find "$DOWNLOADS_DIR" -name "*.download" -mtime +1 -delete 2>/dev/null
            print_success "Cleaned up $old_downloads old download tracking files"
        fi
    fi
}

# Function to show help
show_help() {
    cat << 'EOF'
AI Model Management Script

Usage: $0 <command> [options]

Commands:
  setup              - Create directory structure
  status             - Show current model status
  list               - List available models for download
  download <model>   - Download a specific model
  cleanup            - Clean up old cache and download files
  help               - Show this help message

Examples:
  $0 setup                    # Create directory structure
  $0 status                  # Show current status
  $0 download llama2-7b      # Download Llama2 7B model
  $0 cleanup                 # Clean up old files

Available Models:
  llama2-7b, llama2-13b, mistral-7b, codellama-13b, phi-2, qwen-7b

Note: Models are downloaded to /opt/ai-models/models/ and organized by category.
EOF
}

# Main script logic
case "${1:-help}" in
    setup)
        create_directory_structure
        ;;
    status)
        show_model_status
        ;;
    list)
        list_models
        ;;
    download)
        download_model "$2"
        ;;
    cleanup)
        cleanup_downloads
        ;;
    help|*)
        show_help
        ;;
esac
