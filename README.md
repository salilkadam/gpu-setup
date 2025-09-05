# vLLM Blackwell GPU Setup

🚀 **Complete infrastructure for deploying vLLM on cutting-edge Blackwell GPUs with intelligent model routing and smart bypass optimization**

## 🎯 Project Overview

This project provides a complete solution for deploying vLLM (Very Large Language Model) inference server on cutting-edge Blackwell GPUs (RTX 5090, RTX PRO 6000) with Ubuntu 24.04. The setup includes intelligent model routing, smart bypass optimization for real-time conversations, performance optimization, and comprehensive testing.

## ✨ Key Features

- **✅ vLLM Deployment**: Successfully deployed on Blackwell GPUs
- **🧠 Intelligent Model Routing**: Smart model selection based on query type
- **🚀 Smart Bypass Optimization**: Ultra-low latency for real-time conversations
- **📊 Performance Optimization**: Optimized for cutting-edge hardware
- **🔧 Docker Integration**: Complete containerized setup
- **📈 Monitoring**: Prometheus + Grafana monitoring stack
- **🧪 Comprehensive Testing**: Full test suite for all use cases
- **🖼️ Multimodal Capabilities**: Image and video processing with MiniCPM-V-4
- **🌐 Internal DNS Routing**: Kubernetes cluster access to Docker AI services

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │───▶│  Smart Router   │───▶│  vLLM Server    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Session Cache  │    │  GPU Memory     │
                       │  (Redis)        │    │  (Pre-loaded)   │
                       └─────────────────┘    └─────────────────┘
```

## 🎮 Use Cases Supported

1. **🚀 Talking Head Avatars & Lip Sync**
2. **🗣️ Multilingual STT (Indian Languages)**
3. **🎵 Multilingual TTS (Indian Languages)**
4. **🤖 Content Generation & Executing Agents**
5. **📊 Multi-Modal Temporal Agentic RAG**
6. **🎬 Video-to-Text Understanding**

## 📦 Models Included

### **✅ Currently Deployed**
- **MiniCPM-V-4** (7GB) - Multimodal vision-language model with image/video capabilities
- **Whisper Large v3** - Speech-to-text for Indian languages
- **Coqui TTS** - Text-to-speech for Indian languages

### **🔧 Model Capabilities**
- **Image Processing**: Up to 448x448 pixels with batch processing
- **Video Understanding**: Frame analysis and temporal understanding
- **Multimodal Tasks**: Image+text and video+text analysis
- **Scene Understanding**: Object detection and scene description
- **Gemma-7B-IT** - Google's instruction-tuned model

## 🚀 Quick Start

### Prerequisites
- Ubuntu 24.04 LTS
- NVIDIA Blackwell GPUs (RTX 5090, RTX PRO 6000)
- Docker with GPU support
- CUDA 12.9+
- NVIDIA Driver 580.82.07+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/salilkadam/gpu-setup.git
   cd gpu-setup
   ```

2. **Start the services (Standard)**
   ```bash
   docker-compose up -d
   ```

3. **Start the services (Real-Time Optimized)**
   ```bash
   docker-compose -f docker-compose-realtime.yml up -d
   ```

4. **Test the API**
   ```bash
   curl -X POST http://localhost:8000/v1/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "/app/models/qwen2.5-7b-instruct", "prompt": "Hello, world!", "max_tokens": 50}'
   ```

## 📊 Performance Results

### **Model Performance**
| Model | Size | Load Time | Inference Speed | Quality |
|-------|------|-----------|-----------------|---------|
| Phi-2 | 5.2GB | 2.1s | Excellent | High |
| Qwen2.5-7B-Instruct | 15GB | 2.3s | Excellent | Superior |

### **Smart Bypass Optimization**
| Metric | Original System | Smart Bypass | Improvement |
|--------|----------------|--------------|-------------|
| **First Request** | 2.3-5.6s | 250-300ms | **90%+ faster** |
| **Ongoing Conversation** | 250-500ms | 200-250ms | **50% faster** |
| **Routing Overhead** | 50-100ms | 1-5ms | **95% reduction** |
| **Bypass Rate** | 0% | 80-95% | **Real-time ready** |

### **Space Optimization**
- **Before**: 155GB (25 models)
- **After**: 20.2GB (2 models)
- **Space Saved**: 135GB (87% reduction)

## 🧪 Testing

### **Run All Tests**
```bash
python3 scripts/test_vllm_compatible_models.py
```

### **Test Smart Bypass Optimization**
```bash
python3 scripts/test_smart_bypass.py
```

### **Test Specific Model**
```bash
python3 scripts/test_single_model.py --model qwen2.5-7b-instruct
```

## 📁 Project Structure

```
gpu-setup/
├── docs/                          # Documentation
│   └── feature/
│       └── vllm-blackwell-gpu-setup/
│           ├── implementation-plan.md
│           ├── implementation-tracker.md
│           ├── scratchpad.md
│           ├── model-compatibility-report.md
│           ├── vllm-compatible-models.md
│           ├── performance-comparable-models.md
│           ├── latency-analysis-and-optimization.md
│           └── smart-bypass-optimization.md
├── scripts/                       # Automation scripts
│   ├── build-vllm.sh
│   ├── download_all_use_case_models.py
│   ├── test_all_models_vllm.py
│   ├── test_vllm_compatible_models.py
│   └── test_smart_bypass.py
├── src/                           # Source code
│   ├── routing/                   # Routing components
│   │   ├── smart_bypass_router.py
│   │   └── realtime_router.py
│   └── api/                       # API components
│       └── realtime_routing_api.py
├── docker-compose.yml             # Standard deployment
├── docker-compose-realtime.yml    # Real-time optimized deployment
├── Dockerfile.vllm               # vLLM container
├── prometheus/                   # Monitoring config
├── grafana/                      # Dashboard config
└── README.md                     # This file
```

## 🔧 Configuration

### **Environment Variables**
```bash
# GPU Configuration
NVIDIA_VISIBLE_DEVICES=all
CUDA_DEVICE_ORDER=PCI_BUS_ID

# vLLM Configuration
VLLM_USE_TRITON_KERNEL=0
VLLM_GPU_MEMORY_UTILIZATION=0.9

# Smart Bypass Configuration
ROUTING_MODE=realtime
REDIS_URL=redis://localhost:6379
```

### **Model Configuration**
Models are stored in `/opt/ai-models/models/` and mounted into containers.

## 📈 Monitoring

Access monitoring dashboards:
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **vLLM API**: http://localhost:8000
- **Real-Time Routing API**: http://localhost:8001

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🖼️ vLLM Multimodal Capabilities

The vLLM endpoint supports advanced multimodal processing with the MiniCPM-V-4 model:

### Image Processing
- **Image Analysis**: Describe and analyze image content
- **Object Detection**: Identify objects in images
- **Scene Understanding**: Understand complex scenes and contexts
- **Format Support**: JPEG, PNG, and other common formats

### Video Understanding
- **Frame Analysis**: Process individual video frames
- **Temporal Analysis**: Understand video sequences over time
- **Action Recognition**: Identify actions and movements
- **Content Summarization**: Summarize video content

### API Usage Examples

#### Direct vLLM Endpoint
```bash
curl -X POST http://192.168.0.21:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/app/models/minicpm-v-4",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Describe what you see in this image"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,YOUR_IMAGE_BASE64"
            }
          }
        ]
      }
    ]
  }'
```

#### Through Routing API
```bash
curl -X POST http://192.168.0.21:8001/route \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this image and describe what you see",
    "use_case": "multimodal"
  }'
```

For detailed information, see [VLLM Multimodal Capabilities Documentation](docs/VLLM-MULTIMODAL-CAPABILITIES.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **vLLM Team** for the excellent inference server
- **NVIDIA** for Blackwell GPU support
- **Hugging Face** for model hosting
- **Qwen Team** for high-performance models

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the documentation in `docs/`
- Review the implementation tracker

---

**Status**: ✅ **Production Ready with Real-Time Optimization**  
**Last Updated**: December 19, 2024  
**Version**: 2.0.0
