# Kubernetes Deployment for AI Infrastructure

This directory contains Kubernetes configurations for internal cluster access to AI services running in Docker containers.

## 🎯 **Overview**

The AI infrastructure uses **Internal DNS routing** to connect Kubernetes cluster applications to AI endpoints running in Docker containers on the host (192.168.0.21).

## 📁 **Files Structure**

```
k8s/
├── namespace.yaml           # Kubernetes namespace
├── services.yaml           # Internal ClusterIP services
├── endpoints.yaml          # Endpoints pointing to Docker containers
├── ingress-internal.yaml   # Internal ingress for intranet
├── configmap.yaml         # Configuration values
├── networkpolicy.yaml     # Network security policies
├── dns-config.yaml        # DNS configuration examples
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## 🚀 **Quick Deployment**

### **1. Prerequisites**

- Kubernetes cluster (v1.19+)
- kubectl configured
- Docker containers running AI services on host (192.168.0.21)
- NGINX Ingress Controller (for internal ingress)

### **2. Deploy**

```bash
# Make deployment script executable
chmod +x k8s/deploy.sh

# Run deployment
./k8s/deploy.sh
```

### **3. Manual Deployment**

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy services and endpoints
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/endpoints.yaml

# Deploy internal ingress (optional)
kubectl apply -f k8s/ingress-internal.yaml
```

## 🌐 **Access Methods**

### **1. Internal Cluster Access (Primary)**

**Service Names (within cluster):**
- Main API: `http://ai-routing-api:8001`
- STT Service: `http://ai-stt-service:8002`
- TTS Service: `http://ai-tts-service:8003`
- vLLM Service: `http://ai-vllm-service:8000`
- Redis Cache: `redis://ai-redis:6379`

### **2. Internal Ingress (Intranet)**

**Internal Domains:**
- Main API: `http://ai-api.internal`
- STT Service: `http://ai-stt.internal`
- TTS Service: `http://ai-tts.internal`
- vLLM Service: `http://ai-vllm.internal`

**Single Internal Domain:**
- All services: `http://ai.internal/api`, `http://ai.internal/stt`, etc.

## 🔧 **Configuration**

### **1. Docker Container Setup**

Ensure Docker containers are running on host IP `192.168.0.21`:
- vLLM Service: Port 8000
- Routing API: Port 8001  
- STT Service: Port 8002
- TTS Service: Port 8003
- Redis: Port 6379

### **2. Internal DNS (Intranet)**

For intranet access, configure your internal DNS server to resolve:
- `ai-api.internal`
- `ai-stt.internal`
- `ai-tts.internal`
- `ai-vllm.internal`
- `ai.internal` (single domain)

## 🔒 **Security**

### **1. Network Policies**

Network policies are deployed to restrict traffic:
- Only allow ingress from ingress controller
- Only allow internal service communication
- Restrict egress to necessary services

### **2. Internal Access Only**

- Services are accessible only within the cluster
- No external exposure by default
- Internal ingress provides controlled intranet access

### **3. CORS Configuration**

CORS is configured to allow cross-origin requests:
- Origins: `*` (configure as needed)
- Methods: `GET, POST, PUT, DELETE, OPTIONS`
- Headers: Standard API headers

## 📊 **Monitoring**

### **1. Check Deployment Status**

```bash
# Check pods
kubectl get pods -n ai-infrastructure

# Check services
kubectl get svc -n ai-infrastructure

# Check ingress
kubectl get ingress -n ai-infrastructure

# Check certificates
kubectl get certificates -n ai-infrastructure
```

### **2. View Logs**

```bash
# View pod logs
kubectl logs -f deployment/ai-routing-api -n ai-infrastructure
kubectl logs -f deployment/ai-stt-service -n ai-infrastructure
kubectl logs -f deployment/ai-tts-service -n ai-infrastructure
kubectl logs -f deployment/ai-vllm-service -n ai-infrastructure
```

### **3. Test Endpoints**

```bash
# Test from within cluster
kubectl run test-pod --image=busybox --rm -it --restart=Never -n ai-infrastructure -- wget -qO- http://ai-routing-api:8001/health

# Test main API
kubectl run test-pod --image=busybox --rm -it --restart=Never -n ai-infrastructure -- wget -qO- http://ai-routing-api:8001/health

# Test STT service
kubectl run test-pod --image=busybox --rm -it --restart=Never -n ai-infrastructure -- wget -qO- http://ai-stt-service:8002/health

# Test TTS service
kubectl run test-pod --image=busybox --rm -it --restart=Never -n ai-infrastructure -- wget -qO- http://ai-tts-service:8003/health
```

## 🛠️ **Troubleshooting**

### **1. Ingress Not Working**

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress status
kubectl describe ingress ai-infrastructure-external -n ai-infrastructure

# Check ingress controller logs
kubectl logs -f deployment/ingress-nginx-controller -n ingress-nginx
```

### **2. Certificates Not Issued**

```bash
# Check cert-manager
kubectl get pods -n cert-manager

# Check certificate status
kubectl describe certificate ai-infrastructure-tls -n ai-infrastructure

# Check certificate issuer
kubectl describe clusterissuer letsencrypt-prod
```

### **3. Services Not Accessible**

```bash
# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Check pod readiness
kubectl get pods -n ai-infrastructure -o wide

# Test internal connectivity
kubectl exec -it deployment/ai-routing-api -n ai-infrastructure -- curl http://ai-stt-service:8002/health
```

### **4. DNS Resolution Issues**

```bash
# Test DNS resolution
nslookup ai.bionicaisolutions.com/api
dig ai.bionicaisolutions.com/api

# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -f deployment/coredns -n kube-system
```

## 🔄 **Updates and Maintenance**

### **1. Update Configuration**

```bash
# Update ConfigMap
kubectl apply -f k8s/configmap.yaml

# Restart deployments to pick up changes
kubectl rollout restart deployment -n ai-infrastructure
```

### **2. Scale Services**

```bash
# Scale routing API
kubectl scale deployment ai-routing-api --replicas=3 -n ai-infrastructure

# Scale STT service
kubectl scale deployment ai-stt-service --replicas=2 -n ai-infrastructure
```

### **3. Backup and Restore**

```bash
# Backup configurations
kubectl get all -n ai-infrastructure -o yaml > ai-infrastructure-backup.yaml

# Restore from backup
kubectl apply -f ai-infrastructure-backup.yaml
```

## 📚 **Additional Resources**

- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

## 🆘 **Support**

For issues and questions:
1. Check the troubleshooting section above
2. Review Kubernetes logs
3. Verify DNS configuration
4. Check network connectivity
5. Ensure all prerequisites are met

---

**Status**: ✅ **Production Ready**  
**Last Updated**: September 5, 2025  
**Version**: 1.0.0
