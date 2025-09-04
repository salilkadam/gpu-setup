# Centralized AI Model Management

## Overview

This document outlines the centralized model management approach for the AI inference server infrastructure. Instead of storing models within individual containers or application directories, all AI models are stored in a centralized location at `/opt/ai-models` for persistent access and efficient management.

## Architecture

### Directory Structure
```
/opt/ai-models/
├── cache/           # Temporary download cache
├── downloads/       # Download progress tracking
├── active/          # Currently active models
├── versions/        # Model version metadata
└── models/          # Organized model storage
    ├── llama2/      # Llama2 family models
    │   ├── llama2-7b/
    │   └── llama2-13b/
    ├── mistral/     # Mistral models
    │   └── mistral-7b/
    ├── codellama/   # Code generation models
    │   └── codellama-13b/
    ├── phi/         # Microsoft Phi models
    │   └── phi-2/
    └── qwen/        # Qwen models
        └── qwen-7b/
```

### Model Organization
Each model is organized by category and stored with its complete Hugging Face repository structure:

```
/opt/ai-models/models/llama2/llama2-7b/
├── config.json
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
├── generation_config.json
├── pytorch_model.bin
├── pytorch_model-00001-of-00002.safetensors
├── pytorch_model-00002-of-00002.safetensors
└── ... (other model files)
```

## Benefits of Centralized Storage

### 1. **Persistence Across Restarts**
- Models remain available after container restarts
- No need to re-download models after system reboots
- Consistent model availability for all applications

### 2. **Shared Access**
- Multiple inference servers can access the same models
- No duplicate storage for the same model
- Efficient resource utilization across the infrastructure

### 3. **Version Control & Metadata**
- Track model versions and download dates
- Maintain model information and requirements
- Easy model lifecycle management

### 4. **Simplified Management**
- Centralized model administration
- Easy model updates and replacements
- Consistent model organization across the system

### 5. **Storage Efficiency**
- Avoid duplicate model downloads
- Optimized storage allocation
- Better disk space utilization

## Model Management Workflow

### 1. **Initial Setup**
```bash
# Create centralized model storage
sudo ./scripts/manage-ai-models.sh setup

# Verify directory structure
ls -la /opt/ai-models/
```

### 2. **Model Download**
```bash
# Download specific models
sudo ./scripts/manage-ai-models.sh download llama2-7b
sudo ./scripts/manage-ai-models.sh download mistral-7b
sudo ./scripts/manage-ai-models.sh download codellama-13b
```

### 3. **Model Status Check**
```bash
# Check current model status
sudo ./scripts/manage-ai-models.sh status

# List available models
sudo ./scripts/manage-ai-models.sh list
```

### 4. **Model Usage in Applications**
```python
import os
# Note: This document will be updated for Triton Inference Server

# Load model from centralized location
models_dir = os.getenv("MODELS_DIR", "/opt/ai-models")
model_path = os.path.join(models_dir, "models", "llama2", "llama2-7b")

# Initialize vLLM with the model
llm = LLM(model=model_path)
```

## Docker Integration

### Volume Mounting
The centralized model storage is mounted into containers as read-only volumes:

```yaml
# docker-compose.yml
services:
  ai-server-1:
    volumes:
      - /opt/ai-models:/opt/ai-models:ro  # Read-only access
    environment:
      - MODELS_DIR=/opt/ai-models
```

### Environment Variables
Applications access the centralized models through environment variables:

```bash
# Set model directory in container
export MODELS_DIR=/opt/ai-models

# Access models in Python
models_dir = os.getenv("MODELS_DIR", "/opt/ai-models")
```

## Model Categories & Recommendations

### **GPU 0 (RTX 5090 - 32GB)**
| Model | Memory | Users | Category | Use Case |
|-------|---------|-------|----------|----------|
| llama2-7b | ~14GB | 15-20 | llama2 | General purpose, chat |
| mistral-7b | ~14GB | 15-20 | mistral | Reasoning, instruction |
| phi-2 | ~7GB | 25-30 | phi | Lightweight, fast |

### **GPU 1 (RTX PRO 6000 - 96GB)**
| Model | Memory | Users | Category | Use Case |
|-------|---------|-------|----------|----------|
| llama2-13b | ~26GB | 20-25 | llama2 | High quality, general |
| codellama-13b | ~26GB | 20-25 | codellama | Code generation |
| llama2-70b | ~70GB | 8-10 | llama2 | State-of-the-art |

## Storage Requirements

### Estimated Storage Needs
- **llama2-7b**: ~13.5GB
- **llama2-13b**: ~25.5GB
- **mistral-7b**: ~13.5GB
- **codellama-13b**: ~25.5GB
- **phi-2**: ~6.5GB
- **qwen-7b**: ~13.5GB

### Total Storage
- **All Models**: ~100GB
- **Recommended**: 200GB+ for future models and versions
- **Cache & Metadata**: ~10GB additional

## Security Considerations

### Access Control
- Models stored with root ownership
- Read-only access for containers
- No write access from applications

### Model Validation
- Verify model checksums after download
- Track model sources and versions
- Maintain audit trail of model usage

## Backup & Recovery

### Backup Strategy
```bash
# Backup model storage
tar -czf /backup/ai-models-$(date +%Y%m%d).tar.gz /opt/ai-models/

# Backup specific categories
tar -czf /backup/llama2-models-$(date +%Y%m%d).tar.gz /opt/ai-models/models/llama2/
```

### Recovery Process
```bash
# Restore from backup
tar -xzf /backup/ai-models-20241201.tar.gz -C /

# Verify model integrity
sudo ./scripts/manage-ai-models.sh status
```

## Monitoring & Maintenance

### Health Checks
```bash
# Check model availability
sudo ./scripts/manage-ai-models.sh status

# Monitor storage usage
df -h /opt/ai-models

# Check model integrity
find /opt/ai-models/models -name "*.bin" -exec ls -la {} \;
```

### Cleanup Operations
```bash
# Clean old cache files
sudo ./scripts/manage-ai-models.sh cleanup

# Remove unused models
rm -rf /opt/ai-models/models/phi/phi-1.5  # Example
```

## Best Practices

### 1. **Model Organization**
- Use consistent naming conventions
- Group models by family/category
- Maintain clear version information

### 2. **Storage Management**
- Monitor disk space regularly
- Clean up old cache files
- Archive unused models

### 3. **Access Control**
- Mount models as read-only in containers
- Use environment variables for paths
- Validate model paths before loading

### 4. **Backup Strategy**
- Regular backups of model storage
- Version control for model configurations
- Test recovery procedures

## Troubleshooting

### Common Issues

#### Model Not Found
```bash
# Check if model exists
ls -la /opt/ai-models/models/llama2/llama2-7b/

# Verify permissions
ls -la /opt/ai-models/
```

#### Permission Denied
```bash
# Fix permissions
chmod 755 /opt/ai-models
chown -R root:root /opt/ai-models

# Check container mounts
docker exec -it <container> ls -la /opt/ai-models
```

#### Storage Full
```bash
# Check disk usage
df -h /opt/ai-models

# Clean up cache
sudo ./scripts/manage-ai-models.sh cleanup

# Remove unused models
du -sh /opt/ai-models/models/*/
```

## Future Enhancements

### Planned Features
1. **Model Versioning**: Automatic version management
2. **Delta Updates**: Incremental model updates
3. **Compression**: Model compression for storage efficiency
4. **CDN Integration**: Distributed model distribution
5. **Model Registry**: Centralized model metadata management

### Scalability Considerations
- **Horizontal Scaling**: Multiple model storage locations
- **Load Balancing**: Distribute models across storage nodes
- **Caching Layers**: Redis-based model metadata caching
- **Monitoring**: Prometheus metrics for model usage

---

**This centralized approach ensures efficient model management, persistent availability, and optimal resource utilization across your AI inference infrastructure.**
