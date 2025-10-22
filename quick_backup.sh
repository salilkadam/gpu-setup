#!/bin/bash

# Quick Backup Script - Current State
# This creates a lightweight backup of the current setup before PyTorch build completion

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_progress() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

# Configuration
BACKUP_DIR="/home/skadam/gpu-setup-backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
QUICK_BACKUP_NAME="quick-backup-${TIMESTAMP}"

echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${WHITE}║                        Quick Backup - Current State                         ║${NC}"
echo -e "${WHITE}║                    (Before PyTorch Build Completion)                        ║${NC}"
echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR/$QUICK_BACKUP_NAME"

print_progress "Creating quick backup of current state..."

# Backup current configurations
print_progress "Backing up configurations..."
cp docker-compose.yml "$BACKUP_DIR/$QUICK_BACKUP_NAME/"
cp -r docker/ "$BACKUP_DIR/$QUICK_BACKUP_NAME/"
cp -r scripts/ "$BACKUP_DIR/$QUICK_BACKUP_NAME/" 2>/dev/null || true
cp -r k8s/ "$BACKUP_DIR/$QUICK_BACKUP_NAME/" 2>/dev/null || true

# Backup current Docker images
print_progress "Backing up current Docker images..."
docker images > "$BACKUP_DIR/$QUICK_BACKUP_NAME/docker-images-list.txt"
docker save ai-wan-service:latest | gzip > "$BACKUP_DIR/$QUICK_BACKUP_NAME/ai-wan-service-current.tar.gz" 2>/dev/null || print_warning "ai-wan-service image not found"

# Backup current build progress
print_progress "Backing up current build progress..."
if [ -f "/tmp/pytorch_build.log" ]; then
    cp /tmp/pytorch_build.log "$BACKUP_DIR/$QUICK_BACKUP_NAME/pytorch-build-progress.log"
    print_progress "PyTorch build progress saved"
fi

# Backup system information
print_progress "Backing up system information..."
uname -a > "$BACKUP_DIR/$QUICK_BACKUP_NAME/system-info.txt"
nvidia-smi > "$BACKUP_DIR/$QUICK_BACKUP_NAME/nvidia-smi.txt" 2>/dev/null || true
docker version > "$BACKUP_DIR/$QUICK_BACKUP_NAME/docker-version.txt"

# Create quick documentation
cat > "$BACKUP_DIR/$QUICK_BACKUP_NAME/README.md" << EOF
# Quick Backup - $TIMESTAMP

This is a quick backup of the current GPU setup state before PyTorch build completion.

## Current Status

- **PyTorch Build**: In progress (check pytorch-build-progress.log)
- **Docker Images**: Current state saved
- **Configurations**: All configs backed up
- **System Info**: Hardware and software details saved

## Contents

- \`docker-compose.yml\` - Main orchestration file
- \`docker/\` - Dockerfile configurations
- \`scripts/\` - Setup and utility scripts
- \`k8s/\` - Kubernetes configurations
- \`ai-wan-service-current.tar.gz\` - Current WAN service image
- \`pytorch-build-progress.log\` - Current build progress
- \`system-info.txt\` - System information
- \`nvidia-smi.txt\` - GPU information
- \`docker-version.txt\` - Docker version info

## Next Steps

1. Wait for PyTorch build to complete
2. Run the full backup script: \`./backup_setup.sh\`
3. Push to Docker Hub: \`./push_to_dockerhub.sh\`

## Restoration

To restore this quick backup:
1. Extract the backup
2. Load Docker image: \`gunzip -c ai-wan-service-current.tar.gz | docker load\`
3. Start services: \`docker compose up -d\`

Created: $TIMESTAMP
EOF

# Create archive
print_progress "Creating archive..."
cd "$BACKUP_DIR"
tar -czf "${QUICK_BACKUP_NAME}.tar.gz" "$QUICK_BACKUP_NAME"

# Display summary
echo ""
print_status "✅ Quick backup completed!"
print_status "📁 Location: $BACKUP_DIR/$QUICK_BACKUP_NAME"
print_status "📦 Archive: $BACKUP_DIR/${QUICK_BACKUP_NAME}.tar.gz"
print_status "💾 Size: $(du -h "${QUICK_BACKUP_NAME}.tar.gz" | cut -f1)"

echo ""
print_warning "⚠️  This is a quick backup of the current state."
print_warning "   Run the full backup script after PyTorch build completes for complete preservation."


