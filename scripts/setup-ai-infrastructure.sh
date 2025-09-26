#!/bin/bash

# AI Infrastructure Complete Setup Script
# This script sets up the complete AI infrastructure from scratch

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/$USER/gpu-setup"
HOST_IP="192.168.0.20"  # Update this with your actual host IP
DOMAIN="api.askcollections.com"  # Update this with your domain
EMAIL="your-email@example.com"  # Update this with your email

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user with sudo privileges."
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check if NVIDIA GPU is available
    if ! command -v nvidia-smi &> /dev/null; then
        error "NVIDIA GPU driver not found. Please install NVIDIA drivers first."
    fi
    
    # Check available GPU memory
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    if [ "$GPU_MEMORY" -lt 20000 ]; then
        warning "GPU memory is less than 20GB. Some models may not work properly."
    fi
    
    # Check system memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 32 ]; then
        warning "System memory is less than 32GB. Consider upgrading for better performance."
    fi
    
    log "System requirements check completed."
}

# Install Docker and Docker Compose
install_docker() {
    log "Installing Docker and Docker Compose..."
    
    if command -v docker &> /dev/null; then
        info "Docker is already installed."
    else
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        log "Docker installed successfully."
    fi
    
    if command -v docker-compose &> /dev/null; then
        info "Docker Compose is already installed."
    else
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        log "Docker Compose installed successfully."
    fi
}

# Install Kubernetes (K3s)
install_kubernetes() {
    log "Installing Kubernetes (K3s)..."
    
    if command -v kubectl &> /dev/null; then
        info "Kubernetes is already installed."
    else
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
        
        log "Kubernetes installed successfully."
    fi
}

# Install ingress controllers
install_ingress_controllers() {
    log "Installing ingress controllers..."
    
    # Install NGINX Ingress Controller
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
    
    # Install Kong Ingress Controller
    kubectl apply -f https://raw.githubusercontent.com/Kong/kubernetes-ingress-controller/main/deploy/single/all-in-one-dbless.yaml
    
    # Install cert-manager
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for controllers to be ready
    log "Waiting for ingress controllers to be ready..."
    kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s
    kubectl wait --namespace kong --for=condition=ready pod --selector=app.kubernetes.io/name=ingress-controller --timeout=300s
    kubectl wait --namespace cert-manager --for=condition=ready pod --selector=app.kubernetes.io/name=cert-manager --timeout=300s
    
    log "Ingress controllers installed successfully."
}

# Create project structure
create_project_structure() {
    log "Creating project structure..."
    
    # Create directories
    mkdir -p "$PROJECT_DIR"/{docker,k8s,nginx,prometheus,grafana,logs,scripts,src/{api,audio,routing,config},tests/{unit,integration}}
    
    # Create model storage directory
    sudo mkdir -p /opt/ai-models/models
    sudo chown $USER:$USER /opt/ai-models/models
    
    log "Project structure created successfully."
}

# Download AI models
download_models() {
    log "Downloading AI models..."
    
    # Check if models already exist
    if [ -d "/opt/ai-models/models/multimodal/minicpm-v-4" ]; then
        info "Models already exist, skipping download."
        return
    fi
    
    # Download MiniCPM-V-4
    model_path="/opt/ai-models/models/multimodal"
    mkdir -p "$model_path"
    
    cd "$model_path"
    git lfs install
    git clone https://huggingface.co/openbmb/MiniCPM-V-4 minicpm-v-4
    
    # Download Whisper
    model_path="/opt/ai-models/models/audio"
    mkdir -p "$model_path"
    
    cd "$model_path"
    git lfs install
    git clone https://huggingface.co/openai/whisper-large-v3 whisper-large-v3
    
    log "AI models downloaded successfully."
}

# Create configuration files
create_config_files() {
    log "Creating configuration files..."
    
    # Create docker-compose.yml
    cat > "$PROJECT_DIR/docker-compose.yml" << 'EOF'
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
EOF

    # Create Dockerfile.routing
    cat > "$PROJECT_DIR/Dockerfile.routing" << 'EOF'
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
EOF

    # Create requirements-routing.txt
    cat > "$PROJECT_DIR/requirements-routing.txt" << 'EOF'
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
EOF

    log "Configuration files created successfully."
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    log "Deploying Kubernetes resources..."
    
    # Create namespace
    cat > "$PROJECT_DIR/k8s/namespace.yaml" << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: ai-infrastructure
  labels:
    name: ai-infrastructure
    purpose: ai-services
EOF

    # Create services
    cat > "$PROJECT_DIR/k8s/services.yaml" << 'EOF'
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
EOF

    # Create endpoints
    cat > "$PROJECT_DIR/k8s/endpoints.yaml" << EOF
apiVersion: v1
kind: Endpoints
metadata:
  name: ai-routing-api
  namespace: ai-infrastructure
subsets:
- addresses:
  - ip: $HOST_IP
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
  - ip: $HOST_IP
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
  - ip: $HOST_IP
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
  - ip: $HOST_IP
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
  - ip: $HOST_IP
  ports:
  - port: 6379
    name: redis
EOF

    # Create Let's Encrypt issuer
    cat > "$PROJECT_DIR/k8s/letsencrypt-issuer.yaml" << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: $EMAIL
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

    # Create external ingress
    cat > "$PROJECT_DIR/k8s/nginx-external-ingress.yaml" << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-external-ingress
  namespace: ai-infrastructure
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /\$2
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
    - $DOMAIN
    secretName: ${DOMAIN//./-}-tls
  rules:
  - host: $DOMAIN
    http:
      paths:
      # Main AI Routing API
      - path: /api(/|\$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-routing-api
            port:
              number: 8001
      # Speech-to-Text Service
      - path: /stt(/|\$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-stt-service
            port:
              number: 8002
      # Text-to-Speech Service
      - path: /tts(/|\$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-tts-service
            port:
              number: 8003
      # Direct vLLM Service
      - path: /vllm(/|\$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-vllm-service
            port:
              number: 8000
      # Health check endpoint
      - path: /health(/|\$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: ai-routing-api
            port:
              number: 8001
EOF

    # Deploy Kubernetes resources
    cd "$PROJECT_DIR"
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/services.yaml
    kubectl apply -f k8s/endpoints.yaml
    kubectl apply -f k8s/letsencrypt-issuer.yaml
    kubectl apply -f k8s/nginx-external-ingress.yaml
    
    log "Kubernetes resources deployed successfully."
}

# Start Docker services
start_docker_services() {
    log "Starting Docker services..."
    
    cd "$PROJECT_DIR"
    docker compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    for service in vllm-inference-server ai-routing-api ai-stt-service ai-tts-service ai-redis; do
        if docker compose ps | grep -q "$service.*healthy"; then
            log "$service is healthy"
        else
            warning "$service is not healthy, checking logs..."
            docker compose logs "$service"
        fi
    done
    
    log "Docker services started successfully."
}

# Test the setup
test_setup() {
    log "Testing the setup..."
    
    # Test Docker services
    info "Testing Docker services..."
    curl -f http://localhost:8000/health || error "vLLM service not responding"
    curl -f http://localhost:8001/health || error "Routing API not responding"
    curl -f http://localhost:8002/health || error "STT service not responding"
    curl -f http://localhost:8003/health || error "TTS service not responding"
    
    # Test Kubernetes integration
    info "Testing Kubernetes integration..."
    kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-routing-api.ai-infrastructure.svc.cluster.local:8001/health || error "Kubernetes service not responding"
    
    # Test external access (if domain is configured)
    if [ "$DOMAIN" != "api.askcollections.com" ]; then
        info "Testing external access..."
        curl -H "Host: $DOMAIN" https://$DOMAIN/api/ -k || warning "External access not working (this is expected if DNS is not configured yet)"
    fi
    
    log "Setup testing completed successfully."
}

# Main setup function
main() {
    log "Starting AI Infrastructure setup..."
    
    check_root
    check_requirements
    install_docker
    install_kubernetes
    install_ingress_controllers
    create_project_structure
    download_models
    create_config_files
    deploy_kubernetes
    start_docker_services
    test_setup
    
    log "AI Infrastructure setup completed successfully!"
    
    info "Next steps:"
    info "1. Configure DNS to point $DOMAIN to your nginx ingress external IPs"
    info "2. Enable Cloudflare proxy for HTTPS termination"
    info "3. Test external access: curl https://$DOMAIN/api/health"
    info "4. Monitor services: docker compose ps && kubectl get all -n ai-infrastructure"
    
    info "Service URLs:"
    info "- vLLM: http://localhost:8000"
    info "- Routing API: http://localhost:8001"
    info "- STT: http://localhost:8002"
    info "- TTS: http://localhost:8003"
    info "- Prometheus: http://localhost:9090"
    info "- Grafana: http://localhost:3000 (admin/admin)"
}

# Run main function
main "$@"
