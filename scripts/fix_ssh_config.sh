#!/bin/bash

# SSH Configuration Fix Script
# This script applies SSH server configuration changes to improve connection stability

set -e

echo "=== SSH Configuration Fix Script ==="
echo "Backing up current SSH configuration..."

# Backup current config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backup created"

echo "Applying SSH configuration changes..."

# Create temporary file with new configuration
cat > /tmp/sshd_config_additions << 'EOF'

# SSH Connection Stability Improvements
# Added by fix_ssh_config.sh on $(date)

# Enable TCP keep-alive to detect broken connections
TCPKeepAlive yes

# Send keep-alive messages every 60 seconds
ClientAliveInterval 60

# Allow 3 missed keep-alive messages before disconnecting
ClientAliveCountMax 3

# Increase login grace time for slow connections
LoginGraceTime 5m

# Additional stability settings
MaxStartups 30:60:100
MaxSessions 20
EOF

# Add the new configuration to sshd_config
sudo bash -c 'cat /tmp/sshd_config_additions >> /etc/ssh/sshd_config'

# Clean up temporary file
rm /tmp/sshd_config_additions

echo "✓ SSH configuration updated"

# Test configuration
echo "Testing SSH configuration..."
if sudo sshd -t; then
    echo "✓ SSH configuration test passed"
else
    echo "✗ SSH configuration test failed"
    exit 1
fi

# Reload SSH service
echo "Reloading SSH service..."
sudo systemctl reload ssh
echo "✓ SSH service reloaded"

echo ""
echo "=== SSH Configuration Applied Successfully ==="
echo "Changes made:"
echo "- Enabled TCP keep-alive"
echo "- Set ClientAliveInterval to 60 seconds"
echo "- Set ClientAliveCountMax to 3"
echo "- Increased LoginGraceTime to 5 minutes"
echo "- Increased MaxStartups and MaxSessions"
echo ""
echo "SSH connections should now be more stable."
echo "Monitor connections with: ss -tuln | grep :22"
