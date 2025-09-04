#!/bin/bash

# Docker-based Model Download Script
# Downloads AI models using Docker containers to avoid Python environment issues

set -e

# Color functions
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Configuration
MODELS_DIR="/opt/ai-models"
MODELS_STORAGE="$MODELS_DIR/models"
DOWNLOADS_DIR="$MODELS_DIR/downloads"
VERSIONS_DIR="$MODELS_DIR/versions"
NETWORK_NAME="ai-network"
HF_TOKEN="${HF_TOKEN:-}"

# Model registry for downloading
declare -A MODEL_REGISTRY

# 1. TALKING HEAD AVATARS & LIP SYNC
MODEL_REGISTRY["sadtalker"]="CVPR2023/SadTalker|avatar|8GB|GPU 0|Real-time talking head generation"
MODEL_REGISTRY["wav2lip"]="rudrabha/Wav2Lip|avatar|4GB|GPU 0|High-quality lip synchronization"
MODEL_REGISTRY["facefusion"]="facefusion/facefusion|avatar|6GB|GPU 0|Advanced face swapping and manipulation"
MODEL_REGISTRY["animatediff"]="guoyww/AnimateDiff|avatar|8GB|GPU 0|Text-to-video animation capabilities"

# 2. MULTILINGUAL STT (Indian Languages)
MODEL_REGISTRY["whisper-large-v3"]="openai/whisper-large-v3|stt|10GB|GPU 0|OpenAI's latest multilingual model"
MODEL_REGISTRY["whisperlive"]="guillaumekln/faster-whisper-large-v3|stt|10GB|GPU 0|Real-time streaming version"
MODEL_REGISTRY["m2m100"]="facebook/m2m100_418M|stt|2GB|GPU 0|Facebook's multilingual model"
MODEL_REGISTRY["indicwhisper"]="ai4bharat/indic-whisper|stt|8GB|GPU 0|Specialized for Indian languages"

# 3. MULTILINGUAL TTS (Indian Languages)
MODEL_REGISTRY["coqui-tts"]="tts_models/multilingual/multi-dataset/your_tts|tts|6GB|GPU 0|Excellent Indian language support"
MODEL_REGISTRY["bark"]="suno/bark|tts|12GB|GPU 0|High-quality multilingual TTS"
MODEL_REGISTRY["valle-x"]="microsoft/speecht5_tts|tts|8GB|GPU 0|Microsoft's multilingual TTS"
MODEL_REGISTRY["indic-tts"]="ai4bharat/indic-tts|tts|4GB|GPU 0|Specialized for Indian languages"

# 4. CONTENT GENERATION & EXECUTING AGENTS (Multi-use case models)
MODEL_REGISTRY["deepseek-coder-33b"]="deepseek-ai/deepseek-coder-33b-instruct|agent|66GB|GPU 1|Multi-use: Coding, reasoning, content generation, multilingual"
MODEL_REGISTRY["deepseek-llm-67b"]="deepseek-ai/deepseek-llm-67b-chat|agent|134GB|GPU 1|Multi-use: Reasoning, content, coding, analysis, multilingual"
MODEL_REGISTRY["qwen2-72b"]="Qwen/Qwen2.5-72B-Instruct|agent|144GB|GPU 1|Multi-use: Reasoning, coding, content, multilingual, vision-capable"
MODEL_REGISTRY["llama3.1-8b"]="meta-llama/Meta-Llama-3.1-8B-Instruct|agent|16GB|GPU 0|Multi-use: Fast reasoning, coding, content, multilingual"
MODEL_REGISTRY["llama3.1-70b"]="meta-llama/Meta-Llama-3.1-70B-Instruct|agent|140GB|GPU 1|Multi-use: Best reasoning, coding, content, multilingual"
MODEL_REGISTRY["codellama-34b"]="codellama/CodeLlama-34b-Instruct-hf|agent|68GB|GPU 1|Multi-use: Coding, reasoning, content, multilingual"
MODEL_REGISTRY["phi-3.5-14b"]="microsoft/Phi-3.5-14B-Instruct|agent|28GB|GPU 0|Multi-use: Fast reasoning, coding, content, multilingual"
MODEL_REGISTRY["gemma2-27b"]="google/gemma2-27b-it|agent|54GB|GPU 1|Multi-use: Reasoning, coding, content, multilingual"

# 5. MULTI-MODAL TEMPORAL AGENTIC RAG (Multi-use case models)
MODEL_REGISTRY["llava-13b"]="liuhaotian/llava-v1.5-13b|multimodal|26GB|GPU 1|Multi-use: Vision-language, content generation, reasoning"
MODEL_REGISTRY["cogvlm-17b"]="THUDM/cogvlm-chat-hf|multimodal|34GB|GPU 1|Multi-use: Visual reasoning, content, analysis"
MODEL_REGISTRY["qwen-vl-7b"]="Qwen/Qwen-VL-7B|multimodal|14GB|GPU 0|Multi-use: Vision-language, multilingual, content"
MODEL_REGISTRY["instructblip-7b"]="Salesforce/instructblip-vicuna-7b|multimodal|14GB|GPU 0|Multi-use: Vision-language, instruction following"
MODEL_REGISTRY["llava-1.6-34b"]="liuhaotian/llava-v1.6-34b|multimodal|68GB|GPU 1|Multi-use: Advanced vision-language, reasoning, content"
MODEL_REGISTRY["cogvlm-2-19b"]="THUDM/cogvlm2-19b|multimodal|38GB|GPU 1|Multi-use: Latest vision-language, reasoning, content"

# 6. VIDEO-TO-TEXT UNDERSTANDING & CONTENT GENERATION (Multi-use case models)
MODEL_REGISTRY["video-llava"]="LanguageBind/Video-LLaVA-7B|video|26GB|GPU 1|Multi-use: Video understanding, content generation, reasoning"
MODEL_REGISTRY["videochat"]="microsoft/DialoGPT-medium|video|14GB|GPU 0|Multi-use: Video conversation, content, analysis"
MODEL_REGISTRY["video-chatgpt"]="microsoft/DialoGPT-large|video|20GB|GPU 1|Multi-use: Video analysis, reasoning, content"
MODEL_REGISTRY["univl"]="microsoft/univl-base|video|18GB|GPU 0|Multi-use: Video-language understanding, content, reasoning"
MODEL_REGISTRY["video-llava-1.6"]="liuhaotian/Video-LLaVA-1.6-34B|video|68GB|GPU 1|Multi-use: Advanced video understanding, reasoning, content"
MODEL_REGISTRY["video-cogvlm"]="THUDM/video-cogvlm|video|38GB|GPU 1|Multi-use: Latest video understanding, reasoning, content"

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if models directory exists
    if [ ! -d "$MODELS_DIR" ]; then
        print_error "Models directory $MODELS_DIR does not exist. Please run setup first."
        exit 1
    fi
    
    # Create network if it doesn't exist
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        print_warning "Network '$NETWORK_NAME' not found. Creating it..."
        docker network create "$NETWORK_NAME"
        print_success "Network '$NETWORK_NAME' created"
    fi
    
    print_success "Prerequisites check passed"
}

# Function to download model using Docker
download_model_docker() {
    local model_name="$1"
    local use_case="$2"
    
    if [[ -z "${MODEL_REGISTRY[$model_name]}" ]]; then
        print_error "Model $model_name not found in registry"
        return 1
    fi
    
    IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model_name]}"
    
    if [ "$category" != "$use_case" ]; then
        print_error "Model $model_name is not in the $use_case category"
        echo "Model $model_name belongs to category: $category"
        return 1
    fi
    
    # Determine target directory
    local target_dir="$MODELS_STORAGE/$use_case/$model_name"
    
    if [ -d "$target_dir" ] && [ "$(ls -A "$target_dir" 2>/dev/null)" ]; then
        print_warning "Model $model_name already exists at $target_dir with content"
        echo "Skipping download..."
        return 0
    fi
    
    # Remove empty directory if it exists
    if [ -d "$target_dir" ]; then
        rm -rf "$target_dir"
    fi
    
    # Create target directory
    mkdir -p "$target_dir"
    
    print_status "Downloading $model_name for $use_case use case..."
    print_status "Model: $model_name"
    echo "  Repo: $repo_id"
    echo "  Size: $size"
    echo "  GPU: $gpu"
    echo "  Description: $description"
    echo "  Target: $target_dir"
    
    # Create download tracking file
    local download_file="$DOWNLOADS_DIR/${model_name}-${use_case}.download"
    echo "Download started: $(date)" > "$download_file"
    echo "Model: $model_name" >> "$download_file"
    echo "Use Case: $use_case" >> "$download_file"
    echo "Repo: $repo_id" >> "$download_file"
    
    # Download using Docker container
    print_status "Starting download using Docker..."
    
    if docker run --rm \
        --network "$NETWORK_NAME" \
        -v "$target_dir:/app/model" \
        -v "$(pwd)/scripts/download_model.py:/app/download_model.py:ro" \
        -e HF_TOKEN="$HF_TOKEN" \
        python:3.10-slim \
        bash -c "
            pip install huggingface_hub &&
            python /app/download_model.py '$repo_id' '/app/model' '$model_name'
        "; then
        
        print_success "Model $model_name downloaded successfully!"
        
        # Create version metadata
        local version_file="$VERSIONS_DIR/${model_name}-${use_case}.version"
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
        
        print_success "Model $model_name is ready for $use_case use case!"
        return 0
    else
        print_error "Failed to download model $model_name"
        echo "Download failed: $(date)" >> "$download_file"
        echo "Status: Failed" >> "$download_file"
        return 1
    fi
}

# Function to download models by use case
download_use_case_models() {
    local use_case="$1"
    
    case "$use_case" in
        avatar)
            print_status "Downloading avatar models..."
            for model in sadtalker wav2lip facefusion animatediff; do
                download_model_docker "$model" "avatar"
                echo ""
            done
            ;;
        stt)
            print_status "Downloading STT models..."
            for model in whisper-large-v3 whisperlive m2m100 indicwhisper; do
                download_model_docker "$model" "stt"
                echo ""
            done
            ;;
        tts)
            print_status "Downloading TTS models..."
            for model in coqui-tts bark valle-x indic-tts; do
                download_model_docker "$model" "tts"
                echo ""
            done
            ;;
        agent)
            print_status "Downloading agent models..."
            for model in phi-3.5-14b llama3.1-8b; do
                download_model_docker "$model" "agent"
                echo ""
            done
            ;;
        multimodal)
            print_status "Downloading multimodal models..."
            for model in qwen-vl-7b instructblip-7b; do
                download_model_docker "$model" "multimodal"
                echo ""
            done
            ;;
        video)
            print_status "Downloading video models..."
            for model in univl videochat; do
                download_model_docker "$model" "video"
                echo ""
            done
            ;;
        all)
            print_status "Downloading models for all use cases..."
            download_use_case_models "avatar"
            download_use_case_models "stt"
            download_use_case_models "tts"
            download_use_case_models "agent"
            download_use_case_models "multimodal"
            download_use_case_models "video"
            ;;
        *)
            print_error "Unknown use case: $use_case"
            echo "Available use cases: avatar, stt, tts, agent, multimodal, video, all"
            exit 1
            ;;
    esac
}

# Function to show available models
show_available_models() {
    print_status "Available models for download:"
    echo ""
    
    for use_case in avatar stt tts agent multimodal video; do
        echo "=== $use_case ==="
        for model in "${!MODEL_REGISTRY[@]}"; do
            if [[ "${MODEL_REGISTRY[$model]}" == *"|$use_case|"* ]]; then
                IFS='|' read -r repo_id category size gpu description <<< "${MODEL_REGISTRY[$model]}"
                echo "  $model ($size) - $description"
            fi
        done
        echo ""
    done
}

# Function to show download status
show_download_status() {
    print_status "Download Status:"
    echo ""
    
    for use_case in avatar stt tts agent multimodal video; do
        echo "=== $use_case ==="
        local use_case_dir="$MODELS_STORAGE/$use_case"
        if [ -d "$use_case_dir" ]; then
            for model_dir in "$use_case_dir"/*; do
                if [ -d "$model_dir" ]; then
                    local model_name=$(basename "$model_dir")
                    if [ "$(ls -A "$model_dir" 2>/dev/null)" ]; then
                        local size=$(du -sh "$model_dir" | cut -f1)
                        echo "  ✅ $model_name ($size) - Downloaded"
                    else
                        echo "  ⏳ $model_name - Directory created, not downloaded"
                    fi
                fi
            done
        else
            echo "  ❌ Directory not created"
        fi
        echo ""
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [ARGS]"
    echo ""
    echo "Commands:"
    echo "  download <use_case>     - Download models for specific use case"
    echo "  download-all            - Download models for all use cases"
    echo "  models                  - Show available models"
    echo "  status                  - Show download status"
    echo "  help                    - Show this help"
    echo ""
    echo "Use Cases:"
    echo "  avatar                  - Talking head avatars and lip sync"
    echo "  stt                     - Speech-to-text (Indian languages)"
    echo "  tts                     - Text-to-speech (Indian languages)"
    echo "  agent                   - Content generation and executing agents"
    echo "  multimodal             - Multi-modal temporal agentic RAG"
    echo "  video                   - Video-to-text understanding and content generation"
    echo ""
    echo "Examples:"
    echo "  $0 download agent       # Download agent models"
    echo "  $0 download avatar      # Download avatar models"
    echo "  $0 download-all         # Download all models"
    echo "  $0 status               # Check download status"
}

# Main script logic
main() {
    case "${1:-help}" in
        download)
            if [ -z "$2" ]; then
                print_error "Please specify use case for download"
                show_usage
                exit 1
            fi
            check_prerequisites
            download_use_case_models "$2"
            ;;
        download-all)
            check_prerequisites
            download_use_case_models "all"
            ;;
        models)
            show_available_models
            ;;
        status)
            show_download_status
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"
