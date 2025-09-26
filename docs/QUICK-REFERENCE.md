# AI Infrastructure Quick Reference

## 🚀 **Current Setup Status**

✅ **Production Ready** - All services are running and accessible via HTTPS

### **Service Status**
- **Docker Services**: 9 containers running
- **Kubernetes Integration**: Active with nginx ingress
- **External Access**: `https://api.askcollections.com` working
- **SSL Certificates**: Managed by cert-manager + Let's Encrypt
- **Cloudflare Integration**: Active with HTTPS termination

---

## 🌐 **API Endpoints**

### **Main API Endpoints**
```bash
# Main AI Routing API
curl https://api.askcollections.com/api/
curl https://api.askcollections.com/api/health

# AI Chat Request
curl -X POST https://api.askcollections.com/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, how are you?", "max_tokens": 50}'
```

### **Speech Services**
```bash
# Speech-to-Text
curl https://api.askcollections.com/stt/health

# Text-to-Speech
curl https://api.askcollections.com/tts/health
```

### **Direct vLLM Access**
```bash
# Available Models
curl https://api.askcollections.com/vllm/v1/models

# Direct Inference
curl -X POST https://api.askcollections.com/vllm/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/app/models/multimodal/minicpm-v-4", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## 🔧 **Management Commands**

### **Docker Services**
```bash
# Check status
docker compose ps

# View logs
docker compose logs -f routing-api
docker compose logs -f vllm-inference-server

# Restart services
docker compose restart routing-api
docker compose up -d
```

### **Kubernetes Services**
```bash
# Check status
kubectl get all -n ai-infrastructure
kubectl get ingress -n ai-infrastructure

# View logs
kubectl logs -f deployment/ai-routing-api -n ai-infrastructure

# Test internal connectivity
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-routing-api.ai-infrastructure.svc.cluster.local:8001/health
```

### **SSL Certificates**
```bash
# Check certificate status
kubectl get certificates -n ai-infrastructure
kubectl describe certificate api-askcollections-com-tls -n ai-infrastructure

# Check cert-manager
kubectl get pods -n cert-manager
```

---

## 📊 **Monitoring**

### **Service Health**
```bash
# Docker services
curl http://localhost:8000/health  # vLLM
curl http://localhost:8001/health  # Routing API
curl http://localhost:8002/health  # STT
curl http://localhost:8003/health  # TTS

# External services
curl https://api.askcollections.com/health
```

### **Resource Usage**
```bash
# GPU usage
nvidia-smi

# System resources
htop

# Kubernetes resources
kubectl top nodes
kubectl top pods -n ai-infrastructure
```

### **Monitoring Dashboards**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Services Not Responding**
```bash
# Check Docker services
docker compose ps
docker compose logs

# Check Kubernetes services
kubectl get pods -n ai-infrastructure
kubectl get endpoints -n ai-infrastructure
```

#### **2. External Access Issues**
```bash
# Check ingress status
kubectl describe ingress ai-external-ingress -n ai-infrastructure

# Check DNS resolution
nslookup api.askcollections.com

# Test direct IP access
curl -H "Host: api.askcollections.com" http://192.168.0.20/api/health
```

#### **3. SSL Certificate Issues**
```bash
# Check certificate status
kubectl get certificates -n ai-infrastructure
kubectl describe certificate api-askcollections-com-tls -n ai-infrastructure

# Check cert-manager logs
kubectl logs -f deployment/cert-manager -n cert-manager
```

#### **4. Model Loading Issues**
```bash
# Check model files
ls -la /opt/ai-models/models/multimodal/minicpm-v-4/

# Check vLLM logs
docker compose logs vllm-inference-server

# Test model availability
curl http://localhost:8000/v1/models
```

---

## 🔄 **Updates and Maintenance**

### **Update Services**
```bash
# Update Docker services
docker compose pull
docker compose up -d

# Update Kubernetes configurations
kubectl apply -f k8s/
```

### **Backup and Recovery**
```bash
# Backup configurations
kubectl get all -n ai-infrastructure -o yaml > ai-infrastructure-backup.yaml

# Backup models
sudo tar -czf ai-models-backup.tar.gz /opt/ai-models/

# Restore from backup
kubectl apply -f ai-infrastructure-backup.yaml
```

---

## 📁 **File Structure**

```
gpu-setup/
├── docker-compose.yml              # Docker services configuration
├── Dockerfile.routing              # Routing API Dockerfile
├── requirements-routing.txt        # Python dependencies
├── k8s/
│   ├── namespace.yaml              # Kubernetes namespace
│   ├── services.yaml               # Kubernetes services
│   ├── endpoints.yaml              # Endpoints to Docker containers
│   ├── nginx-external-ingress.yaml # External nginx ingress
│   ├── letsencrypt-issuer.yaml    # SSL certificate issuer
│   ├── deploy.sh                   # Deployment script
│   └── README.md                   # Kubernetes documentation
├── scripts/
│   ├── setup-ai-infrastructure.sh  # Complete setup script
│   └── cleanup-and-organize.sh     # Cleanup script
├── docs/
│   ├── COMPLETE-SETUP-GUIDE.md     # Complete setup guide
│   └── QUICK-REFERENCE.md          # This file
└── src/
    ├── api/                        # API source code
    ├── routing/                    # Routing logic
    └── config/                     # Configuration files
```

---

## 🚨 **Emergency Procedures**

### **Service Recovery**
```bash
# Restart all Docker services
docker compose down
docker compose up -d

# Restart Kubernetes services
kubectl rollout restart deployment -n ai-infrastructure

# Check service health
./scripts/test-services.sh
```

### **Complete Rebuild**
```bash
# Stop all services
docker compose down

# Rebuild containers
docker compose build --no-cache

# Restart services
docker compose up -d

# Redeploy Kubernetes
kubectl apply -f k8s/
```

---

## 📞 **Support Information**

### **Service URLs**
- **Main API**: https://api.askcollections.com/api/
- **Health Check**: https://api.askcollections.com/health
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

### **Log Locations**
- **Docker Logs**: `docker compose logs [service-name]`
- **Kubernetes Logs**: `kubectl logs -f deployment/[deployment-name] -n ai-infrastructure`
- **System Logs**: `/var/log/syslog`

### **Configuration Files**
- **Docker**: `docker-compose.yml`
- **Kubernetes**: `k8s/` directory
- **Models**: `/opt/ai-models/models/`

---

**Last Updated**: January 2025  
**Version**: 2.0.0  
**Status**: ✅ Production Ready
