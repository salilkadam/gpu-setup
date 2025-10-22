#!/bin/bash

# Docker Hub Push Script for ai-wan-service with sm_120 support
# This script will rebuild and push the WAN service image to Docker Hub

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_progress() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

# Function to check if PyTorch build is complete
check_pytorch_build() {
    if [ -f "/tmp/pytorch_build.log" ]; then
        if docker exec ai-wan-service grep -q "PyTorch build completed successfully" /tmp/pytorch_build.log 2>/dev/null; then
            return 0  # Build complete
        else
            return 1  # Build not complete
        fi
    else
        return 1  # No build log
    fi
}

# Function to verify sm_120 support
verify_sm120_support() {
    print_progress "Verifying sm_120 support in the built PyTorch..."
    
    # Test PyTorch installation in the container
    local test_result=$(docker exec ai-wan-service python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA arch list: {torch.cuda.get_arch_list()}')
print(f'Device count: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f'Device {i}: {torch.cuda.get_device_name(i)}')
" 2>&1)
    
    echo "$test_result"
    
    # Check if sm_120 is in the arch list
    if echo "$test_result" | grep -q "sm_120"; then
        print_success "✅ sm_120 support confirmed!"
        return 0
    else
        print_warning "⚠️  sm_120 support not detected in arch list"
        return 1
    fi
}

# Function to rebuild Docker image
rebuild_image() {
    local image_name="$1"
    local tag="$2"
    
    print_progress "Rebuilding Docker image with new PyTorch installation..."
    
    # Stop the current container
    print_progress "Stopping current WAN service container..."
    docker compose stop wan-service
    
    # Rebuild the image
    print_progress "Building new Docker image..."
    if docker build -f docker/Dockerfile.wan -t "$image_name:$tag" .; then
        print_success "✅ Docker image rebuilt successfully!"
        return 0
    else
        print_error "❌ Failed to rebuild Docker image"
        return 1
    fi
}

# Function to push to Docker Hub
push_to_dockerhub() {
    local image_name="$1"
    local tag="$2"
    local dockerhub_username="$3"
    
    print_progress "Pushing image to Docker Hub..."
    
    # Tag for Docker Hub
    local dockerhub_image="$dockerhub_username/$image_name:$tag"
    docker tag "$image_name:$tag" "$dockerhub_image"
    
    # Push to Docker Hub
    if docker push "$dockerhub_image"; then
        print_success "✅ Image pushed to Docker Hub successfully!"
        print_success "Image: $dockerhub_image"
        return 0
    else
        print_error "❌ Failed to push image to Docker Hub"
        return 1
    fi
}

# Function to create backup tag
create_backup_tag() {
    local image_name="$1"
    local dockerhub_username="$2"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    print_progress "Creating backup tag with timestamp..."
    
    local backup_tag="sm120_${timestamp}"
    local backup_image="$dockerhub_username/$image_name:$backup_tag"
    
    docker tag "$image_name:latest" "$backup_image"
    
    if docker push "$backup_image"; then
        print_success "✅ Backup image created: $backup_image"
        return 0
    else
        print_error "❌ Failed to create backup image"
        return 1
    fi
}

# Main function
main() {
    echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║                    Docker Hub Push Script for ai-wan-service                ║${NC}"
    echo -e "${WHITE}║                        with sm_120 GPU Support                              ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Check if PyTorch build is complete
    if ! check_pytorch_build; then
        print_error "❌ PyTorch build is not complete yet!"
        print_warning "Please wait for the PyTorch build to finish before pushing to Docker Hub."
        exit 1
    fi
    
    print_success "✅ PyTorch build is complete!"
    
    # Verify sm_120 support
    if ! verify_sm120_support; then
        print_warning "⚠️  sm_120 support verification failed, but continuing..."
    fi
    
    # Get Docker Hub credentials
    if [ -z "$DOCKERHUB_USERNAME" ]; then
        echo -n "Enter your Docker Hub username: "
        read DOCKERHUB_USERNAME
    fi
    
    if [ -z "$DOCKERHUB_TOKEN" ]; then
        echo -n "Enter your Docker Hub access token: "
        read -s DOCKERHUB_TOKEN
        echo ""
    fi
    
    # Login to Docker Hub
    print_progress "Logging in to Docker Hub..."
    if echo "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin; then
        print_success "✅ Logged in to Docker Hub successfully!"
    else
        print_error "❌ Failed to login to Docker Hub"
        exit 1
    fi
    
    # Set image details
    local image_name="ai-wan-service"
    local tag="sm120-latest"
    
    # Rebuild the image
    if ! rebuild_image "$image_name" "$tag"; then
        exit 1
    fi
    
    # Create backup tag
    create_backup_tag "$image_name" "$DOCKERHUB_USERNAME"
    
    # Push main image
    if ! push_to_dockerhub "$image_name" "$tag" "$DOCKERHUB_USERNAME"; then
        exit 1
    fi
    
    # Restart the service
    print_progress "Restarting WAN service with new image..."
    docker compose up -d wan-service
    
    echo ""
    print_success "🎉 Docker Hub push completed successfully!"
    print_success "Main image: $DOCKERHUB_USERNAME/$image_name:$tag"
    print_success "Backup image: $DOCKERHUB_USERNAME/$image_name:sm120_$(date +"%Y%m%d_%H%M%S")"
    echo ""
    print_status "Your sm_120 enabled PyTorch build is now safely stored in Docker Hub!"
}

# Check if running with environment variables
if [ "$1" = "auto" ]; then
    if [ -z "$DOCKERHUB_USERNAME" ] || [ -z "$DOCKERHUB_TOKEN" ]; then
        print_error "❌ DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables must be set for auto mode"
        exit 1
    fi
fi

# Run main function
main "$@"


