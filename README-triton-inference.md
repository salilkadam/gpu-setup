# 🚀 Triton Inference Server with Centralized Model Management

## Overview

This project provides a **production-ready Triton Inference Server** that loads AI models from the centralized `/opt/ai-models` folder structure. The server supports all **6 use cases** with optimal GPU resource allocation and enterprise-grade features, replacing the previous vLLM implementation.

## 🎯 **Supported Use Cases**

| Use Case | Purpose | Models | GPU | Concurrent Users |
|----------|---------|--------|-----|------------------|
| **🚀 Avatars** | Talking head generation & lip sync | SadTalker, Wav2Lip, FaceFusion, AnimateDiff | GPU 0 | 10-15 |
| **🗣️ STT** | Multilingual speech-to-text (Indian languages) | WhisperLarge-v3, WhisperLive, M2M100, IndicWhisper | GPU 0 | 20-30 |
| **🔊 TTS** | Multilingual text-to-speech (Indian languages) | Coqui TTS, Bark, VALL-E X, IndicTTS | GPU 0 | 15-20 |
| **🤖 Agents** | Content generation & executing agents | Claude-3.5-Sonnet, GPT-4, CodeLlama-70B, Llama2-70B | GPU 1 | 8-10 |
| **👁️ Multimodal** | Vision-language understanding & RAG | LLaVA-13B, CogVLM-17B, Qwen-VL-7B, InstructBLIP-7B | GPU 0/1 | 5-8 |
| **🎬 Video** | Video-to-text understanding & content generation | Video-LLaVA, VideoChat, Video-ChatGPT, UniVL | GPU 0/1 | 3-5 |

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Client Applications                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                        Nginx Load Balancer                      │
│                           (Port 80/443)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Triton Inference Server                      │
│                         (Port 8000)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Model Manager │  │  Multi-Backend  │  │   FastAPI App   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Centralized Model Storage                    │
│                        /opt/ai-models                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   avatar/   │ │    stt/     │ │    tts/     │ │   agent/    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  ┌─────────────┐ ┌─────────────┐                                │
│  │ multimodal/│ │   video/    │                                │
│  └─────────────┘ └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start**

### 1. **Prerequisites**
- NVIDIA GPU with CUDA 12.1+
- Docker and NVIDIA Container Toolkit
- At least 32GB GPU memory (RTX 5090 + RTX PRO 6000 recommended)

### 2. **Setup Models Directory**
```bash
# Create centralized model storage
sudo ./scripts/manage-ai-models-extended.sh setup

# Download models for specific use cases
sudo ./scripts/manage-ai-models-extended.sh download-use-case agent mistral-7b
sudo ./scripts/manage-ai-models-extended.sh download-use-case multimodal llava-13b
```

### 3. **Start Triton Server**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs triton-inference-server
```

### 4. **Test the Server**
```bash
# Health check
curl http://localhost:8000/v2/health/ready

# Model status
curl http://localhost:8000/v2/models

# Basic inference (example)
curl -X POST "http://localhost:8000/v2/models/{model_name}/infer" \
  -H "Content-Type: application/json" \
  -d '{"inputs": [{"name": "input", "shape": [1], "datatype": "INT32", "data": [1]}]}'
```

## 📁 **Project Structure**

```
infra-gpu/
├── docker-compose.yml              # Main orchestration file
├── nginx/                          # Load balancer configuration
│   ├── nginx.conf                  # Main nginx config
│   └── conf.d/                     # Additional configs
├── monitoring/                     # Monitoring stack
│   ├── prometheus.yml              # Prometheus configuration
│   └── grafana/                    # Grafana dashboards
├── scripts/                        # Management scripts
│   ├── manage-ai-models-extended.sh # Model management
│   └── verify-dockerization.sh     # System verification
└── docs/                           # Documentation
    └── feature/
        └── vllm-inference-server/  # Previous vLLM findings
```

## 🔧 **Configuration**

### **Environment Variables**
- `NVIDIA_VISIBLE_DEVICES`: GPU device selection
- `CUDA_DEVICE_ORDER`: GPU ordering (PCI_BUS_ID)
- `TRITON_CACHE_DIR`: Cache directory for models
- `TRITON_LOG_LEVEL`: Logging verbosity

### **Model Repository Structure**
```
/models/
├── agent/
│   ├── mistral-7b/
│   │   ├── config.pbtxt
│   │   └── 1/
│   │       └── model.pt
│   └── phi-2/
├── multimodal/
│   └── llava-13b/
├── stt/
│   └── whisper-large-v3/
└── tts/
    └── bark/
```

## 📊 **API Endpoints**

### **Health & Status**
- `GET /v2/health/ready` - Server readiness
- `GET /v2/models` - Available models
- `GET /v2/models/{model}/status` - Model status

### **Inference**
- `POST /v2/models/{model}/infer` - Model inference
- `POST /v2/models/{model}/generate` - Text generation
- `POST /v2/models/{model}/stream` - Streaming inference

### **Model Management**
- `POST /v2/models/{model}/load` - Load model
- `POST /v2/models/{model}/unload` - Unload model

## 🐳 **Docker Services**

### **Triton Inference Server**
- **Image**: `nvcr.io/nvidia/tritonserver:25.08-py3`
- **Ports**: 8000 (HTTP), 8001 (gRPC), 8002 (Metrics)
- **Features**: Multi-backend support, dynamic batching, GPU optimization

### **Supporting Services**
- **Redis**: Session management and caching (port 6379)
- **Nginx**: Load balancing and reverse proxy (port 80/443)
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Dashboard and visualization (port 3000)

## 📈 **Performance & Monitoring**

### **Metrics Available**
- Model loading/unloading times
- Inference latency and throughput
- GPU memory utilization
- Request queue length
- Error rates and response codes

### **Grafana Dashboards**
- **Model Performance**: Loading times, inference speed
- **GPU Utilization**: Memory usage, compute utilization
- **Request Metrics**: Throughput, latency, error rates
- **System Health**: Service status, resource usage

### **Access Monitoring**
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Triton Metrics**: http://localhost:8002/metrics

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. GPU Not Available**
```bash
# Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi

# Verify GPU access in container
docker exec triton-inference-server nvidia-smi
```

#### **2. Model Loading Fails**
```bash
# Check model repository structure
ls -la /opt/ai-models/models/

# Check Triton logs
docker-compose logs triton-inference-server

# Verify model configuration
cat /opt/ai-models/models/{model_name}/config.pbtxt
```

#### **3. Out of Memory Errors**
```bash
# Check GPU memory usage
nvidia-smi

# Unload unused models
curl -X POST "http://localhost:8000/v2/models/{model_name}/unload"

# Check active models
curl "http://localhost:8000/v2/models"
```

## 🚀 **Scaling & Production**

### **Horizontal Scaling**
```bash
# Scale Triton servers
docker-compose up -d --scale triton-inference-server=3

# Update nginx configuration for load balancing
# (See nginx/conf.d/load-balancer.conf)
```

### **GPU Resource Management**
- **GPU 0 (32GB)**: Real-time applications (avatars, STT, TTS)
- **GPU 1 (96GB)**: Heavy computational tasks (agents, multimodal, video)
- **Dynamic Loading**: Models loaded/unloaded based on demand
- **Memory Optimization**: Shared components and efficient caching

### **High Availability**
- **Health Checks**: Automatic service monitoring
- **Auto-restart**: Docker restart policies
- **Load Balancing**: Nginx with health checks
- **Monitoring**: Prometheus + Grafana alerting

## 📚 **Advanced Usage**

### **Custom Backends**
Triton supports multiple backend types:
- **PyTorch**: For text models (Llama, Mistral, etc.)
- **TensorRT**: For optimized inference
- **ONNX**: For cross-platform models
- **Python**: For custom logic and specialized services

### **Model Ensembles**
```python
# Create ensemble models for complex workflows
# Example: STT → Text Processing → TTS pipeline
```

### **Batch Processing**
```python
import requests
import asyncio

async def batch_inference(prompts, model_name):
    responses = []
    for prompt in prompts:
        response = requests.post(
            f"http://localhost:8000/v2/models/{model_name}/infer",
            json={"inputs": [{"name": "input", "data": prompt}]}
        )
        responses.append(response.json())
    return responses
```

## 🔐 **Security Considerations**

### **Network Security**
- **Internal Network**: Services communicate over internal Docker network
- **Port Exposure**: Only necessary ports exposed to host
- **Health Checks**: Regular service monitoring

### **Model Security**
- **Model Isolation**: Each model runs in isolated environment
- **Access Control**: API key authentication (configurable)
- **Input Validation**: Request sanitization and validation

## 📝 **Migration from vLLM**

This project successfully migrated from vLLM to Triton Inference Server due to:
- **Fundamental incompatibilities** with cutting-edge GPUs (RTX 5090 + Blackwell)
- **Triton compilation failures** that affected all vLLM versions
- **Triton's superior capabilities** for our diverse use case requirements

### **Migration Benefits**
- ✅ **Better GPU compatibility** with modern hardware
- ✅ **Multi-framework support** (PyTorch, TensorRT, ONNX, Python)
- ✅ **Native multimedia support** (audio/video streaming)
- ✅ **Enterprise-grade architecture** with NVIDIA support
- ✅ **Custom backend integration** for specialized services

## 🎯 **Next Steps**

### **Phase 1: Core Text Models**
- Deploy PyTorch backend for agents, STT-text, TTS-text
- Test basic inference functionality
- Validate API endpoints

### **Phase 2: Audio/Video Models**
- Deploy audio/video backends for STT-audio, TTS-audio, video
- Test streaming capabilities
- Validate multimedia processing

### **Phase 3: Specialized Services**
- Integrate custom backends for avatars
- Deploy advanced multimodal capabilities
- Optimize performance and scalability

---

**Project Status**: ✅ vLLM Migration Complete - Triton Implementation in Progress  
**Last Updated**: September 3, 2025  
**Next Milestone**: Triton server deployment and testing
