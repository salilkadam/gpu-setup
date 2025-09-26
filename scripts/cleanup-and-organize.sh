#!/bin/bash

# Cleanup and Organize AI Infrastructure Script
# This script cleans up redundant files and organizes the current setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/$USER/gpu-setup"
BACKUP_DIR="$PROJECT_DIR/archive"

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

# Create backup directory
create_backup_dir() {
    log "Creating backup directory..."
    mkdir -p "$BACKUP_DIR"
}

# Backup important files before cleanup
backup_files() {
    log "Backing up important files..."
    
    # Backup current working configurations
    cp "$PROJECT_DIR/k8s/nginx-ai-ingress.yaml" "$BACKUP_DIR/" 2>/dev/null || true
    cp "$PROJECT_DIR/k8s/kong-ai-ingress.yaml" "$BACKUP_DIR/" 2>/dev/null || true
    cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_DIR/" 2>/dev/null || true
    cp "$PROJECT_DIR/Dockerfile.routing" "$BACKUP_DIR/" 2>/dev/null || true
    
    log "Files backed up successfully."
}

# Remove redundant Kubernetes files
cleanup_k8s_files() {
    log "Cleaning up redundant Kubernetes files..."
    
    cd "$PROJECT_DIR/k8s"
    
    # Remove redundant ingress files (keep only the working nginx ingress)
    if [ -f "kong-ai-ingress.yaml" ]; then
        info "Removing redundant Kong ingress file..."
        mv kong-ai-ingress.yaml "$BACKUP_DIR/"
    fi
    
    if [ -f "kong-ai-ingress-https.yaml" ]; then
        info "Removing redundant Kong HTTPS ingress file..."
        mv kong-ai-ingress-https.yaml "$BACKUP_DIR/"
    fi
    
    # Remove internal ingress files (not needed for external access)
    if [ -f "ingress-internal.yaml" ]; then
        info "Removing internal ingress file..."
        mv ingress-internal.yaml "$BACKUP_DIR/"
    fi
    
    # Remove redundant config files
    if [ -f "dns-config.yaml" ]; then
        info "Removing DNS config file..."
        mv dns-config.yaml "$BACKUP_DIR/"
    fi
    
    if [ -f "nginx-config.yaml" ]; then
        info "Removing nginx config file..."
        mv nginx-config.yaml "$BACKUP_DIR/"
    fi
    
    # Remove network policy (not needed for current setup)
    if [ -f "networkpolicy.yaml" ]; then
        info "Removing network policy file..."
        mv networkpolicy.yaml "$BACKUP_DIR/"
    fi
    
    # Remove configmap (not used in current setup)
    if [ -f "configmap.yaml" ]; then
        info "Removing configmap file..."
        mv configmap.yaml "$BACKUP_DIR/"
    fi
    
    log "Kubernetes files cleaned up successfully."
}

# Rename working files to standard names
rename_working_files() {
    log "Renaming working files to standard names..."
    
    cd "$PROJECT_DIR/k8s"
    
    # Rename the working nginx ingress to standard name
    if [ -f "nginx-ai-ingress.yaml" ]; then
        info "Renaming nginx-ai-ingress.yaml to nginx-external-ingress.yaml..."
        mv nginx-ai-ingress.yaml nginx-external-ingress.yaml
    fi
    
    log "Files renamed successfully."
}

# Create Let's Encrypt issuer if it doesn't exist
create_letsencrypt_issuer() {
    log "Creating Let's Encrypt issuer..."
    
    if [ ! -f "$PROJECT_DIR/k8s/letsencrypt-issuer.yaml" ]; then
        cat > "$PROJECT_DIR/k8s/letsencrypt-issuer.yaml" << 'EOF'
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Update this with your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
        info "Let's Encrypt issuer created."
    else
        info "Let's Encrypt issuer already exists."
    fi
}

# Update README with current setup
update_readme() {
    log "Updating README with current setup..."
    
    cat > "$PROJECT_DIR/k8s/README.md" << 'EOF'
# Kubernetes Deployment for AI Infrastructure

This directory contains Kubernetes configurations for external access to AI services running in Docker containers.

## 🎯 **Overview**

The AI infrastructure uses **External DNS routing** to provide public access to AI endpoints running in Docker containers on the host (192.168.0.20).

## 📁 **Files Structure**

```
k8s/
├── namespace.yaml                    # Kubernetes namespace
├── services.yaml                     # Internal ClusterIP services
├── endpoints.yaml                    # Endpoints pointing to Docker containers
├── nginx-external-ingress.yaml      # External nginx ingress for public access
├── letsencrypt-issuer.yaml          # Let's Encrypt SSL certificate issuer
└── README.md                        # This file
```

## 🚀 **Quick Deployment**

### **1. Prerequisites**

- Kubernetes cluster (v1.19+)
- kubectl configured
- Docker containers running AI services on host (192.168.0.20)
- NGINX Ingress Controller
- cert-manager for SSL certificates
- Domain name with DNS control

### **2. Deploy**

```bash
# Deploy all resources
kubectl apply -f k8s/

# Or deploy individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/endpoints.yaml
kubectl apply -f k8s/letsencrypt-issuer.yaml
kubectl apply -f k8s/nginx-external-ingress.yaml
```

## 🌐 **External Access**

### **Public API Endpoints**

Your AI services are accessible via HTTPS at `api.askcollections.com`:

- **Main API**: `https://api.askcollections.com/api/`
- **Health Check**: `https://api.askcollections.com/api/health`
- **AI Routing**: `https://api.askcollections.com/api/route`
- **Speech-to-Text**: `https://api.askcollections.com/stt/health`
- **Text-to-Speech**: `https://api.askcollections.com/tts/health`
- **Direct vLLM**: `https://api.askcollections.com/vllm/v1/models`

### **DNS Configuration**

Configure your DNS to point `api.askcollections.com` to the nginx ingress external IPs:

```bash
# Get nginx ingress external IPs
kubectl get svc -n ingress-nginx
```

## 🔧 **Configuration**

### **1. Docker Container Setup**

Ensure Docker containers are running on host IP `192.168.0.20`:
- vLLM Service: Port 8000
- Routing API: Port 8001  
- STT Service: Port 8002
- TTS Service: Port 8003
- Redis: Port 6379

### **2. SSL Certificates**

SSL certificates are automatically managed by cert-manager using Let's Encrypt.

### **3. CORS and Security**

The nginx ingress is configured with:
- CORS enabled for cross-origin requests
- Rate limiting (1000 requests/minute)
- Automatic HTTPS redirect
- Security headers

## 📊 **Monitoring**

### **1. Check Deployment Status**

```bash
# Check all resources
kubectl get all -n ai-infrastructure

# Check ingress
kubectl get ingress -n ai-infrastructure

# Check certificates
kubectl get certificates -n ai-infrastructure
```

### **2. Test Endpoints**

```bash
# Test external access
curl https://api.askcollections.com/api/health

# Test AI routing
curl -X POST https://api.askcollections.com/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, how are you?", "max_tokens": 50}'
```

## 🛠️ **Troubleshooting**

### **1. Ingress Not Working**

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress status
kubectl describe ingress ai-external-ingress -n ai-infrastructure
```

### **2. SSL Certificate Issues**

```bash
# Check cert-manager
kubectl get pods -n cert-manager

# Check certificate status
kubectl describe certificate api-askcollections-com-tls -n ai-infrastructure
```

### **3. Services Not Accessible**

```bash
# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Test internal connectivity
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-routing-api.ai-infrastructure.svc.cluster.local:8001/health
```

---

**Status**: ✅ **Production Ready**  
**Last Updated**: January 2025  
**Version**: 2.0.0
EOF

    log "README updated successfully."
}

# Create deployment script
create_deployment_script() {
    log "Creating deployment script..."
    
    cat > "$PROJECT_DIR/k8s/deploy.sh" << 'EOF'
#!/bin/bash

# AI Infrastructure Kubernetes Deployment Script

set -e

echo "🚀 Deploying AI Infrastructure to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible. Please check your kubeconfig."
    exit 1
fi

echo "✅ Kubernetes cluster is accessible"

# Deploy resources
echo "📦 Deploying namespace..."
kubectl apply -f namespace.yaml

echo "📦 Deploying services..."
kubectl apply -f services.yaml

echo "📦 Deploying endpoints..."
kubectl apply -f endpoints.yaml

echo "📦 Deploying Let's Encrypt issuer..."
kubectl apply -f letsencrypt-issuer.yaml

echo "📦 Deploying external ingress..."
kubectl apply -f nginx-external-ingress.yaml

echo "⏳ Waiting for resources to be ready..."
sleep 10

echo "🔍 Checking deployment status..."
kubectl get all -n ai-infrastructure
kubectl get ingress -n ai-infrastructure

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Your AI services are now accessible at:"
echo "   https://api.askcollections.com/api/"
echo "   https://api.askcollections.com/stt/health"
echo "   https://api.askcollections.com/tts/health"
echo "   https://api.askcollections.com/vllm/v1/models"
echo ""
echo "📋 Next steps:"
echo "   1. Configure DNS to point api.askcollections.com to nginx ingress IPs"
echo "   2. Enable Cloudflare proxy for HTTPS termination"
echo "   3. Test external access"
EOF

    chmod +x "$PROJECT_DIR/k8s/deploy.sh"
    log "Deployment script created successfully."
}

# Main cleanup function
main() {
    log "Starting cleanup and organization..."
    
    create_backup_dir
    backup_files
    cleanup_k8s_files
    rename_working_files
    create_letsencrypt_issuer
    update_readme
    create_deployment_script
    
    log "Cleanup and organization completed successfully!"
    
    info "Summary of changes:"
    info "✅ Removed redundant Kong ingress files"
    info "✅ Removed internal ingress files"
    info "✅ Removed unused config files"
    info "✅ Renamed working nginx ingress to standard name"
    info "✅ Created Let's Encrypt issuer"
    info "✅ Updated README with current setup"
    info "✅ Created deployment script"
    
    info "Backed up files are available in: $BACKUP_DIR"
    info "Current working files:"
    info "- k8s/nginx-external-ingress.yaml (main ingress)"
    info "- k8s/letsencrypt-issuer.yaml (SSL certificates)"
    info "- k8s/deploy.sh (deployment script)"
}

# Run main function
main "$@"
