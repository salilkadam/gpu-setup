#!/bin/bash

# Network Optimization Script for GPU Server
# This script applies network optimizations to improve SSH and general connectivity

set -e

echo "=== Network Optimization Script ==="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as regular user with sudo access."
   exit 1
fi

echo "Applying network optimizations..."

# Create sysctl configuration for network optimization
sudo tee /etc/sysctl.d/99-gpu-server-network.conf > /dev/null << 'EOF'
# Network optimizations for GPU server
# Applied by optimize_network.sh

# Increase network buffer sizes for better performance
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 262144
net.core.wmem_default = 262144

# TCP buffer sizes
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# TCP connection optimizations
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# Increase connection limits
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Reduce timeouts for faster recovery
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 3

# File descriptor limits
fs.file-max = 2097152
EOF

echo "✓ Network configuration file created"

# Apply the configuration
echo "Applying network configuration..."
sudo sysctl -p /etc/sysctl.d/99-gpu-server-network.conf
echo "✓ Network configuration applied"

# Check network interface for errors
echo "Checking network interface status..."
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
echo "Primary interface: $INTERFACE"

if command -v ethtool >/dev/null 2>&1; then
    echo "Network interface statistics:"
    sudo ethtool -S $INTERFACE | grep -E "(error|drop|discard)" || echo "No errors found"
else
    echo "ethtool not available, skipping interface statistics"
fi

# Check current network settings
echo "Current network buffer settings:"
echo "rmem_max: $(cat /proc/sys/net/core/rmem_max)"
echo "wmem_max: $(cat /proc/sys/net/core/wmem_max)"
echo "tcp_rmem: $(cat /proc/sys/net/ipv4/tcp_rmem)"
echo "tcp_wmem: $(cat /proc/sys/net/ipv4/tcp_wmem)"

echo ""
echo "=== Network Optimization Complete ==="
echo "Changes applied:"
echo "- Increased network buffer sizes"
echo "- Optimized TCP settings"
echo "- Enabled BBR congestion control"
echo "- Reduced connection timeouts"
echo "- Increased connection limits"
echo ""
echo "Network optimizations will persist after reboot."
echo "Monitor network performance with: ss -s"
