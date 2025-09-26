# AI Infrastructure - Complete Setup

## 🎯 **Overview**

This repository contains a complete AI infrastructure setup with:
- **Docker containers** running AI services (vLLM, STT, TTS, Routing API)
- **Kubernetes cluster** integration for orchestration
- **External access** via `api.askcollections.com` with HTTPS support
- **Cloudflare integration** for production deployment
- **Monitoring** with Prometheus and Grafana

## 🚀 **Quick Start**

### **For Fresh Installation**
```bash
# Clone and setup from scratch
git clone <repository-url>
cd gpu-setup
./scripts/setup-ai-infrastructure.sh
```

### **For Current Setup**
```bash
# Test current setup
./scripts/test-current-setup.sh

# Deploy Kubernetes resources
cd k8s && ./deploy.sh
```

## 📚 **Documentation**

### **Complete Guides**
- **[Complete Setup Guide](docs/COMPLETE-SETUP-GUIDE.md)** - Step-by-step setup from scratch
- **[Quick Reference](docs/QUICK-REFERENCE.md)** - Current setup management and troubleshooting

### **API Documentation**
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[App Integration Guide](docs/app-integration-guide.md)** - Integration examples

## 🌐 **Live API Endpoints**

Your AI services are accessible at:

| Service | Endpoint | Description |
|---------|----------|-------------|
| **Main API** | `https://api.askcollections.com/api/` | AI routing and chat |
| **Health Check** | `https://api.askcollections.com/health` | System health status |
| **STT Service** | `https://api.askcollections.com/stt/health` | Speech-to-Text |
| **TTS Service** | `https://api.askcollections.com/tts/health` | Text-to-Speech |
| **vLLM Direct** | `https://api.askcollections.com/vllm/v1/models` | Direct model access |

### **Example Usage**
```bash
# AI Chat Request
curl -X POST https://api.askcollections.com/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, how are you?", "max_tokens": 100}'

# Health Check
curl https://api.askcollections.com/health
```

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cloudflare    │────│  nginx Ingress   │────│  Kubernetes     │
│   (HTTPS)       │    │  (SSL/TLS)       │    │  Services       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │  Docker         │
                                               │  Containers     │
                                               │  (AI Services)  │
                                               └─────────────────┘
```

### **Components**
- **Frontend**: Cloudflare CDN with HTTPS termination
- **Ingress**: nginx Ingress Controller with SSL certificates
- **Orchestration**: Kubernetes cluster (K3s)
- **Services**: Docker containers with AI models
- **Monitoring**: Prometheus + Grafana

## 🔧 **Management**

### **Service Management**
```bash
# Docker services
docker compose ps                    # Check status
docker compose logs -f routing-api   # View logs
docker compose restart routing-api   # Restart service

# Kubernetes services
kubectl get all -n ai-infrastructure # Check status
kubectl logs -f deployment/ai-routing-api -n ai-infrastructure # View logs
```

### **Monitoring**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **GPU Usage**: `nvidia-smi`
- **System Resources**: `htop`

## 🛠️ **Scripts**

| Script | Purpose |
|--------|---------|
| `scripts/setup-ai-infrastructure.sh` | Complete setup from scratch |
| `scripts/test-current-setup.sh` | Test all components |
| `scripts/cleanup-and-organize.sh` | Clean up redundant files |
| `k8s/deploy.sh` | Deploy Kubernetes resources |

## 📁 **Project Structure**

```
gpu-setup/
├── README.md                        # This file
├── docker-compose.yml               # Docker services
├── Dockerfile.routing               # Routing API container
├── requirements-routing.txt         # Python dependencies
├── k8s/                            # Kubernetes configurations
│   ├── namespace.yaml              # Namespace
│   ├── services.yaml               # Services
│   ├── endpoints.yaml              # Endpoints
│   ├── nginx-external-ingress.yaml # External ingress
│   ├── letsencrypt-issuer.yaml    # SSL certificates
│   └── deploy.sh                   # Deployment script
├── scripts/                        # Management scripts
│   ├── setup-ai-infrastructure.sh  # Complete setup
│   ├── test-current-setup.sh       # Testing
│   └── cleanup-and-organize.sh     # Cleanup
├── docs/                           # Documentation
│   ├── COMPLETE-SETUP-GUIDE.md     # Setup guide
│   ├── QUICK-REFERENCE.md          # Quick reference
│   └── api-reference.md            # API docs
└── src/                            # Source code
    ├── api/                        # API implementation
    ├── routing/                    # Routing logic
    └── config/                     # Configuration
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Services Not Responding**
```bash
# Check Docker services
docker compose ps
docker compose logs

# Check Kubernetes services
kubectl get pods -n ai-infrastructure
kubectl get endpoints -n ai-infrastructure
```

#### **External Access Issues**
```bash
# Check ingress status
kubectl describe ingress ai-external-ingress -n ai-infrastructure

# Check DNS resolution
nslookup api.askcollections.com

# Test direct access
curl -H "Host: api.askcollections.com" http://192.168.0.20/api/health
```

#### **SSL Certificate Issues**
```bash
# Check certificate status
kubectl get certificates -n ai-infrastructure
kubectl describe certificate api-askcollections-com-tls -n ai-infrastructure

# Check cert-manager
kubectl get pods -n cert-manager
```

### **Emergency Recovery**
```bash
# Restart all services
docker compose down && docker compose up -d
kubectl rollout restart deployment -n ai-infrastructure

# Complete rebuild
docker compose build --no-cache
docker compose up -d
kubectl apply -f k8s/
```

## 📊 **Status**

| Component | Status | Health |
|-----------|--------|--------|
| **Docker Services** | ✅ Running | 9/9 containers healthy |
| **Kubernetes** | ✅ Active | All services running |
| **External Access** | ✅ Working | HTTPS via Cloudflare |
| **SSL Certificates** | ✅ Valid | Let's Encrypt managed |
| **AI Models** | ✅ Loaded | MiniCPM-V-4, Whisper |
| **Monitoring** | ✅ Active | Prometheus + Grafana |

## 🔄 **Updates**

### **Update Services**
```bash
# Update Docker services
docker compose pull
docker compose up -d

# Update Kubernetes
kubectl apply -f k8s/
```

### **Backup and Recovery**
```bash
# Backup
kubectl get all -n ai-infrastructure -o yaml > backup.yaml
sudo tar -czf models-backup.tar.gz /opt/ai-models/

# Restore
kubectl apply -f backup.yaml
sudo tar -xzf models-backup.tar.gz -C /
```

## 📞 **Support**

### **Resources**
- **Documentation**: [docs/](docs/)
- **API Reference**: [docs/api-reference.md](docs/api-reference.md)
- **Quick Reference**: [docs/QUICK-REFERENCE.md](docs/QUICK-REFERENCE.md)

### **Monitoring**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Service Health**: `./scripts/test-current-setup.sh`

---

**Status**: ✅ **Production Ready**  
**Last Updated**: January 2025  
**Version**: 2.0.0

This infrastructure provides a complete, production-ready AI service platform with external access, monitoring, and automated management.