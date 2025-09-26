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
