# Complete AI Infrastructure Setup Guide

## 🎯 **Overview**

This guide provides step-by-step instructions to set up a complete AI infrastructure with:
- Docker containers running AI services (vLLM, STT, TTS, Routing API)
- Kubernetes cluster integration
- External access via `api.askcollections.com` with HTTPS support
- Cloudflare integration for production deployment

## 📋 **Prerequisites**

### **System Requirements**
- Ubuntu 22.04+ or similar Linux distribution
- NVIDIA GPU with CUDA support
- Docker and Docker Compose
- Kubernetes cluster (K3s recommended)
- kubectl configured
- Domain name with DNS control
- Cloudflare account (for production)

### **Hardware Requirements**
- GPU: NVIDIA RTX 4090 or better (24GB+ VRAM recommended)
- RAM: 64GB+ system memory
- Storage: 500GB+ SSD for models and data
- Network: Stable internet connection

## 🚀 **Step 1: Initial System Setup**

### **1.1 Install Docker and Docker Compose**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

### **1.2 Install Kubernetes (K3s)**

```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Configure kubectl
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify installation
kubectl cluster-info
```

### **1.3 Install Ingress Controllers**

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Install Kong Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/Kong/kubernetes-ingress-controller/main/deploy/single/all-in-one-dbless.yaml

# Install cert-manager for SSL certificates
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for controllers to be ready
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s
kubectl wait --namespace kong --for=condition=ready pod --selector=app.kubernetes.io/name=ingress-controller --timeout=300s
kubectl wait --namespace cert-manager --for=condition=ready pod --selector=app.kubernetes.io/name=cert-manager --timeout=300s
```

## 🐳 **Step 2: Docker Services Setup**

### **2.1 Create Project Structure**

```bash
# Create project directory
mkdir -p /home/$USER/gpu-setup
cd /home/$USER/gpu-setup

# Create required directories
mkdir -p {docker,k8s,nginx,prometheus,grafana,logs,scripts,src/{api,audio,routing,config},tests/{unit,integration}}

# Create model storage directory
sudo mkdir -p /opt/ai-models/models
sudo chown $USER:$USER /opt/ai-models/models
```

### **2.2 Create Docker Compose Configuration**

Create `/home/$USER/gpu-setup/docker-compose.yml`:

```yaml
services:
  # vLLM Inference Server
  vllm-inference-server:
    image: vllm/vllm-openai:latest
    container_name: vllm-inference-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - CUDA_DEVICE_ORDER=PCI_BUS_ID
      - VLLM_USE_TRITON_KERNEL=0
    volumes:
      - /opt/ai-models/models:/app/models:ro
      - vllm_cache:/app/cache
      - vllm_logs:/app/logs
    command: ["--host", "0.0.0.0", "--port", "8000", "--model", "/app/models/multimodal/minicpm-v-4", "--trust-remote-code"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # AI Routing API
  routing-api:
    build:
      context: .
      dockerfile: Dockerfile.routing
    container_name: ai-routing-api
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      - PYTHONPATH=/app
      - VLLM_URL=http://vllm-inference-server:8000
      - REDIS_URL=redis://ai-redis:6379
    volumes:
      - ./src:/app/src:ro
      - ./logs:/app/logs
    depends_on:
      - vllm-inference-server
      - ai-redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Speech-to-Text Service
  stt-service:
    build:
      context: .
      dockerfile: docker/Dockerfile.audio
    container_name: ai-stt-service
    restart: unless-stopped
    ports:
      - "8002:8002"
    environment:
      - SERVICE_TYPE=stt
      - MODEL_NAME=whisper-large-v3
    volumes:
      - /opt/ai-models/models:/app/models:ro
    depends_on:
      - vllm-inference-server
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Text-to-Speech Service
  tts-service:
    build:
      context: .
      dockerfile: docker/Dockerfile.audio
    container_name: ai-tts-service
    restart: unless-stopped
    ports:
      - "8003:8003"
    environment:
      - SERVICE_TYPE=tts
    volumes:
      - /opt/ai-models/models:/app/models:ro
    depends_on:
      - vllm-inference-server
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  ai-redis:
    image: redis:7-alpine
    container_name: ai-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Prometheus Monitoring
  ai-prometheus:
    image: prom/prometheus:latest
    container_name: ai-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'

  # Grafana Dashboard
  ai-grafana:
    image: grafana/grafana:latest
    container_name: ai-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro

volumes:
  vllm_cache:
  vllm_logs:
  redis_data:
  prometheus_data:
  grafana_data:
```

### **2.3 Create Dockerfile for Routing API**

Create `/home/$USER/gpu-setup/Dockerfile.routing`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-routing.txt .
RUN pip install --no-cache-dir -r requirements-routing.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY docs/ ./docs/

# Create necessary directories
RUN mkdir -p /app/logs /app/cache

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "src.api.realtime_routing_api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### **2.4 Create Requirements File**

Create `/home/$USER/gpu-setup/requirements-routing.txt`:

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
aiohttp>=3.9.0
asyncio-mqtt>=0.16.0
torch>=2.1.0
transformers>=4.35.0
accelerate>=0.24.0
sentencepiece>=0.1.99
protobuf>=4.25.0
numpy>=1.24.0
pandas>=2.0.0
pyyaml>=6.0.1
psutil>=5.9.0
prometheus-client>=0.19.0
structlog>=23.2.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.25.0
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.7.0
redis>=5.0.0
celery>=5.3.0
```

### **2.5 Download AI Models**

Create `/home/$USER/gpu-setup/scripts/download_models.py`:

```python
#!/usr/bin/env python3
"""
Download essential AI models for the infrastructure
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ Success: {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {cmd}")
        print(f"Error output: {e.stderr}")
        return False

def download_minicpm_v4():
    """Download MiniCPM-V-4 model"""
    model_path = "/opt/ai-models/models/multimodal"
    os.makedirs(model_path, exist_ok=True)
    
    cmd = f"""
    cd {model_path} && \
    git lfs install && \
    git clone https://huggingface.co/openbmb/MiniCPM-V-4 minicpm-v-4
    """
    
    return run_command(cmd)

def download_whisper():
    """Download Whisper model"""
    model_path = "/opt/ai-models/models/audio"
    os.makedirs(model_path, exist_ok=True)
    
    cmd = f"""
    cd {model_path} && \
    git lfs install && \
    git clone https://huggingface.co/openai/whisper-large-v3 whisper-large-v3
    """
    
    return run_command(cmd)

def main():
    """Main download function"""
    print("🚀 Starting AI model downloads...")
    
    # Check if running as root or with sudo
    if os.geteuid() != 0:
        print("❌ This script needs to be run with sudo for model downloads")
        sys.exit(1)
    
    # Download models
    success = True
    success &= download_minicpm_v4()
    success &= download_whisper()
    
    if success:
        print("✅ All models downloaded successfully!")
    else:
        print("❌ Some models failed to download")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Make it executable and run:

```bash
chmod +x /home/$USER/gpu-setup/scripts/download_models.py
sudo /home/$USER/gpu-setup/scripts/download_models.py
```

### **2.6 Start Docker Services**

```bash
cd /home/$USER/gpu-setup
docker compose up -d
```

Verify services are running:

```bash
docker compose ps
```

## ☸️ **Step 3: Kubernetes Integration**

### **3.1 Create Kubernetes Namespace**

Create `/home/$USER/gpu-setup/k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-infrastructure
  labels:
    name: ai-infrastructure
    purpose: ai-services
```

### **3.2 Create Kubernetes Services**

Create `/home/$USER/gpu-setup/k8s/services.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-routing-api
  namespace: ai-infrastructure
  labels:
    app: ai-routing-api
spec:
  type: ClusterIP
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
    name: http
  selector:
    app: ai-routing-api

---
apiVersion: v1
kind: Service
metadata:
  name: ai-stt-service
  namespace: ai-infrastructure
  labels:
    app: ai-stt-service
spec:
  type: ClusterIP
  ports:
  - port: 8002
    targetPort: 8002
    protocol: TCP
    name: http
  selector:
    app: ai-stt-service

---
apiVersion: v1
kind: Service
metadata:
  name: ai-tts-service
  namespace: ai-infrastructure
  labels:
    app: ai-tts-service
spec:
  type: ClusterIP
  ports:
  - port: 8003
    targetPort: 8003
    protocol: TCP
    name: http
  selector:
    app: ai-tts-service

---
apiVersion: v1
kind: Service
metadata:
  name: ai-vllm-service
  namespace: ai-infrastructure
  labels:
    app: ai-vllm-service
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: ai-vllm-service

---
apiVersion: v1
kind: Service
metadata:
  name: ai-redis
  namespace: ai-infrastructure
  labels:
    app: ai-redis
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
    name: redis
  selector:
    app: ai-redis
```

### **3.3 Create Kubernetes Endpoints**

Create `/home/$USER/gpu-setup/k8s/endpoints.yaml`:

```yaml
apiVersion: v1
kind: Endpoints
metadata:
  name: ai-routing-api
  namespace: ai-infrastructure
subsets:
- addresses:
  - ip: 192.168.0.20  # Replace with your host IP
  ports:
  - port: 8001
    name: http

---
apiVersion: v1
kind: Endpoints
metadata:
  name: ai-stt-service
  namespace: ai-infrastructure
subsets:
- addresses:
  - ip: 192.168.0.20  # Replace with your host IP
  ports:
  - port: 8002
    name: http

---
apiVersion: v1
kind: Endpoints
metadata:
  name: ai-tts-service
  namespace: ai-infrastructure
subsets:
- addresses:
  - ip: 192.168.0.20  # Replace with your host IP
  ports:
  - port: 8003
    name: http

---
apiVersion: v1
kind: Endpoints
metadata:
  name: ai-vllm-service
  namespace: ai-infrastructure
subsets:
- addresses:
  - ip: 192.168.0.20  # Replace with your host IP
  ports:
  - port: 8000
    name: http

---
apiVersion: v1
kind: Endpoints
metadata:
  name: ai-redis
  namespace: ai-infrastructure
subsets:
- addresses:
  - ip: 192.168.0.20  # Replace with your host IP
  ports:
  - port: 6379
    name: redis
```

### **3.4 Deploy Kubernetes Resources**

```bash
cd /home/$USER/gpu-setup
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/endpoints.yaml
```

Verify deployment:

```bash
kubectl get all -n ai-infrastructure
kubectl get endpoints -n ai-infrastructure
```

## 🌐 **Step 4: External Access Setup**

### **4.1 Create nginx Ingress for External Access**

Create `/home/$USER/gpu-setup/k8s/nginx-external-ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-external-ingress
  namespace: ai-infrastructure
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    nginx.ingress.kubernetes.io/cors-allow-headers: "Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Auth-Token, Authorization, X-Requested-With, X-Session-ID, X-User-ID"
    nginx.ingress.kubernetes.io/cors-allow-credentials: "true"
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.askcollections.com
    secretName: api-askcollections-com-tls
  rules:
  - host: api.askcollections.com
    http:
      paths:
      # Main AI Routing API
      - path: /api(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-routing-api
            port:
              number: 8001
      # Speech-to-Text Service
      - path: /stt(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-stt-service
            port:
              number: 8002
      # Text-to-Speech Service
      - path: /tts(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-tts-service
            port:
              number: 8003
      # Direct vLLM Service
      - path: /vllm(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-vllm-service
            port:
              number: 8000
      # Health check endpoint
      - path: /health(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-routing-api
            port:
              number: 8001
```

### **4.2 Create Let's Encrypt ClusterIssuer**

Create `/home/$USER/gpu-setup/k8s/letsencrypt-issuer.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### **4.3 Deploy External Access Configuration**

```bash
cd /home/$USER/gpu-setup
kubectl apply -f k8s/letsencrypt-issuer.yaml
kubectl apply -f k8s/nginx-external-ingress.yaml
```

### **4.4 Configure DNS**

1. **Get nginx Ingress External IPs:**
```bash
kubectl get svc -n ingress-nginx
```

2. **Configure DNS Records:**
   - Point `api.askcollections.com` to the nginx ingress external IPs
   - Enable Cloudflare proxy (orange cloud) for HTTPS termination

3. **Verify DNS Resolution:**
```bash
nslookup api.askcollections.com
```

## 🧪 **Step 5: Testing and Verification**

### **5.1 Test Docker Services**

```bash
# Test vLLM service
curl http://localhost:8000/health

# Test routing API
curl http://localhost:8001/health

# Test STT service
curl http://localhost:8002/health

# Test TTS service
curl http://localhost:8003/health
```

### **5.2 Test Kubernetes Integration**

```bash
# Test from within cluster
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-routing-api.ai-infrastructure.svc.cluster.local:8001/health

# Test STT service
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-stt-service.ai-infrastructure.svc.cluster.local:8002/health
```

### **5.3 Test External Access**

```bash
# Test HTTP (should redirect to HTTPS)
curl -H "Host: api.askcollections.com" http://api.askcollections.com/api/

# Test HTTPS
curl -H "Host: api.askcollections.com" https://api.askcollections.com/api/ -k

# Test AI routing
curl -H "Host: api.askcollections.com" -H "Content-Type: application/json" -X POST https://api.askcollections.com/api/route -k -d '{"query": "Hello, how are you?", "max_tokens": 50}'

# Test STT service
curl -H "Host: api.askcollections.com" https://api.askcollections.com/stt/health -k

# Test TTS service
curl -H "Host: api.askcollections.com" https://api.askcollections.com/tts/health -k

# Test vLLM service
curl -H "Host: api.askcollections.com" https://api.askcollections.com/vllm/v1/models -k
```

## 🔧 **Step 6: Monitoring and Maintenance**

### **6.1 Check Service Status**

```bash
# Docker services
docker compose ps

# Kubernetes services
kubectl get all -n ai-infrastructure

# Ingress status
kubectl get ingress -n ai-infrastructure

# Certificate status
kubectl get certificates -n ai-infrastructure
```

### **6.2 View Logs**

```bash
# Docker logs
docker compose logs -f routing-api
docker compose logs -f vllm-inference-server

# Kubernetes logs
kubectl logs -f deployment/ai-routing-api -n ai-infrastructure
```

### **6.3 Monitor Resources**

```bash
# GPU usage
nvidia-smi

# System resources
htop

# Kubernetes resources
kubectl top nodes
kubectl top pods -n ai-infrastructure
```

## 🚨 **Troubleshooting**

### **Common Issues and Solutions**

#### **1. Docker Services Not Starting**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check GPU access
nvidia-smi

# Check logs
docker compose logs
```

#### **2. Kubernetes Services Not Accessible**
```bash
# Check endpoints
kubectl get endpoints -n ai-infrastructure

# Check service connectivity
kubectl run debug --image=busybox --rm -it --restart=Never -- wget -qO- http://ai-routing-api:8001/health
```

#### **3. External Access Issues**
```bash
# Check ingress status
kubectl describe ingress ai-external-ingress -n ai-infrastructure

# Check certificate status
kubectl describe certificate api-askcollections-com-tls -n ai-infrastructure

# Check DNS resolution
nslookup api.askcollections.com
```

#### **4. SSL Certificate Issues**
```bash
# Check cert-manager
kubectl get pods -n cert-manager

# Check certificate issuer
kubectl describe clusterissuer letsencrypt-prod

# Check certificate order
kubectl get certificaterequests -n ai-infrastructure
```

## 📚 **API Endpoints Reference**

### **Available Endpoints**

| Endpoint | Description | Method |
|----------|-------------|---------|
| `https://api.askcollections.com/api/` | Main AI Routing API | GET |
| `https://api.askcollections.com/api/health` | Health check | GET |
| `https://api.askcollections.com/api/route` | AI routing endpoint | POST |
| `https://api.askcollections.com/stt/health` | STT health check | GET |
| `https://api.askcollections.com/tts/health` | TTS health check | GET |
| `https://api.askcollections.com/vllm/v1/models` | Available models | GET |
| `https://api.askcollections.com/health` | Overall health | GET |

### **Example API Usage**

```bash
# AI Chat Request
curl -X POST https://api.askcollections.com/api/route \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Hello, how are you?",
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Get Available Models
curl https://api.askcollections.com/vllm/v1/models

# Health Check
curl https://api.askcollections.com/health
```

## 🔄 **Updates and Maintenance**

### **Updating Services**

```bash
# Update Docker services
docker compose pull
docker compose up -d

# Update Kubernetes configurations
kubectl apply -f k8s/

# Restart services if needed
kubectl rollout restart deployment -n ai-infrastructure
```

### **Backup and Recovery**

```bash
# Backup configurations
kubectl get all -n ai-infrastructure -o yaml > ai-infrastructure-backup.yaml

# Backup models
sudo tar -czf ai-models-backup.tar.gz /opt/ai-models/

# Restore from backup
kubectl apply -f ai-infrastructure-backup.yaml
sudo tar -xzf ai-models-backup.tar.gz -C /
```

## 📞 **Support and Resources**

### **Documentation Links**
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [vLLM Documentation](https://docs.vllm.ai/)

### **Community Support**
- [Docker Community Forums](https://forums.docker.com/)
- [Kubernetes Slack](https://kubernetes.slack.com/)
- [vLLM GitHub Issues](https://github.com/vllm-project/vllm/issues)

---

**Status**: ✅ **Production Ready**  
**Last Updated**: January 2025  
**Version**: 2.0.0

This guide provides a complete setup for a production-ready AI infrastructure with external access via HTTPS and Cloudflare integration.
