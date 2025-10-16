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
- **Wan Video Generation**: `https://api.askcollections.com/wan/health`

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
