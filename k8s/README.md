# Kubernetes Deployment for AI Infrastructure

This directory contains Kubernetes configurations to deploy the AI infrastructure with external access capabilities.

## 🎯 **Overview**

The AI infrastructure can be accessed from remote machines through multiple methods:
- **External Ingress** (recommended for production)
- **LoadBalancer Services** (cloud providers)
- **NodePort Services** (direct node access)
- **Internal DNS** (intranet access)

## 📁 **Files Structure**

```
k8s/
├── namespace.yaml           # Kubernetes namespace
├── services.yaml           # Internal ClusterIP services
├── ingress-external.yaml   # External ingress with TLS
├── ingress-internal.yaml   # Internal ingress for intranet
├── loadbalancer.yaml       # LoadBalancer services
├── nodeport.yaml          # NodePort services
├── configmap.yaml         # Configuration values
├── networkpolicy.yaml     # Network security policies
├── certificate.yaml       # TLS certificates
├── dns-config.yaml        # DNS configuration examples
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## 🚀 **Quick Deployment**

### **1. Prerequisites**

- Kubernetes cluster (v1.19+)
- kubectl configured
- NGINX Ingress Controller (optional)
- cert-manager (optional, for TLS)

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

# Deploy services
kubectl apply -f k8s/services.yaml

# Deploy ingress (if available)
kubectl apply -f k8s/ingress-external.yaml
kubectl apply -f k8s/ingress-internal.yaml

# Deploy LoadBalancer services
kubectl apply -f k8s/loadbalancer.yaml

# Deploy NodePort services
kubectl apply -f k8s/nodeport.yaml
```

## 🌐 **Access Methods**

### **1. External Ingress (Recommended)**

**External Domains:**
- Main API: `https://ai.bionicaisolutions.com/api`
- STT Service: `https://ai.bionicaisolutions.com/stt`
- TTS Service: `https://ai.bionicaisolutions.com/tts`
- vLLM Service: `https://ai.bionicaisolutions.com/vllm`

**Single Domain:**
- Main API: `https://ai.bionicaisolutions.com/api`
- STT Service: `https://ai.bionicaisolutions.com/stt`
- TTS Service: `https://ai.bionicaisolutions.com/tts`
- vLLM Service: `https://ai.bionicaisolutions.com/vllm`

### **2. Internal Ingress (Intranet)**

**Internal Domains:**
- Main API: `http://ai-api.internal`
- STT Service: `http://ai-stt.internal`
- TTS Service: `http://ai-tts.internal`
- vLLM Service: `http://ai-vllm.internal`

### **3. LoadBalancer Services**

```bash
# Get LoadBalancer IPs
kubectl get svc -n ai-infrastructure

# Access via LoadBalancer IPs
# http://LOADBALANCER_IP:80
```

### **4. NodePort Services**

```bash
# Get node IP
kubectl get nodes -o wide

# Access via NodePort
# http://NODE_IP:30001  (Main API)
# http://NODE_IP:30002  (STT Service)
# http://NODE_IP:30003  (TTS Service)
# http://NODE_IP:30000  (vLLM Service)
```

## 🔧 **Configuration**

### **1. Update Domains**

Edit the following files to replace `bionicaisolutions.com` with your actual domain:

- `k8s/ingress-external.yaml`
- `k8s/certificate.yaml`
- `k8s/configmap.yaml`

### **2. Update Email for Certificates**

Edit `k8s/certificate.yaml` and replace `your-email@bionicaisolutions.com` with your email.

### **3. Configure DNS**

Add DNS records pointing to your cluster:

```bash
# A Records
ai.bionicaisolutions.com/api     A    YOUR_CLUSTER_IP
ai.bionicaisolutions.com/stt     A    YOUR_CLUSTER_IP
ai.bionicaisolutions.com/tts     A    YOUR_CLUSTER_IP
ai.bionicaisolutions.com/vllm    A    YOUR_CLUSTER_IP
ai.bionicaisolutions.com         A    YOUR_CLUSTER_IP
```

### **4. Internal DNS (Intranet)**

For intranet access, configure your internal DNS server to resolve:
- `ai-api.internal`
- `ai-stt.internal`
- `ai-tts.internal`
- `ai-vllm.internal`

## 🔒 **Security**

### **1. Network Policies**

Network policies are deployed to restrict traffic:
- Only allow ingress from ingress controller
- Only allow internal service communication
- Restrict egress to necessary services

### **2. TLS Certificates**

- Automatic TLS certificates via Let's Encrypt
- HTTPS redirect enabled
- Secure headers configured

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
# Test main API
curl -X POST https://ai.bionicaisolutions.com/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, world!"}'

# Test STT service
curl -X POST https://ai.bionicaisolutions.com/stt/transcribe \
  -F "file=@audio.wav" \
  -F "language=hi"

# Test TTS service
curl -X POST https://ai.bionicaisolutions.com/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "language": "hi", "gender": "female"}'
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
