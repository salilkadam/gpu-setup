#!/bin/bash

# Complete Setup Backup Script
# This script creates a comprehensive backup of the entire GPU setup
# including Docker images, configurations, and build artifacts

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

# Configuration
BACKUP_DIR="/home/skadam/gpu-setup-backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="gpu-setup-backup-${TIMESTAMP}"

# Function to create backup directory structure
create_backup_structure() {
    print_progress "Creating backup directory structure..."
    
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"/{docker-images,configs,scripts,models,logs,documentation}
    
    print_success "✅ Backup directory created: $BACKUP_DIR/$BACKUP_NAME"
}

# Function to backup Docker images
backup_docker_images() {
    print_progress "Backing up Docker images..."
    
    local images_dir="$BACKUP_DIR/$BACKUP_NAME/docker-images"
    
    # List of images to backup
    local images=(
        "ai-wan-service:latest"
        "ai-routing-api:latest"
        "ai-mcp-server:latest"
        "ai-stt-service:latest"
        "ai-tts-service:latest"
        "ai-vllm-inference-server:latest"
    )
    
    for image in "${images[@]}"; do
        if docker images | grep -q "$image"; then
            print_progress "Saving $image..."
            docker save "$image" | gzip > "$images_dir/${image//\//_}.tar.gz"
            print_success "✅ Saved $image"
        else
            print_warning "⚠️  Image $image not found, skipping..."
        fi
    done
    
    # Save all images as a complete backup
    print_progress "Creating complete Docker images backup..."
    docker save $(docker images -q) | gzip > "$images_dir/all-images.tar.gz"
    print_success "✅ Complete Docker images backup created"
}

# Function to backup configurations
backup_configurations() {
    print_progress "Backing up configurations..."
    
    local configs_dir="$BACKUP_DIR/$BACKUP_NAME/configs"
    
    # Docker Compose and Dockerfiles
    cp docker-compose.yml "$configs_dir/"
    cp -r docker/ "$configs_dir/"
    
    # Kubernetes configurations
    if [ -d "k8s" ]; then
        cp -r k8s/ "$configs_dir/"
    fi
    
    # Scripts
    cp -r scripts/ "$configs_dir/" 2>/dev/null || true
    
    # Environment files
    cp .env* "$configs_dir/" 2>/dev/null || true
    
    print_success "✅ Configurations backed up"
}

# Function to backup models and data
backup_models_and_data() {
    print_progress "Backing up models and data..."
    
    local models_dir="$BACKUP_DIR/$BACKUP_NAME/models"
    
    # Create symbolic links to model directories (don't copy the actual files)
    if [ -d "/opt/ai-models-extended" ]; then
        ln -sf "/opt/ai-models-extended" "$models_dir/ai-models-extended"
        print_progress "Linked /opt/ai-models-extended (${models_dir}/ai-models-extended)"
    fi
    
    if [ -d "/opt/ai-models" ]; then
        ln -sf "/opt/ai-models" "$models_dir/ai-models"
        print_progress "Linked /opt/ai-models (${models_dir}/ai-models)"
    fi
    
    # Backup model metadata
    if [ -d "/opt/ai-models-extended" ]; then
        find /opt/ai-models-extended -name "*.json" -o -name "*.txt" -o -name "*.md" | head -20 | while read file; do
            cp "$file" "$models_dir/" 2>/dev/null || true
        done
    fi
    
    print_success "✅ Models and data backed up"
}

# Function to backup build artifacts
backup_build_artifacts() {
    print_progress "Backing up build artifacts..."
    
    local logs_dir="$BACKUP_DIR/$BACKUP_NAME/logs"
    
    # PyTorch build log
    if [ -f "/tmp/pytorch_build.log" ]; then
        cp /tmp/pytorch_build.log "$logs_dir/"
        print_progress "Saved PyTorch build log"
    fi
    
    # Docker logs
    docker logs ai-wan-service > "$logs_dir/wan-service.log" 2>/dev/null || true
    docker logs ai-routing-api > "$logs_dir/routing-api.log" 2>/dev/null || true
    docker logs ai-mcp-server > "$logs_dir/mcp-server.log" 2>/dev/null || true
    
    # System information
    uname -a > "$logs_dir/system-info.txt"
    nvidia-smi > "$logs_dir/nvidia-smi.txt" 2>/dev/null || true
    docker version > "$logs_dir/docker-version.txt"
    docker images > "$logs_dir/docker-images-list.txt"
    
    print_success "✅ Build artifacts backed up"
}

# Function to create documentation
create_documentation() {
    print_progress "Creating documentation..."
    
    local docs_dir="$BACKUP_DIR/$BACKUP_NAME/documentation"
    
    cat > "$docs_dir/README.md" << EOF
# GPU Setup Backup - $TIMESTAMP

This backup contains a complete GPU setup with sm_120 support for RTX 5090/RTX PRO 6000.

## Contents

- **docker-images/**: All Docker images including the custom PyTorch build
- **configs/**: Docker Compose, Dockerfiles, and Kubernetes configurations
- **scripts/**: All setup and utility scripts
- **models/**: Links to model directories (actual models are in /opt/)
- **logs/**: Build logs, system info, and service logs
- **documentation/**: This documentation

## System Information

- **OS**: $(uname -a)
- **Docker Version**: $(docker --version)
- **NVIDIA Driver**: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits 2>/dev/null || echo "Not available")
- **CUDA Version**: $(nvcc --version 2>/dev/null | grep "release" | cut -d' ' -f5 || echo "Not available")
- **GPUs**: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | tr '\n' ',' | sed 's/,$//' || echo "Not available")

## PyTorch Build Information

- **Build Date**: $TIMESTAMP
- **CUDA Support**: 12.8 with sm_120 architecture
- **GPU Compatibility**: RTX 5090, RTX PRO 6000
- **Build Log**: logs/pytorch_build.log

## Services Included

- **WAN Video Generation Service**: Port 8004
- **Routing API**: Port 8000
- **MCP AI Server**: Port 8080
- **STT Service**: Port 8001
- **TTS Service**: Port 8002
- **vLLM Inference Server**: Port 8003

## Restoration Instructions

1. Install Docker and NVIDIA Container Toolkit
2. Run the restoration script: \`./restore_setup.sh\`
3. Start services: \`docker compose up -d\`
4. Verify GPU support: \`docker exec ai-wan-service python3 -c "import torch; print(torch.cuda.get_arch_list())"\`

## Model Directories

- **Primary**: /opt/ai-models-extended (2TB)
- **Secondary**: /opt/ai-models (500GB)

## Important Notes

- This backup was created after a successful PyTorch build with sm_120 support
- All Docker images include the custom PyTorch installation
- Model files are linked, not copied (to save space)
- Use the restoration script to recreate the entire setup

## Contact

Created by AI Assistant for GPU setup with sm_120 support.
EOF

    # Create restoration script
    cat > "$BACKUP_DIR/$BACKUP_NAME/restore_setup.sh" << 'EOF'
#!/bin/bash

# Setup Restoration Script
# This script restores the complete GPU setup from backup

set -e

BACKUP_DIR="$(dirname "$0")"
RESTORE_DIR="/home/skadam/gpu-setup"

echo "🚀 Starting GPU Setup Restoration..."

# Create restore directory
mkdir -p "$RESTORE_DIR"
cd "$RESTORE_DIR"

# Restore configurations
echo "📁 Restoring configurations..."
cp -r "$BACKUP_DIR/configs"/* ./

# Restore Docker images
echo "🐳 Restoring Docker images..."
for image in "$BACKUP_DIR/docker-images"/*.tar.gz; do
    if [ -f "$image" ]; then
        echo "Loading $(basename "$image")..."
        gunzip -c "$image" | docker load
    fi
done

# Create model directories
echo "📦 Creating model directories..."
sudo mkdir -p /opt/ai-models-extended
sudo mkdir -p /opt/ai-models
sudo chown -R $USER:$USER /opt/ai-models*

# Restore scripts
echo "🔧 Restoring scripts..."
cp -r "$BACKUP_DIR/scripts"/* ./scripts/ 2>/dev/null || true

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

echo "✅ Restoration complete!"
echo "📋 Next steps:"
echo "1. Copy your models to /opt/ai-models-extended"
echo "2. Run: docker compose up -d"
echo "3. Test GPU support with the monitoring script"
EOF

    chmod +x "$BACKUP_DIR/$BACKUP_NAME/restore_setup.sh"
    
    print_success "✅ Documentation created"
}

# Function to create compressed archive
create_archive() {
    print_progress "Creating compressed archive..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    local archive_size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    print_success "✅ Archive created: ${BACKUP_NAME}.tar.gz ($archive_size)"
}

# Function to create checksums
create_checksums() {
    print_progress "Creating checksums..."
    
    cd "$BACKUP_DIR"
    sha256sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.sha256"
    md5sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.md5"
    
    print_success "✅ Checksums created"
}

# Function to display backup summary
display_summary() {
    echo ""
    echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║                            Backup Summary                                  ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    print_success "🎉 Backup completed successfully!"
    print_success "📁 Backup location: $BACKUP_DIR/$BACKUP_NAME"
    print_success "📦 Archive: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    local archive_size=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    print_success "💾 Archive size: $archive_size"
    
    echo ""
    print_status "📋 Backup contents:"
    print_status "  • Docker images with sm_120 PyTorch build"
    print_status "  • Complete configuration files"
    print_status "  • All setup and utility scripts"
    print_status "  • Build logs and system information"
    print_status "  • Restoration script and documentation"
    
    echo ""
    print_status "🚀 To restore on a new system:"
    print_status "  1. Copy ${BACKUP_NAME}.tar.gz to new system"
    print_status "  2. Extract: tar -xzf ${BACKUP_NAME}.tar.gz"
    print_status "  3. Run: ./restore_setup.sh"
    print_status "  4. Start services: docker compose up -d"
    
    echo ""
    print_warning "⚠️  Note: Model files are linked, not copied (to save space)"
    print_warning "   You'll need to copy your models to /opt/ai-models-extended separately"
}

# Main function
main() {
    echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║                        GPU Setup Backup Script                              ║${NC}"
    echo -e "${WHITE}║                    Complete System Backup with sm_120                       ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Check if running as root for some operations
    if [ "$EUID" -eq 0 ]; then
        print_warning "⚠️  Running as root. Some operations may require user permissions."
    fi
    
    # Create backup structure
    create_backup_structure
    
    # Backup components
    backup_docker_images
    backup_configurations
    backup_models_and_data
    backup_build_artifacts
    create_documentation
    
    # Create final archive
    create_archive
    create_checksums
    
    # Display summary
    display_summary
}

# Run main function
main "$@"


