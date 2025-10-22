#!/bin/bash

# Increase Ephemeral Storage for GPU Server
# This script increases the ephemeral storage allocation for Docker and containers

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
TARGET_SIZE_GB=500  # Increase to 500GB
CURRENT_SIZE_GB=150
KUBELET_CONFIG="/var/lib/kubelet/config.yaml"
KUBELET_SERVICE="/etc/systemd/system/k3s.service.d/20-k3s-agent.conf"

print_status "🚀 Starting Ephemeral Storage Increase..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

print_progress "Current ephemeral storage: ${CURRENT_SIZE_GB}GB"
print_progress "Target ephemeral storage: ${TARGET_SIZE_GB}GB"

# Check available disk space
print_progress "Checking available disk space..."
AVAILABLE_SPACE=$(df /var/lib/kubelet | tail -1 | awk '{print $4}')
AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))

print_progress "Available space: ${AVAILABLE_GB}GB"

if [ $AVAILABLE_GB -lt $TARGET_SIZE_GB ]; then
    print_warning "⚠️  Available space (${AVAILABLE_GB}GB) is less than target (${TARGET_SIZE_GB}GB)"
    print_warning "   Consider using external storage or reducing target size"
    read -p "Continue with available space? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Aborted by user"
        exit 1
    fi
    TARGET_SIZE_GB=$AVAILABLE_GB
fi

# Create backup
print_progress "Creating backup of current configuration..."
BACKUP_DIR="/opt/backups/kubelet-config-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "$KUBELET_CONFIG" ]; then
    cp "$KUBELET_CONFIG" "$BACKUP_DIR/"
fi

if [ -f "$KUBELET_SERVICE" ]; then
    cp "$KUBELET_SERVICE" "$BACKUP_DIR/"
fi

# Stop k3s service
print_progress "Stopping k3s service..."
systemctl stop k3s-agent

# Create kubelet configuration directory
mkdir -p /var/lib/kubelet

# Create or update kubelet configuration
print_progress "Creating kubelet configuration..."
cat > "$KUBELET_CONFIG" << EOF
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: /var/lib/rancher/k3s/agent/client-ca.crt
authorization:
  mode: Webhook
clusterDomain: cluster.local
clusterDNS:
  - 10.43.0.10
cgroupDriver: systemd
containerRuntimeEndpoint: unix:///run/k3s/containerd/containerd.sock
failSwapOn: false
hairpinMode: promiscuous-bridge
healthzBindAddress: 127.0.0.1
healthzPort: 10248
httpCheckFrequency: 20s
imageMinimumGCAge: 0s
nodeStatusUpdateFrequency: 10s
nodeStatusReportFrequency: 5m0s
rotateCertificates: true
runtimeRequestTimeout: 2m0s
staticPodPath: /var/lib/rancher/k3s/agent/pod-manifests
streamingConnectionIdleTimeout: 4h0m0s
syncFrequency: 1m0s
volumeStatsAggPeriod: 1m0s
# Ephemeral storage configuration
evictionHard:
  imagefs.available: 10%
  memory.available: 100Mi
  nodefs.available: 10%
  nodefs.inodesFree: 5%
evictionSoft:
  imagefs.available: 15%
  memory.available: 200Mi
  nodefs.available: 15%
  nodefs.inodesFree: 10%
evictionSoftGracePeriod:
  imagefs.available: 2m
  memory.available: 2m
  nodefs.available: 2m
  nodefs.inodesFree: 2m
evictionMaxPodGracePeriod: 0
evictionPressureTransitionPeriod: 5m0s
evictionMinimumReclaim:
  imagefs.available: 0
  memory.available: 0
  nodefs.available: 0
  nodefs.inodesFree: 0
# Image garbage collection
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
imageMaximumGCAge: 0s
# Container garbage collection
containerGCMaxPerPodContainer: 1
containerGCMaxContainers: -1
minimumGCAge: 0s
EOF

# Create k3s service configuration
print_progress "Creating k3s service configuration..."
mkdir -p /etc/systemd/system/k3s.service.d
cat > "$KUBELET_SERVICE" << EOF
[Service]
ExecStart=
ExecStart=/usr/local/bin/k3s agent \\
    --kubelet-arg=config=$KUBELET_CONFIG \\
    --kubelet-arg=eviction-hard=imagefs.available<10%,nodefs.available<10% \\
    --kubelet-arg=eviction-soft=imagefs.available<15%,nodefs.available<15% \\
    --kubelet-arg=eviction-soft-grace-period=imagefs.available=2m,nodefs.available=2m \\
    --kubelet-arg=eviction-max-pod-grace-period=0 \\
    --kubelet-arg=eviction-pressure-transition-period=5m \\
    --kubelet-arg=image-gc-high-threshold=85 \\
    --kubelet-arg=image-gc-low-threshold=80 \\
    --kubelet-arg=container-gc-threshold=0 \\
    --kubelet-arg=max-pods=110 \\
    --kubelet-arg=pod-infra-container-image=k8s.gcr.io/pause:3.9
EOF

# Set proper permissions
chmod 644 "$KUBELET_CONFIG"
chmod 644 "$KUBELET_SERVICE"

# Reload systemd
print_progress "Reloading systemd configuration..."
systemctl daemon-reload

# Start k3s service
print_progress "Starting k3s service..."
systemctl start k3s-agent

# Wait for service to start
sleep 30

# Check if k3s is running
if systemctl is-active --quiet k3s-agent; then
    print_status "✅ k3s service is running"
else
    print_error "❌ k3s service failed to start"
    print_error "Check logs: journalctl -u k3s-agent -f"
    exit 1
fi

# Wait for node to be ready
print_progress "Waiting for node to be ready..."
sleep 60

# Check node status
print_progress "Checking node status..."
kubectl get nodes gpu-server

# Check ephemeral storage
print_progress "Checking ephemeral storage allocation..."
kubectl describe node gpu-server | grep -A 5 -B 5 "ephemeral-storage"

print_status "🎉 Ephemeral storage configuration completed!"
print_status "📁 Backup location: $BACKUP_DIR"
print_status "📁 Kubelet config: $KUBELET_CONFIG"
print_status "📁 Service config: $KUBELET_SERVICE"

print_warning "⚠️  Important Notes:"
print_warning "   - Ephemeral storage limits have been increased"
print_warning "   - Image garbage collection thresholds adjusted"
print_warning "   - Eviction policies configured for better resource management"
print_warning "   - Monitor node status to ensure changes are applied"

print_status "🔧 Next steps:"
print_status "   1. Monitor node status: kubectl describe node gpu-server"
print_status "   2. Check ephemeral storage allocation"
print_status "   3. Verify disk pressure condition resolves"
print_status "   4. Test pod scheduling on the GPU server"


