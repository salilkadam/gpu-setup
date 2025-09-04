#!/bin/bash

# Extended AI Model Management Script
# Manages models for specialized use cases: Avatars, STT, TTS, Agents, and Multimodal RAG

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
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_category() {
    echo -e "${PURPLE}[CATEGORY]${NC} $1"
}

print_model() {
    echo -e "${CYAN}[MODEL]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root or with sudo"
    exit 1
fi

# Extended model registry with use case categorization
declare -A MODEL_REGISTRY

# 1. TALKING HEAD AVATARS & LIP SYNC
MODEL_REGISTRY["sadtalker"]="CompVis/stable-diffusion-v1-4|avatar|8GB|GPU 0|Real-time talking head generation"
MODEL_REGISTRY["wav2lip"]="Rudrabha/Wav2Lip|avatar|4GB|GPU 0|Lip sync for videos"
MODEL_REGISTRY["facefusion"]="deepinsight/facefusion|avatar|6GB|GPU 0|High-quality face swapping"
MODEL_REGISTRY["animatediff"]="runwayml/stable-diffusion-v1-5|avatar|8GB|GPU 0|Text-to-video animation"

# 2. MULTILINGUAL STT (Indian Languages)
MODEL_REGISTRY["whisper-large-v3"]="openai/whisper-large-v3|stt|10GB|GPU 0|Multilingual STT with Indian language support"
MODEL_REGISTRY["whisperlive"]="guillaumekln/faster-whisper-large-v3|stt|10GB|GPU 0|Real-time streaming Whisper"
MODEL_REGISTRY["m2m100"]="facebook/m2m100_418M|stt|2GB|GPU 0|Facebook's multilingual model"
MODEL_REGISTRY["indicwhisper"]="ai4bharat/indic-whisper|stt|8GB|GPU 0|Specialized for Indian languages"

# 3. MULTILINGUAL TTS (Indian Languages)
MODEL_REGISTRY["coqui-tts"]="microsoft/speecht5_tts|tts|6GB|GPU 0|Excellent Indian language TTS"
MODEL_REGISTRY["bark"]="suno-ai/bark|tts|12GB|GPU 0|High-quality multilingual TTS"
MODEL_REGISTRY["valle-x"]="microsoft/speecht5_tts|tts|8GB|GPU 0|Microsoft's multilingual TTS"
MODEL_REGISTRY["indic-tts"]="ai4bharat/indic-tts|tts|4GB|GPU 0|Specialized for Indian languages"

# 4. CONTENT GENERATION & EXECUTING AGENTS
MODEL_REGISTRY["claude-3.5-sonnet"]="anthropic/claude-3.5-sonnet|agent|40GB|GPU 1|Best reasoning and coding"
MODEL_REGISTRY["gpt-4"]="openai/gpt-4|agent|50GB|GPU 1|Excellent content generation"
MODEL_REGISTRY["codellama-70b"]="codellama/CodeLlama-70b-Instruct-hf|agent|70GB|GPU 1|Best coding capabilities"
MODEL_REGISTRY["llama2-70b"]="meta-llama/Llama-2-70b-chat-hf|agent|70GB|GPU 1|Strong general reasoning"
MODEL_REGISTRY["llama2-13b"]="meta-llama/Llama-2-13b-chat-hf|agent|26GB|GPU 1|Balanced performance"
MODEL_REGISTRY["mistral-7b"]="mistralai/Mistral-7B-Instruct-v0.2|agent|14GB|GPU 0|Fast reasoning"

# 5. MULTI-MODAL TEMPORAL AGENTIC RAG
MODEL_REGISTRY["llava-13b"]="liuhaotian/llava-v1.5-13b|multimodal|26GB|GPU 1|Open-source vision-language"
MODEL_REGISTRY["cogvlm-17b"]="THUDM/cogvlm-chat-hf|multimodal|34GB|GPU 1|Strong visual reasoning"
MODEL_REGISTRY["qwen-vl-7b"]="Qwen/Qwen-VL-7B|multimodal|14GB|GPU 0|Alibaba's vision-language model"
MODEL_REGISTRY["instructblip-7b"]="Salesforce/instructblip-vicuna-7b|multimodal|14GB|GPU 0|Instruction-tuned vision-language"

# 6. VIDEO-TO-TEXT UNDERSTANDING & CONTENT GENERATION
MODEL_REGISTRY["video-llava"]="LanguageBind/Video-LLaVA-7B|video|26GB|GPU 1|Video understanding with language model"
MODEL_REGISTRY["videochat"]="microsoft/DialoGPT-medium|video|14GB|GPU 0|Specialized video conversation"
MODEL_REGISTRY["video-chatgpt"]="microsoft/DialoGPT-large|video|20GB|GPU 1|Video analysis and reasoning"
MODEL_REGISTRY["univl"]="microsoft/univl-base|video|18GB|GPU 0|Unified video-language understanding"

# Function to create extended directory structure
create_extended_directory_structure() {
    print_status "Creating extended model directory structure..."
    
    # Create main directories
    mkdir -p "$MODELS_DIR"/{cache,downloads,active,versions}
    
    # Create use case specific directories
    mkdir -p "$MODELS_STORAGE"/{avatar,stt,tts,agent,multimodal,video}
    
    # Create subdirectories for each category
    mkdir -p "$MODELS_STORAGE"/avatar/{sadtalker,wav2lip,facefusion,animatediff}
    mkdir -p "$MODELS_STORAGE"/stt/{whisper,m2m100,indicwhisper}
    mkdir -p "$MODELS_STORAGE"/tts/{coqui,bark,valle,indic}
    mkdir -p "$MODELS_STORAGE"/agent/{claude,gpt,codellama,llama2,mistral}
    mkdir -p "$MODELS_STORAGE"/multimodal/{llava,cogvlm,qwen,instructblip}
    mkdir -p "$MODELS_STORAGE"/video/{video-llava,videochat,video-chatgpt,univl}
    
    # Set proper permissions
    chmod 755 "$MODELS_DIR"
    chown -R root:root "$MODELS_DIR"
    
    print_success "Extended directory structure created at $MODELS_DIR"
}

# Function to show use case categories
show_use_case_categories() {
    print_status "Available Use Case Categories:"
    echo "====================================="
    
    echo ""
    print_category "1. TALKING HEAD AVATARS & LIP SYNC"
    echo "   Models: sadtalker, wav2lip, facefusion, animatediff"
    echo "   Purpose: Real-time avatar generation and lip synchronization"
    
    echo ""
    print_category "2. MULTILINGUAL STT (Indian Languages)"
    echo "   Models: whisper-large-v3, whisperlive, m2m100, indicwhisper"
    echo "   Purpose: Speech-to-text with Indian language support"
    
    echo ""
    print_category "3. MULTILINGUAL TTS (Indian Languages)"
    echo "   Models: coqui-tts, bark, valle-x, indic-tts"
    echo "   Purpose: Text-to-speech with Indian language support"
    
    echo ""
    print_category "4. CONTENT GENERATION & EXECUTING AGENTS"
    echo "   Models: claude-3.5-sonnet, gpt-4, codellama-70b, llama2-70b"
    echo "   Purpose: Reasoning, coding, and content generation"
    
    echo ""
    print_category "5. MULTI-MODAL TEMPORAL AGENTIC RAG"
    echo "   Models: llava-13b, cogvlm-17b, qwen-vl-7b, instructblip-7b"
    echo "   Purpose: Vision-language understanding and reasoning"
    
    echo ""
    print_category "6. VIDEO-TO-TEXT UNDERSTANDING & CONTENT GENERATION"
    echo "   Models: video-llava, videochat, video-chatgpt, univl"
    echo "   Purpose: Video analysis, understanding, and content generation"
}

# Function to show models by use case
show_models_by_use_case() {
    local use_case="$1"
    
    case "$use_case" in
        avatar)
            print_category "TALKING HEAD AVATARS & LIP SYNC MODELS"
            echo "================================================"
            for model in sadtalker wav2lip facefusion animatediff; do
                if [[ -n "${MODEL_REGISTRY[$model]}" ]]; then
                    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                    print_model "$model"
                    echo "  Repo: $repo_id"
                    echo "  Size: $size"
                    echo "  GPU: $gpu"
                    echo "  Description: $description"
                    echo ""
                fi
            done
            ;;
        stt)
            print_category "MULTILINGUAL STT MODELS (Indian Languages)"
            echo "=================================================="
            for model in whisper-large-v3 whisperlive m2m100 indicwhisper; do
                if [[ -n "${MODEL_REGISTRY[$model]}" ]]; then
                    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                    print_model "$model"
                    echo "  Repo: $repo_id"
                    echo "  Size: $size"
                    echo "  GPU: $gpu"
                    echo "  Description: $description"
                    echo ""
                fi
            done
            ;;
        tts)
            print_category "MULTILINGUAL TTS MODELS (Indian Languages)"
            echo "=================================================="
            for model in coqui-tts bark valle-x indic-tts; do
                if [[ -n "${MODEL_REGISTRY[$model]}" ]]; then
                    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                    print_model "$model"
                    echo "  Repo: $repo_id"
                    echo "  Size: $size"
                    echo "  GPU: $gpu"
                    echo "  Description: $description"
                    echo ""
                fi
            done
            ;;
        agent)
            print_category "CONTENT GENERATION & EXECUTING AGENTS"
            echo "============================================"
            for model in claude-3.5-sonnet gpt-4 codellama-70b llama2-70b llama2-13b mistral-7b; do
                if [[ -n "${MODEL_REGISTRY[$model]}" ]]; then
                    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                    print_model "$model"
                    echo "  Repo: $repo_id"
                    echo "  Size: $size"
                    echo "  GPU: $gpu"
                    echo "  Description: $description"
                    echo ""
                fi
            done
            ;;
        multimodal)
            print_category "MULTI-MODAL TEMPORAL AGENTIC RAG"
            echo "======================================="
            for model in llava-13b cogvlm-17b qwen-vl-7b instructblip-7b; do
                if [[ -n "${MODEL_REGISTRY[$model]}" ]]; then
                    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                    print_model "$model"
                    echo "  Repo: $repo_id"
                    echo "  Size: $size"
                    echo "  GPU: $gpu"
                    echo "  Description: $description"
                    echo ""
                fi
            done
            ;;
        video)
            print_category "VIDEO-TO-TEXT UNDERSTANDING & CONTENT GENERATION"
            echo "========================================================="
            for model in video-llava videochat video-chatgpt univl; do
                if [[ -n "${MODEL_REGISTRY[$model]}" ]]; then
                    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                    print_model "$model"
                    echo "  Repo: $repo_id"
                    echo "  Size: $size"
                    echo "  GPU: $gpu"
                    echo "  Description: $description"
                    echo ""
                fi
            done
            ;;
        *)
            print_error "Unknown use case: $use_case"
            echo "Available use cases: avatar, stt, tts, agent, multimodal"
            ;;
    esac
}

# Function to download model by use case
download_model_by_use_case() {
    local use_case="$1"
    local model_name="$2"
    
    if [ -z "$use_case" ] || [ -z "$model_name" ]; then
        print_error "Please specify both use case and model name"
        echo "Usage: $0 download-use-case <use_case> <model_name>"
        echo "Example: $0 download-use-case avatar sadtalker"
        exit 1
    fi
    
    if [[ -z "${MODEL_REGISTRY[$model_name]}" ]]; then
        print_error "Model $model_name not found in registry"
        exit 1
    fi
    
    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model_name]}"
    
    if [ "$category" != "$use_case" ]; then
        print_error "Model $model_name is not in the $use_case category"
        echo "Model $model_name belongs to category: $category"
        exit 1
    fi
    
    print_status "Downloading $model_name for $use_case use case..."
    print_model "Model: $model_name"
    echo "  Repo: $repo_id"
    echo "  Size: $size"
    echo "  GPU: $gpu"
    echo "  Description: $description"
    
    # Create download tracking file
    download_file="$DOWNLOADS_DIR/${model_name}-${use_case}.download"
    echo "Download started: $(date)" > "$download_file"
    echo "Model: $model_name" >> "$download_file"
    echo "Use Case: $use_case" >> "$download_file"
    echo "Category: $category" >> "$download_file"
    echo "Repo: $repo_id" >> "$download_file"
    
    # Determine target directory
    case "$use_case" in
        avatar)
            target_dir="$MODELS_STORAGE/avatar/$model_name"
            ;;
        stt)
            target_dir="$MODELS_STORAGE/stt/$model_name"
            ;;
        tts)
            target_dir="$MODELS_STORAGE/tts/$model_name"
            ;;
        agent)
            target_dir="$MODELS_STORAGE/agent/$model_name"
            ;;
        multimodal)
            target_dir="$MODELS_STORAGE/multimodal/$model_name"
            ;;
        video)
            target_dir="$MODELS_STORAGE/video/$model_name"
            ;;
    esac
    
    if [ -d "$target_dir" ]; then
        print_warning "Model $model_name already exists at $target_dir"
        echo "Skipping download..."
        return 0
    fi
    
    # Create target directory
    mkdir -p "$target_dir"
    
    # Download using Python script
    print_status "Starting download to $target_dir..."
    
    # Create a temporary Python script for downloading
    cat > /tmp/download_model_extended.py << 'PYTHON_EOF'
import os
import sys
from huggingface_hub import snapshot_download

def download_model(model_name, repo_id, target_dir):
    try:
        print(f"Downloading {model_name} from {repo_id}...")
        snapshot_download(
            repo_id=repo_id,
            local_dir=target_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ {model_name} downloaded successfully to {target_dir}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 download_model_extended.py <model_name> <repo_id> <target_dir>")
        sys.exit(1)
    
    model_name = sys.argv[1]
    repo_id = sys.argv[2]
    target_dir = sys.argv[3]
    
    success = download_model(model_name, repo_id, target_dir)
    sys.exit(0 if success else 1)
PYTHON_EOF
    
    # Install huggingface-hub if not present
    if ! python3 -c "import huggingface_hub" 2>/dev/null; then
        print_status "Installing huggingface-hub..."
        pip3 install huggingface-hub
    fi
    
    # Run download
    if python3 /tmp/download_model_extended.py "$model_name" "$repo_id" "$target_dir"; then
        print_success "Model $model_name downloaded successfully!"
        
        # Create version metadata
        version_file="$VERSIONS_DIR/${model_name}-${use_case}.version"
        cat > "$version_file" << EOF
Model: $model_name
Use Case: $use_case
Category: $category
Repo: $repo_id
Downloaded: $(date)
Location: $target_dir
Size: $(du -sh "$target_dir" | cut -f1)
GPU Recommendation: $gpu
Description: $description
Status: Ready
EOF
        
        # Update download tracking
        echo "Download completed: $(date)" >> "$download_file"
        echo "Status: Success" >> "$download_file"
        
        # Clean up
        rm -f /tmp/download_model_extended.py
        
        print_success "Model $model_name is ready for $use_case use case!"
    else
        print_error "Failed to download model $model_name"
        echo "Download failed: $(date)" >> "$download_file"
        echo "Status: Failed" >> "$download_file"
        rm -f /tmp/download_model_extended.py
        exit 1
    fi
}

# Function to show current model status
show_extended_model_status() {
    print_status "Extended Model Status:"
    echo "============================"
    
    # Show directory sizes
    echo "Storage Usage:"
    du -sh "$MODELS_DIR"/* 2>/dev/null | while read size path; do
        echo "  $size $path"
    done
    
    echo ""
    echo "Models by Use Case:"
    
    # Check each use case category
    for use_case in avatar stt tts agent multimodal video; do
        use_case_path="$MODELS_STORAGE/$use_case"
        if [ -d "$use_case_path" ]; then
            models=$(find "$use_case_path" -maxdepth 2 -type d -name "*" | wc -l)
            if [ "$models" -gt 1 ]; then
                echo "  $use_case: $((models-1)) models"
                find "$use_case_path" -maxdepth 2 -type d -name "*" | grep -v "^$use_case_path$" | while read model; do
                    model_name=$(basename "$model")
                    size=$(du -sh "$model" 2>/dev/null | cut -f1)
                    echo "    - $model_name ($size)"
                done
            else
                echo "  $use_case: No models"
            fi
        fi
    done
}

# Function to show help
show_extended_help() {
    cat << 'EOF'
Extended AI Model Management Script

Usage: $0 <command> [options]

Commands:
  setup                    - Create extended directory structure
  categories              - Show available use case categories
  models <use_case>       - Show models for specific use case
  download-use-case <use_case> <model> - Download model for specific use case
  status                  - Show current model status
  help                    - Show this help message

Use Cases:
  avatar                  - Talking head avatars and lip sync
  stt                     - Speech-to-text (Indian languages)
  tts                     - Text-to-speech (Indian languages)
  agent                   - Content generation and executing agents
  multimodal             - Multi-modal temporal agentic RAG
  video                   - Video-to-text understanding and content generation

Examples:
  $0 setup                                    # Create directory structure
  $0 categories                              # Show all use case categories
  $0 models avatar                           # Show avatar models
  $0 download-use-case avatar sadtalker      # Download SadTalker for avatars
  $0 download-use-case stt whisper-large-v3  # Download Whisper for STT
  $0 download-use-case video video-llava     # Download Video-LLaVA for video understanding
  $0 status                                  # Show current status

Note: Models are organized by use case and downloaded to /opt/ai-models/models/.
EOF
}

# Main script logic
case "${1:-help}" in
    setup)
        create_extended_directory_structure
        ;;
    categories)
        show_use_case_categories
        ;;
    models)
        show_models_by_use_case "$2"
        ;;
    download-use-case)
        download_model_by_use_case "$2" "$3"
        ;;
    status)
        show_extended_model_status
        ;;
    help|*)
        show_extended_help
        ;;
esac
