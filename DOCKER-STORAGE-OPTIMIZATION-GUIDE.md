# Docker Storage Optimization Guide

## Overview
This guide provides a comprehensive solution to increase Docker storage space and configure external volume mounts to prevent Docker from consuming ephemeral storage on the GPU server.

## Problem Analysis
- **Current Issue**: GPU server has only 139GB ephemeral storage
- **Docker Images**: Consuming ephemeral storage space
- **Volume Storage**: Some volumes stored inside Docker instead of external mounts
- **Result**: Disk pressure causing pod evictions

## Solution Components

### 1. Increase Ephemeral Storage
- **Current**: 139GB
- **Target**: 500GB (or available space)
- **Method**: Kubelet configuration updates

### 2. Configure External Volume Mounts
- **Docker Data Root**: `/opt/docker-data`
- **External Volumes**: `/opt/external-volumes`
- **Benefits**: Prevents Docker from consuming ephemeral storage

### 3. Optimize Docker Configuration
- **Storage Driver**: overlay2
- **Garbage Collection**: Improved thresholds
- **Log Management**: Size limits and rotation

## Implementation Steps

### Step 1: Increase Ephemeral Storage
```bash
# Run on GPU server node
sudo ./increase-ephemeral-storage.sh
```

**What this does:**
- Stops k3s service
- Updates kubelet configuration
- Increases ephemeral storage allocation
- Configures better garbage collection
- Restarts k3s service

### Step 2: Configure Docker Storage
```bash
# Run on GPU server node
sudo ./configure-docker-storage.sh
```

**What this does:**
- Moves Docker data to `/opt/docker-data`
- Creates external volume directories
- Updates Docker daemon configuration
- Configures systemd overrides
- Restarts Docker service

### Step 3: Update Docker Compose
```bash
# Use the new docker-compose file
docker-compose -f docker-compose-external-volumes.yml up -d
```

**Key Changes:**
- All volumes mounted to `/opt/external-volumes`
- No Docker-managed volumes
- External storage for models, cache, logs, data

## Directory Structure

```
/opt/
├── docker-data/              # Docker data root (increased space)
│   ├── overlay2/             # Docker storage driver
│   ├── containers/           # Container data
│   └── images/               # Docker images
├── external-volumes/         # External volume mounts
│   ├── models/               # AI models (read-only)
│   ├── cache/                # Application cache
│   │   ├── vllm/
│   │   ├── stt/
│   │   ├── tts/
│   │   └── wan/
│   ├── logs/                 # Application logs
│   │   ├── vllm/
│   │   ├── nginx/
│   │   ├── redis/
│   │   └── ...
│   └── data/                 # Application data
│       ├── redis/
│       ├── prometheus/
│       └── grafana/
└── ai-models -> external-volumes/models  # Symbolic link
```

## Volume Mount Strategy

### Before (Problematic)
```yaml
volumes:
  - vllm_cache:/app/cache      # Docker-managed volume
  - vllm_logs:/app/logs        # Docker-managed volume
```

### After (Optimized)
```yaml
volumes:
  - /opt/external-volumes/cache/vllm:/app/cache    # External mount
  - /opt/external-volumes/logs/vllm:/app/logs      # External mount
```

## Benefits

### 1. Increased Storage
- **Ephemeral Storage**: 139GB → 500GB
- **Docker Space**: Dedicated allocation
- **External Volumes**: Unlimited (based on available disk)

### 2. Better Resource Management
- **Garbage Collection**: Improved thresholds (80%/85%)
- **Eviction Policies**: Better configured
- **Log Rotation**: Size limits and file counts

### 3. Persistent Storage
- **Models**: Stored externally, not in Docker
- **Cache**: External mounts, survives container restarts
- **Logs**: Centralized logging location
- **Data**: Application data persisted externally

## Monitoring

### Check Storage Usage
```bash
# Check Docker storage
docker system df

# Check external volumes
du -sh /opt/external-volumes/*

# Check node status
kubectl describe node gpu-server
```

### Check Disk Pressure
```bash
# Check node conditions
kubectl get nodes gpu-server -o json | jq '.status.conditions[] | select(.type == "DiskPressure")'

# Check taints
kubectl get nodes gpu-server -o json | jq '.spec.taints'
```

## Troubleshooting

### If Docker Fails to Start
```bash
# Check Docker logs
journalctl -u docker -f

# Restore backup configuration
sudo cp /opt/backups/docker-config-*/daemon.json /etc/docker/daemon.json
sudo systemctl restart docker
```

### If k3s Fails to Start
```bash
# Check k3s logs
journalctl -u k3s-agent -f

# Restore backup configuration
sudo cp /opt/backups/kubelet-config-*/config.yaml /var/lib/kubelet/config.yaml
sudo systemctl restart k3s-agent
```

### If Pods Still Get Evicted
```bash
# Check disk pressure
kubectl describe node gpu-server | grep -A 5 -B 5 "DiskPressure"

# Remove taint if needed
kubectl taint nodes gpu-server node.kubernetes.io/disk-pressure:NoSchedule-
```

## Verification

### 1. Check Ephemeral Storage
```bash
kubectl describe node gpu-server | grep ephemeral-storage
```

### 2. Check Docker Configuration
```bash
docker info | grep -E "(Storage Driver|Data Root|Docker Root Dir)"
```

### 3. Check External Volumes
```bash
ls -la /opt/external-volumes/
```

### 4. Test Pod Scheduling
```bash
kubectl get pods --all-namespaces -o wide | grep gpu-server
```

## Expected Results

After implementation:
- ✅ **Ephemeral Storage**: Increased to 500GB
- ✅ **Docker Space**: Dedicated allocation
- ✅ **External Volumes**: All data stored externally
- ✅ **No Disk Pressure**: Taint removed
- ✅ **Pod Scheduling**: Normal operation restored
- ✅ **Persistent Storage**: Data survives container restarts

## Maintenance

### Regular Tasks
1. **Monitor Storage Usage**: Check `/opt/external-volumes/` usage
2. **Clean Old Logs**: Rotate or clean old log files
3. **Update Models**: Manage AI model storage
4. **Backup Data**: Regular backups of external volumes

### Storage Expansion
If more space is needed:
1. Add additional storage to the node
2. Update LVM configuration
3. Expand external volume directories
4. Update Docker configuration if needed

---

**Last Updated**: October 20, 2025  
**Status**: Ready for Implementation  
**Priority**: High (Resolves disk pressure issues)


