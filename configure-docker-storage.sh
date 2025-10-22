#!/bin/bash

# Docker Storage Configuration Script for GPU Server
# This script increases Docker storage space and configures external volume mounts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

print_progress() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

# Configuration
DOCKER_DATA_ROOT="/opt/docker-data"
DOCKER_CONFIG_DIR="/etc/docker"
DOCKER_CONFIG_FILE="$DOCKER_CONFIG_DIR/daemon.json"
BACKUP_DIR="/opt/backups/docker-config-$(date +%Y%m%d_%H%M%S)"

print_status "🚀 Starting Docker Storage Configuration..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Create backup directory
print_progress "Creating backup directory..."
mkdir -p "$BACKUP_DIR"

# Backup existing Docker configuration
if [ -f "$DOCKER_CONFIG_FILE" ]; then
    print_progress "Backing up existing Docker configuration..."
    cp "$DOCKER_CONFIG_FILE" "$BACKUP_DIR/daemon.json.backup"
fi

# Stop Docker service
print_progress "Stopping Docker service..."
systemctl stop docker

# Create Docker data directory with proper permissions
print_progress "Creating Docker data directory: $DOCKER_DATA_ROOT"
mkdir -p "$DOCKER_DATA_ROOT"
chown root:root "$DOCKER_DATA_ROOT"
chmod 755 "$DOCKER_DATA_ROOT"

# Create Docker config directory
print_progress "Creating Docker config directory..."
mkdir -p "$DOCKER_CONFIG_DIR"

# Create new Docker daemon configuration
print_progress "Creating Docker daemon configuration..."
cat > "$DOCKER_CONFIG_FILE" << 'EOF'
{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "data-root": "/opt/docker-data",
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "default-address-pools": [
    {
      "base": "172.17.0.0/12",
      "size": 16
    }
  ],
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  },
  "shutdown-timeout": 15,
  "max-concurrent-downloads": 6,
  "max-concurrent-uploads": 5,
  "default-shm-size": "2g"
}
EOF

# Set proper permissions
chmod 644 "$DOCKER_CONFIG_FILE"
chown root:root "$DOCKER_CONFIG_FILE"

# Create systemd override for Docker service
print_progress "Creating systemd override for Docker service..."
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process
OOMScoreAdjust=-500
EOF

# Reload systemd and restart Docker
print_progress "Reloading systemd configuration..."
systemctl daemon-reload

print_progress "Starting Docker service..."
systemctl start docker

# Wait for Docker to start
sleep 10

# Verify Docker is running
if systemctl is-active --quiet docker; then
    print_status "✅ Docker service is running"
else
    print_error "❌ Docker service failed to start"
    exit 1
fi

# Check Docker info
print_progress "Checking Docker configuration..."
docker info | grep -E "(Storage Driver|Data Root|Docker Root Dir)"

# Create external volume directories
print_progress "Creating external volume directories..."
mkdir -p /opt/external-volumes/{models,cache,logs,data}
chown -R root:root /opt/external-volumes
chmod -R 755 /opt/external-volumes

# Create symbolic links for easy access
print_progress "Creating symbolic links..."
ln -sf /opt/external-volumes/models /opt/ai-models
ln -sf /opt/external-volumes/cache /opt/ai-cache
ln -sf /opt/external-volumes/logs /opt/ai-logs

print_status "🎉 Docker storage configuration completed!"
print_status "📁 Docker data root: $DOCKER_DATA_ROOT"
print_status "📁 External volumes: /opt/external-volumes"
print_status "📁 Backup location: $BACKUP_DIR"

print_warning "⚠️  Important Notes:"
print_warning "   - All Docker data is now stored in $DOCKER_DATA_ROOT"
print_warning "   - External volumes should be mounted to /opt/external-volumes"
print_warning "   - This prevents Docker from consuming ephemeral storage"
print_warning "   - Restart any running containers to use new configuration"

print_status "🔧 Next steps:"
print_status "   1. Update your docker-compose.yml files to use external volume mounts"
print_status "   2. Restart containers to use the new storage configuration"
print_status "   3. Monitor disk usage to ensure external mounts are working"


