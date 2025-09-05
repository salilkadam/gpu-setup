#!/bin/bash

# AI Infrastructure Kubernetes Deployment Script
# This script deploys the AI infrastructure to Kubernetes with external access

set -e

echo "🚀 Deploying AI Infrastructure to Kubernetes"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

print_success "Kubernetes cluster is accessible"

# Create namespace
print_status "Creating namespace..."
kubectl apply -f k8s/namespace.yaml
print_success "Namespace created"

# Create ConfigMap
print_status "Creating ConfigMap..."
kubectl apply -f k8s/configmap.yaml
print_success "ConfigMap created"

# Deploy services
print_status "Deploying internal services..."
kubectl apply -f k8s/services.yaml
print_success "Internal services deployed"

# Deploy network policies
print_status "Deploying network policies..."
kubectl apply -f k8s/networkpolicy.yaml
print_success "Network policies deployed"

# Check if ingress controller is available
print_status "Checking for ingress controller..."
if kubectl get pods -n ingress-nginx &> /dev/null; then
    print_success "NGINX Ingress Controller found"
    INGRESS_AVAILABLE=true
else
    print_warning "NGINX Ingress Controller not found"
    INGRESS_AVAILABLE=false
fi

# Deploy ingress if available
if [ "$INGRESS_AVAILABLE" = true ]; then
    print_status "Deploying ingress configurations..."
    
    # Check if cert-manager is available
    if kubectl get pods -n cert-manager &> /dev/null; then
        print_success "cert-manager found"
        print_status "Deploying certificates..."
        kubectl apply -f k8s/certificate.yaml
        print_success "Certificates deployed"
        
        print_status "Deploying external ingress..."
        kubectl apply -f k8s/ingress-external.yaml
        print_success "External ingress deployed"
    else
        print_warning "cert-manager not found, deploying without TLS"
        # Remove TLS sections from ingress
        sed 's/cert-manager.io\/cluster-issuer.*//' k8s/ingress-external.yaml | \
        sed '/tls:/,/secretName:/d' | \
        kubectl apply -f -
        print_success "External ingress deployed (without TLS)"
    fi
    
    print_status "Deploying internal ingress..."
    kubectl apply -f k8s/ingress-internal.yaml
    print_success "Internal ingress deployed"
else
    print_warning "Ingress not available, deploying LoadBalancer services..."
    kubectl apply -f k8s/loadbalancer.yaml
    print_success "LoadBalancer services deployed"
fi

# Deploy NodePort services as fallback
print_status "Deploying NodePort services..."
kubectl apply -f k8s/nodeport.yaml
print_success "NodePort services deployed"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=ai-routing-api -n ai-infrastructure --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=ai-stt-service -n ai-infrastructure --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=ai-tts-service -n ai-infrastructure --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=ai-vllm-service -n ai-infrastructure --timeout=300s || true

print_success "Services are ready"

# Display access information
echo ""
echo "🎯 DEPLOYMENT COMPLETE"
echo "======================"
echo ""

# Get cluster information
CLUSTER_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
if [ -z "$CLUSTER_IP" ]; then
    CLUSTER_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
fi

print_status "Cluster IP: $CLUSTER_IP"

if [ "$INGRESS_AVAILABLE" = true ]; then
    echo ""
    print_success "🌐 EXTERNAL ACCESS (via Ingress):"
    echo "  Main API:     https://ai-api.yourdomain.com"
    echo "  STT Service:  https://ai-stt.yourdomain.com"
    echo "  TTS Service:  https://ai-tts.yourdomain.com"
    echo "  vLLM Service: https://ai-vllm.yourdomain.com"
    echo ""
    print_success "🏠 INTERNAL ACCESS (via Ingress):"
    echo "  Main API:     http://ai-api.internal"
    echo "  STT Service:  http://ai-stt.internal"
    echo "  TTS Service:  http://ai-tts.internal"
    echo "  vLLM Service: http://ai-vllm.internal"
    echo ""
    print_success "🔗 SINGLE DOMAIN ACCESS:"
    echo "  Main API:     https://ai.yourdomain.com/api"
    echo "  STT Service:  https://ai.yourdomain.com/stt"
    echo "  TTS Service:  https://ai.yourdomain.com/tts"
    echo "  vLLM Service: https://ai.yourdomain.com/vllm"
else
    echo ""
    print_success "🌐 LOADBALANCER ACCESS:"
    kubectl get svc -n ai-infrastructure -l app=ai-routing-api
    kubectl get svc -n ai-infrastructure -l app=ai-stt-service
    kubectl get svc -n ai-infrastructure -l app=ai-tts-service
    kubectl get svc -n ai-infrastructure -l app=ai-vllm-service
fi

echo ""
print_success "🔌 NODEPORT ACCESS:"
echo "  Main API:     http://$CLUSTER_IP:30001"
echo "  STT Service:  http://$CLUSTER_IP:30002"
echo "  TTS Service:  http://$CLUSTER_IP:30003"
echo "  vLLM Service: http://$CLUSTER_IP:30000"

echo ""
print_success "📊 MONITORING:"
echo "  Check services: kubectl get pods -n ai-infrastructure"
echo "  Check ingress:  kubectl get ingress -n ai-infrastructure"
echo "  Check services: kubectl get svc -n ai-infrastructure"

echo ""
print_warning "⚠️  NEXT STEPS:"
echo "  1. Update DNS records to point to your cluster IP"
echo "  2. Replace 'yourdomain.com' with your actual domain"
echo "  3. Update email in certificate.yaml"
echo "  4. Configure firewall rules for ports 80, 443, 30000-30003"
echo "  5. Test the endpoints using the provided URLs"

echo ""
print_success "🎉 AI Infrastructure deployed successfully!"
