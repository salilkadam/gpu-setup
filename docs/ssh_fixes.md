# SSH Connection Stability Fixes

## Server-Side Configuration Changes

### 1. Enable SSH Keep-Alive (Recommended)
Add these lines to `/etc/ssh/sshd_config`:

```bash
# Enable TCP keep-alive
TCPKeepAlive yes

# Send keep-alive messages every 60 seconds
ClientAliveInterval 60

# Allow 3 missed keep-alive messages before disconnecting
ClientAliveCountMax 3

# Increase login grace time for slow connections
LoginGraceTime 5m
```

### 2. Apply Changes
```bash
sudo systemctl reload ssh
```

## Client-Side Configuration

### 1. Create SSH Client Config
Create `~/.ssh/config` with:

```bash
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    Compression yes
    ControlMaster auto
    ControlPath ~/.ssh/control-%h-%p-%r
    ControlPersist 10m
```

## Network Troubleshooting

### 1. Check Network Interface
```bash
# Monitor packet drops
watch -n 1 'cat /proc/net/dev | grep eno2'

# Check for network errors
ethtool -S eno2 | grep -i error
```

### 2. Network Optimization
```bash
# Increase network buffer sizes
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 87380 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' >> /etc/sysctl.conf
sysctl -p
```

## Monitoring Commands

### 1. Real-time SSH Connection Monitoring
```bash
# Monitor active SSH connections
watch -n 1 'ss -tuln | grep :22'

# Monitor SSH logs in real-time
sudo tail -f /var/log/auth.log | grep sshd
```

### 2. Network Quality Testing
```bash
# Test network stability
ping -c 100 192.168.0.98 | grep -E "loss|time"

# Test SSH connection stability
for i in {1..10}; do
  time ssh -o ConnectTimeout=10 192.168.0.98 'echo "Connection $i successful"'
  sleep 2
done
```

## Expected Results After Fixes

- Reduced connection drops
- Better handling of network interruptions
- Automatic reconnection for brief network issues
- Improved connection stability for long-running sessions
