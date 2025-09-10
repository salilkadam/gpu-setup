# Storage Setup Documentation

## Overview
This document describes the optimized storage structure for AI models, Kubernetes, and Docker workloads on the GPU server.

## Storage Architecture

### Physical Storage
- **NVMe0 (3.64TB)**: OS and system files
- **NVMe1 (3.64TB)**: Dedicated for AI/K8s/Docker workloads
- **SATA**: Available for future expansion

### LVM Volume Groups
- **docker-vg**: 3.64TB on NVMe1
- **ubuntu-vg-1**: 3.64TB on NVMe0 (OS)

### Logical Volumes (NVMe1)
- **docker-lv**: 1.5TB - Docker containers and images
- **k8s-storage-lv**: 1TB - Kubernetes persistent storage
- **bulk-cache-lv**: 366GB - Shared cache and bulk data
- **temp-work-lv**: 800GB - Temporary processing and builds

## Directory Structure

### AI Models Storage (`/opt/ai-models`)
```
/opt/ai-models/
├── models/          # Downloaded AI models (vLLM, transformers, etc.)
├── cache/           # Model inference cache
├── downloads/       # Temporary download location
└── checkpoints/     # Training checkpoints and fine-tuned models
```

### Kubernetes Storage (`/opt/k8s-storage`)
```
/opt/k8s-storage/
├── etcd/            # etcd data directory
├── volumes/         # Persistent volumes
├── logs/            # K8s logs and audit
└── backups/         # Cluster backups
```

### Bulk Cache (`/opt/bulk-cache`)
```
/opt/bulk-cache/
├── docker-layers/   # Shared Docker layer cache
├── model-cache/     # Shared model cache across containers
└── shared-data/     # Shared datasets and resources
```

### Temporary Work (`/opt/temp-work`)
```
/opt/temp-work/
├── builds/          # Build artifacts and compilation
├── processing/      # Temporary data processing
└── scratch/         # Scratch space for operations
```

## Performance Optimizations

### Mount Options
- **ext4 filesystem**: Optimized for large files and AI workloads
- **noatime**: Disable access time updates for better performance
- **nodiratime**: Disable directory access time updates
- **barrier=0**: Disable write barriers for better performance (with UPS)

### Access Patterns
- **AI Models**: Read-heavy, large files (GB to TB)
- **Kubernetes**: Mixed read/write, small to medium files
- **Docker**: Mixed, layer-based access patterns
- **Cache**: High-frequency read/write operations

## Usage Guidelines

### AI Models
- Store models in `/opt/ai-models/models/`
- Use symbolic links for easy access: `~/ai-models -> /opt/ai-models`
- Models are shared across all containers and services
- Cache frequently used models in `/opt/ai-models/cache/`

### Kubernetes
- Persistent volumes mount to `/opt/k8s-storage/volumes/`
- etcd data stored in `/opt/k8s-storage/etcd/`
- Logs and backups in respective subdirectories

### Docker
- Docker data directory: `/opt/docker-data/`
- Shared layers cached in `/opt/bulk-cache/docker-layers/`
- Temporary builds in `/opt/temp-work/builds/`

## Monitoring

### Disk Usage
```bash
# Check storage usage
df -h /opt/*

# Check specific directories
du -sh /opt/ai-models/*
du -sh /opt/k8s-storage/*
```

### Performance Monitoring
```bash
# I/O statistics
iostat -x 1

# Disk activity
iotop
```

## Backup Strategy

### Critical Data
- AI models in `/opt/ai-models/models/`
- Kubernetes etcd data in `/opt/k8s-storage/etcd/`
- Configuration files and scripts

### Backup Locations
- Local backups: `/opt/k8s-storage/backups/`
- Remote backups: Configure external storage
- Model backups: Consider cloud storage for large models

## Maintenance

### Regular Tasks
- Monitor disk usage and clean up temporary files
- Update model cache and remove unused models
- Backup critical data regularly
- Check filesystem health with `fsck`

### Expansion
- Add SATA drives for additional storage
- Expand LVM volumes as needed
- Consider RAID for redundancy

## Environment Variables

Add to your shell profile:
```bash
export AI_MODELS_PATH="/opt/ai-models"
export K8S_STORAGE_PATH="/opt/k8s-storage"
export BULK_CACHE_PATH="/opt/bulk-cache"
export TEMP_WORK_PATH="/opt/temp-work"
```

## Docker Integration

### Volume Mounts
```yaml
volumes:
  - /opt/ai-models:/app/models:ro
  - /opt/bulk-cache:/app/cache:rw
  - /opt/temp-work:/app/temp:rw
```

### Performance Tuning
- Use `--shm-size` for shared memory
- Mount cache directories for better performance
- Use read-only mounts for model files

---

**Last Updated**: September 10, 2025  
**Storage Total**: 3.64TB NVMe + 3.64TB NVMe (OS)  
**Available for AI/K8s**: 3.64TB NVMe
