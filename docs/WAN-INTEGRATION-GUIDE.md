# Wan Video Generation Integration Guide

This guide covers the complete integration of Wan video generation models into the GPU setup infrastructure, providing concurrent user access through Docker containers.

## Overview

The Wan integration adds powerful video generation capabilities to your existing AI infrastructure:

- **Text-to-Video (T2V)**: Generate videos from text descriptions
- **Image-to-Video (I2V)**: Animate static images with text prompts
- **Speech-to-Video (S2V)**: Create talking head videos from audio and reference images
- **Animation**: Generate character animations from pose data
- **Text-Image-to-Video (TI2V)**: Combine text and images for video generation

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Routing API    │    │  Wan Service    │
│                 │───▶│                 │───▶│                 │
│ - Web UI        │    │ - Query         │    │ - T2V Models    │
│ - Mobile Apps   │    │   Classification│    │ - I2V Models    │
│ - API Clients   │    │ - Model         │    │ - S2V Models    │
└─────────────────┘    │   Routing       │    │ - Animation     │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Other Services │    │  Model Storage  │
                       │                 │    │                 │
                       │ - vLLM          │    │ - /opt/ai-models│
                       │ - STT/TTS       │    │ - Wan Models    │
                       │ - Multimodal    │    │ - Checkpoints   │
                       └─────────────────┘    └─────────────────┘
```

## Services

### Wan Service (Port 8004)
- **Container**: `ai-wan-service`
- **API**: FastAPI-based video generation service
- **Models**: All Wan model variants (T2V, I2V, S2V, Animation)
- **GPU**: Full GPU access for video generation
- **Storage**: Persistent volumes for cache, logs, and output

### Routing Integration
- **Query Classification**: Automatically detects video generation requests
- **Model Selection**: Routes to appropriate Wan models based on request type
- **Load Balancing**: Handles concurrent requests efficiently
- **Fallback**: Graceful degradation when models are unavailable

## Model Configuration

### Available Models

| Model | Type | Size | Memory | Capabilities |
|-------|------|------|--------|--------------|
| `t2v-A14B` | Text-to-Video | 28GB | 28GB | High-quality T2V generation |
| `i2v-A14B` | Image-to-Video | 28GB | 28GB | Image animation |
| `ti2v-5B` | Text-Image-to-Video | 10GB | 10GB | Fast T2V/I2V generation |
| `s2v-14B` | Speech-to-Video | 28GB | 28GB | Talking head generation |
| `animate-14B` | Animation | 28GB | 28GB | Character animation |

### Model Storage Structure
```
/opt/ai-models/
└── wan/
    ├── t2v-A14B/
    │   ├── model files
    │   └── config files
    ├── i2v-A14B/
    ├── ti2v-5B/
    ├── s2v-14B/
    └── animate-14B/
```

## API Endpoints

### Wan Service Endpoints

#### Health Check
```http
GET /health
```

#### List Models
```http
GET /models
```

#### Text-to-Video Generation
```http
POST /generate/text-to-video
Content-Type: application/json

{
  "task": "t2v-A14B",
  "prompt": "A beautiful sunset over a calm ocean",
  "size": "1280*720",
  "frame_num": 17,
  "sample_steps": 20,
  "sample_guide_scale": 7.5,
  "base_seed": 42
}
```

#### Image-to-Video Generation
```http
POST /generate/image-to-video
Content-Type: application/json

{
  "task": "i2v-A14B",
  "prompt": "The image comes to life with gentle movement",
  "image_path": "/path/to/image.jpg",
  "size": "1280*720",
  "frame_num": 17,
  "sample_steps": 20,
  "sample_guide_scale": 7.5,
  "base_seed": 42
}
```

#### Speech-to-Video Generation
```http
POST /generate/speech-to-video
Content-Type: application/json

{
  "task": "s2v-14B",
  "prompt": "A person speaking naturally",
  "image_path": "/path/to/reference.jpg",
  "enable_tts": true,
  "tts_prompt_text": "Hello, this is a test.",
  "tts_text": "This is the text to synthesize",
  "size": "1280*720",
  "frame_num": 17,
  "sample_steps": 20,
  "sample_guide_scale": 7.5,
  "base_seed": 42
}
```

#### Animation Generation
```http
POST /generate/animation
Content-Type: application/json

{
  "task": "animate-14B",
  "prompt": "A character performing a simple animation",
  "src_root_path": "/path/to/animation/data",
  "replace_flag": false,
  "refert_num": 77,
  "frame_num": 17,
  "sample_steps": 20,
  "sample_guide_scale": 7.5,
  "base_seed": 42
}
```

#### Video Management
```http
# List videos
GET /videos

# Download video
GET /videos/{filename}

# Delete video
DELETE /videos/{filename}
```

### Routing API Integration

The routing system automatically detects video generation requests and routes them to appropriate Wan models:

```http
POST /api/v1/route
Content-Type: application/json

{
  "query": "Generate a video of a cat playing in the garden",
  "modality": "text",
  "context": {
    "prefer_quality": true,
    "max_duration": 10
  }
}
```

## Setup Instructions

### 1. Download Models

```bash
# Download all Wan models
python scripts/download_wan_models.py --all

# Download specific model
python scripts/download_wan_models.py --model t2v-A14B

# List available models
python scripts/download_wan_models.py --list

# Check installed models
python scripts/download_wan_models.py --installed
```

### 2. Start Services

```bash
# Start all services including Wan
docker-compose up -d

# Start only Wan service
docker-compose up -d wan-service

# Check service status
docker-compose ps
```

### 3. Verify Installation

```bash
# Test Wan service
python scripts/test_wan_service.py --test health

# Run comprehensive tests
python scripts/test_wan_service.py --test all

# Test specific functionality
python scripts/test_wan_service.py --test t2v --model t2v-A14B
```

## Usage Examples

### Python Client

```python
import requests
import json

# Wan service URL
wan_url = "http://localhost:8004"

# Generate text-to-video
def generate_video(prompt, model="t2v-A14B"):
    payload = {
        "task": model,
        "prompt": prompt,
        "size": "1280*720",
        "frame_num": 17,
        "sample_steps": 20,
        "sample_guide_scale": 7.5,
        "base_seed": 42
    }
    
    response = requests.post(
        f"{wan_url}/generate/text-to-video",
        json=payload,
        timeout=300
    )
    
    return response.json()

# Generate video
result = generate_video("A beautiful sunset over a calm ocean")
print(f"Video generated: {result['video_path']}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:8004/health

# List models
curl http://localhost:8004/models

# Generate text-to-video
curl -X POST http://localhost:8004/generate/text-to-video \
  -H "Content-Type: application/json" \
  -d '{
    "task": "t2v-A14B",
    "prompt": "A cat playing in a garden",
    "size": "1280*720",
    "frame_num": 17,
    "sample_steps": 20,
    "sample_guide_scale": 7.5,
    "base_seed": 42
  }'

# List generated videos
curl http://localhost:8004/videos
```

## Configuration

### Environment Variables

```bash
# Wan Service Configuration
MODELS_DIR=/opt/ai-models          # Model storage directory
CUDA_VISIBLE_DEVICES=all           # GPU access
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True  # Memory optimization
```

### Docker Compose Configuration

```yaml
wan-service:
  build:
    context: .
    dockerfile: docker/Dockerfile.wan
  container_name: ai-wan-service
  restart: unless-stopped
  ports:
    - "8004:8004"
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
    - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    - MODELS_DIR=/opt/ai-models
  volumes:
    - /opt/ai-models:/opt/ai-models:ro
    - wan_cache:/app/cache
    - wan_logs:/app/logs
    - wan_output:/app/output
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

## Performance Optimization

### GPU Memory Management
- Models use GPU memory efficiently with offloading
- Automatic memory cleanup after generation
- Support for multiple concurrent requests (limited by GPU memory)

### Caching Strategy
- Model loading is cached for faster subsequent requests
- Generated videos are stored for reuse
- Temporary files are cleaned up automatically

### Concurrent Access
- Multiple users can generate videos simultaneously
- Request queuing for resource management
- Load balancing across available models

## Monitoring and Logging

### Health Monitoring
```bash
# Check service health
curl http://localhost:8004/health

# Monitor logs
docker-compose logs -f wan-service

# Check resource usage
docker stats ai-wan-service
```

### Log Files
- Service logs: `/app/logs/` (mounted to `wan_logs` volume)
- Generation logs: Detailed logging of each video generation
- Error logs: Comprehensive error tracking and debugging

## Troubleshooting

### Common Issues

#### Model Not Found
```bash
# Check if models are downloaded
python scripts/download_wan_models.py --installed

# Download missing models
python scripts/download_wan_models.py --model t2v-A14B
```

#### GPU Memory Issues
```bash
# Check GPU memory
nvidia-smi

# Restart service to free memory
docker-compose restart wan-service
```

#### Service Not Responding
```bash
# Check service status
docker-compose ps wan-service

# Check logs
docker-compose logs wan-service

# Restart service
docker-compose restart wan-service
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up wan-service
```

## Security Considerations

### Access Control
- Service runs in isolated Docker container
- No direct file system access from outside
- API endpoints are protected by routing layer

### Resource Limits
- GPU memory limits prevent resource exhaustion
- Request timeouts prevent hanging processes
- Automatic cleanup of temporary files

### Data Privacy
- Generated videos are stored temporarily
- Automatic cleanup of sensitive data
- No persistent storage of user inputs

## Scaling and Production

### Horizontal Scaling
- Multiple Wan service instances can be deployed
- Load balancing through routing API
- Shared model storage for consistency

### Production Deployment
- Use production-grade Docker images
- Implement proper monitoring and alerting
- Set up automated backups of generated content
- Configure proper resource limits and quotas

## Integration with Existing Services

### Routing API Integration
The Wan service integrates seamlessly with the existing routing system:

1. **Query Classification**: Automatically detects video generation requests
2. **Model Selection**: Routes to appropriate Wan models
3. **Load Balancing**: Distributes requests efficiently
4. **Fallback Handling**: Graceful degradation when models are unavailable

### vLLM Integration
- Wan models can be used alongside vLLM models
- Shared GPU resources with intelligent allocation
- Unified API interface for all AI services

### STT/TTS Integration
- Speech-to-video models can use existing STT/TTS services
- Audio processing pipeline integration
- Voice cloning and synthesis capabilities

## Future Enhancements

### Planned Features
- Real-time video generation streaming
- Batch processing for multiple videos
- Advanced animation controls
- Custom model fine-tuning
- WebSocket support for real-time updates

### Model Updates
- Regular model updates and improvements
- New model variants and capabilities
- Performance optimizations
- Memory usage improvements

## Support and Maintenance

### Regular Maintenance
- Model updates and security patches
- Performance monitoring and optimization
- Log rotation and cleanup
- Resource usage monitoring

### Backup and Recovery
- Model checkpoint backups
- Generated content archiving
- Configuration backup
- Disaster recovery procedures

For additional support or questions, refer to the main documentation or contact the development team.
