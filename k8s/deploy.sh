#!/bin/bash

# AI Infrastructure Kubernetes Deployment Script
# This script deploys the AI infrastructure to Kubernetes for internal cluster access

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

# Deploy services and endpoints
print_status "Deploying internal services..."
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/endpoints.yaml
print_success "Internal services and endpoints deployed"

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

# Deploy internal ingress if available
if [ "$INGRESS_AVAILABLE" = true ]; then
    print_status "Deploying internal ingress..."
    kubectl apply -f k8s/ingress-internal.yaml
    print_success "Internal ingress deployed"
else
    print_warning "Ingress not available - services will be accessible via ClusterIP only"
fi

# Check service endpoints
print_status "Checking service endpoints..."
kubectl get endpoints -n ai-infrastructure
print_success "Service endpoints verified"

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

echo ""
print_success "🏠 INTERNAL CLUSTER ACCESS:"
echo "  Main API:     http://ai-routing-api:8001"
echo "  STT Service:  http://ai-stt-service:8002"
echo "  TTS Service:  http://ai-tts-service:8003"
echo "  vLLM Service: http://ai-vllm-service:8000"
echo "  Redis Cache:  redis://ai-redis:6379"

if [ "$INGRESS_AVAILABLE" = true ]; then
    echo ""
    print_success "🌐 INTERNAL INGRESS ACCESS:"
    echo "  Main API:     http://ai-api.internal"
    echo "  STT Service:  http://ai-stt.internal"
    echo "  TTS Service:  http://ai-tts.internal"
    echo "  vLLM Service: http://ai-vllm.internal"
    echo ""
    print_success "🔗 SINGLE DOMAIN ACCESS:"
    echo "  Main API:     http://ai.internal/api"
    echo "  STT Service:  http://ai.internal/stt"
    echo "  TTS Service:  http://ai.internal/tts"
    echo "  vLLM Service: http://ai.internal/vllm"
fi

echo ""
print_success "📊 MONITORING:"
echo "  Check services: kubectl get pods -n ai-infrastructure"
echo "  Check ingress:  kubectl get ingress -n ai-infrastructure"
echo "  Check services: kubectl get svc -n ai-infrastructure"

echo ""
print_warning "⚠️  NEXT STEPS:"
echo "  1. Ensure Docker containers are running on host (192.168.0.21)"
echo "  2. Configure internal DNS for .internal domains (if using ingress)"
echo "  3. Test the endpoints from within the cluster"
echo "  4. Monitor service health and logs"

echo ""
print_success "🎉 AI Infrastructure deployed successfully!"
