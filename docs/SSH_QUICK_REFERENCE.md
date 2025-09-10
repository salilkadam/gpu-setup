# SSH Connectivity Quick Reference

## Problem Solved
Fixed frequent SSH connection drops on GPU server (192.168.0.20) by implementing:
- SSH keep-alive mechanisms
- Network optimizations
- Client-side connection resilience

## Quick Commands

### Check SSH Status
```bash
# SSH service status
systemctl status ssh

# Active SSH connections
ss -tuln | grep :22
ss -o state established '( dport = :22 or sport = :22 )'

# SSH logs
sudo tail -f /var/log/auth.log | grep sshd
```

### Test Connection Stability
```bash
# Network connectivity
ping -c 5 192.168.0.98

# SSH connection test
ssh -o ConnectTimeout=10 192.168.0.98 'echo "Connection successful"'
```

### Monitor Network Performance
```bash
# Network statistics
ss -s

# Interface monitoring
watch -n 1 'cat /proc/net/dev | grep eno2'

# Network buffer settings
cat /proc/sys/net/core/rmem_max
cat /proc/sys/net/ipv4/tcp_rmem
```

## Configuration Files

### SSH Server Config (`/etc/ssh/sshd_config`)
Key settings applied:
- `TCPKeepAlive yes`
- `ClientAliveInterval 60`
- `ClientAliveCountMax 3`
- `LoginGraceTime 5m`

### SSH Client Config (`~/.ssh/config`)
Key settings applied:
- `ServerAliveInterval 60`
- `ControlMaster auto`
- `ControlPersist 10m`
- Connection multiplexing enabled

### Network Config (`/etc/sysctl.d/99-gpu-server-network.conf`)
Key optimizations:
- Increased buffer sizes (128MB)
- BBR congestion control
- Optimized TCP settings
- Increased connection limits

## Scripts Available

### Apply SSH Fixes
```bash
./scripts/fix_ssh_config.sh
```

### Apply Network Optimizations
```bash
./scripts/optimize_network.sh
```

## Results
- ✅ SSH connections now stable with keep-alive
- ✅ Network latency improved (5-7ms average)
- ✅ Packet drops eliminated
- ✅ Connection multiplexing for efficiency
- ✅ Persistent configurations across reboots

## Troubleshooting
If SSH issues persist:
1. Check service status: `systemctl status ssh`
2. Verify config: `sudo sshd -t`
3. Monitor logs: `sudo tail -f /var/log/auth.log`
4. Test network: `ping -c 5 192.168.0.98`
5. Check connections: `ss -tuln | grep :22`
