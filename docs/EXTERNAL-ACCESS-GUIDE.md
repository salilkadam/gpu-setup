# 🌐 External Access Guide: AI Infrastructure

## 🎯 **Overview**

This guide provides comprehensive instructions for making your AI infrastructure APIs accessible from remote machines through Kubernetes ingress, LoadBalancer services, and intranet DNS configuration.

## 🏗️ **Architecture Options**

### **1. External Ingress (Recommended for Production)**
```
Internet → DNS → LoadBalancer → Ingress Controller → AI Services
```

### **2. LoadBalancer Services (Cloud Providers)**
```
Internet → DNS → LoadBalancer → AI Services
```

### **3. NodePort Services (Direct Access)**
```
Internet → DNS → Node IP:Port → AI Services
```

### **4. Internal DNS (Intranet)**
```
Intranet → Internal DNS → AI Services
```

## 🚀 **Quick Setup**

### **1. Deploy to Kubernetes**

```bash
# Clone and navigate to the project
cd /path/to/your/project

# Make deployment script executable
chmod +x k8s/deploy.sh

# Deploy with external access
./k8s/deploy.sh
```

### **2. Configure DNS**

Add these DNS records to your DNS provider:

```bash
# A Records (replace YOUR_CLUSTER_IP with your actual cluster IP)
ai-api.yourdomain.com     A    YOUR_CLUSTER_IP
ai-stt.yourdomain.com     A    YOUR_CLUSTER_IP
ai-tts.yourdomain.com     A    YOUR_CLUSTER_IP
ai-vllm.yourdomain.com    A    YOUR_CLUSTER_IP
ai.yourdomain.com         A    YOUR_CLUSTER_IP

# CNAME Records (if using load balancer)
ai-api.yourdomain.com     CNAME    your-loadbalancer.yourdomain.com
ai-stt.yourdomain.com     CNAME    your-loadbalancer.yourdomain.com
ai-tts.yourdomain.com     CNAME    your-loadbalancer.yourdomain.com
ai-vllm.yourdomain.com    CNAME    your-loadbalancer.yourdomain.com
ai.yourdomain.com         CNAME    your-loadbalancer.yourdomain.com
```

### **3. Test External Access**

```bash
# Test from external machine
python3 scripts/test_external_access.py --domain yourdomain.com

# Test with HTTP (for development)
python3 scripts/test_external_access.py --domain yourdomain.com --http
```

## 🌐 **Access Methods**

### **1. External Ingress (Production)**

**Multiple Domains:**
- Main API: `https://ai-api.yourdomain.com`
- STT Service: `https://ai-stt.yourdomain.com`
- TTS Service: `https://ai-tts.yourdomain.com`
- vLLM Service: `https://ai-vllm.yourdomain.com`

**Single Domain with Paths:**
- Main API: `https://ai.yourdomain.com/api`
- STT Service: `https://ai.yourdomain.com/stt`
- TTS Service: `https://ai.yourdomain.com/tts`
- vLLM Service: `https://ai.yourdomain.com/vllm`

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
curl http://LOADBALANCER_IP:80/health
```

### **4. NodePort Services**

```bash
# Get node IP
kubectl get nodes -o wide

# Access via NodePort
curl http://NODE_IP:30001/health  # Main API
curl http://NODE_IP:30002/health  # STT Service
curl http://NODE_IP:30003/health  # TTS Service
curl http://NODE_IP:30000/health  # vLLM Service
```

## 🔧 **Configuration**

### **1. Update Domain Configuration**

Edit the following files to replace `yourdomain.com` with your actual domain:

```bash
# Update ingress configurations
sed -i 's/yourdomain.com/yourdomain.com/g' k8s/ingress-external.yaml
sed -i 's/yourdomain.com/yourdomain.com/g' k8s/certificate.yaml
sed -i 's/yourdomain.com/yourdomain.com/g' k8s/configmap.yaml

# Update email for certificates
sed -i 's/your-email@yourdomain.com/your-email@yourdomain.com/g' k8s/certificate.yaml
```

### **2. Configure Internal DNS**

For intranet access, configure your internal DNS server:

```bash
# Add to your internal DNS server
ai-api.internal     A    YOUR_CLUSTER_IP
ai-stt.internal     A    YOUR_CLUSTER_IP
ai-tts.internal     A    YOUR_CLUSTER_IP
ai-vllm.internal    A    YOUR_CLUSTER_IP
```

### **3. Configure Firewall Rules**

```bash
# Allow HTTP and HTTPS traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow NodePort traffic (if using NodePort)
sudo ufw allow 30000:30003/tcp

# Allow internal traffic
sudo ufw allow from 10.0.0.0/8
sudo ufw allow from 172.16.0.0/12
sudo ufw allow from 192.168.0.0/16
```

## 🧪 **Testing External Access**

### **1. Basic Connectivity Test**

```bash
# Test DNS resolution
nslookup ai-api.yourdomain.com
dig ai-api.yourdomain.com

# Test HTTP connectivity
curl -I https://ai-api.yourdomain.com/health
curl -I https://ai-stt.yourdomain.com/health
curl -I https://ai-tts.yourdomain.com/health
curl -I https://ai-vllm.yourdomain.com/health
```

### **2. API Functionality Test**

```bash
# Test main routing API
curl -X POST https://ai-api.yourdomain.com/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, world!", "modality": "text"}'

# Test STT service
curl -X POST https://ai-stt.yourdomain.com/transcribe \
  -F "file=@audio.wav" \
  -F "language=hi"

# Test TTS service
curl -X POST https://ai-tts.yourdomain.com/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "language": "hi", "gender": "female"}'

# Test vLLM service
curl -X POST https://ai-vllm.yourdomain.com/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "MiniCPM-V-4", "prompt": "Hello", "max_tokens": 10}'
```

### **3. Comprehensive Testing Script**

```bash
# Run comprehensive external access test
python3 scripts/test_external_access.py --domain yourdomain.com

# Test with HTTP (for development)
python3 scripts/test_external_access.py --domain yourdomain.com --http

# Test internal endpoints only
python3 scripts/test_external_access.py --domain yourdomain.com --internal-only
```

## 🔒 **Security Configuration**

### **1. TLS Certificates**

The deployment automatically configures TLS certificates via Let's Encrypt:

```yaml
# Certificate configuration
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ai-infrastructure-tls
spec:
  secretName: ai-infrastructure-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - ai-api.yourdomain.com
  - ai-stt.yourdomain.com
  - ai-tts.yourdomain.com
  - ai-vllm.yourdomain.com
```

### **2. Network Policies**

Network policies restrict traffic to authorized sources:

```yaml
# Network policy for AI services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-infrastructure-netpol
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
    - protocol: TCP
      port: 8001
    - protocol: TCP
      port: 8002
    - protocol: TCP
      port: 8003
```

### **3. CORS Configuration**

CORS is configured to allow cross-origin requests:

```yaml
# CORS annotations
nginx.ingress.kubernetes.io/cors-allow-origin: "*"
nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
nginx.ingress.kubernetes.io/enable-cors: "true"
```

## 📊 **Monitoring External Access**

### **1. Check Service Status**

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

### **2. Monitor Logs**

```bash
# View ingress controller logs
kubectl logs -f deployment/ingress-nginx-controller -n ingress-nginx

# View AI service logs
kubectl logs -f deployment/ai-routing-api -n ai-infrastructure
kubectl logs -f deployment/ai-stt-service -n ai-infrastructure
kubectl logs -f deployment/ai-tts-service -n ai-infrastructure
kubectl logs -f deployment/ai-vllm-service -n ai-infrastructure
```

### **3. Test Endpoints**

```bash
# Test health endpoints
curl https://ai-api.yourdomain.com/health
curl https://ai-stt.yourdomain.com/health
curl https://ai-tts.yourdomain.com/health
curl https://ai-vllm.yourdomain.com/health

# Test performance
curl https://ai-api.yourdomain.com/stats
```

## 🛠️ **Troubleshooting**

### **1. DNS Resolution Issues**

```bash
# Check DNS resolution
nslookup ai-api.yourdomain.com
dig ai-api.yourdomain.com

# Check DNS propagation
dig @8.8.8.8 ai-api.yourdomain.com
dig @1.1.1.1 ai-api.yourdomain.com

# Test from different locations
curl -I https://ai-api.yourdomain.com/health
```

### **2. SSL Certificate Issues**

```bash
# Check certificate status
kubectl describe certificate ai-infrastructure-tls -n ai-infrastructure

# Check certificate issuer
kubectl describe clusterissuer letsencrypt-prod

# Check cert-manager logs
kubectl logs -f deployment/cert-manager -n cert-manager
```

### **3. Ingress Issues**

```bash
# Check ingress status
kubectl describe ingress ai-infrastructure-external -n ai-infrastructure

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -f deployment/ingress-nginx-controller -n ingress-nginx

# Check ingress controller configuration
kubectl get configmap nginx-configuration -n ingress-nginx -o yaml
```

### **4. Service Connectivity Issues**

```bash
# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Check pod readiness
kubectl get pods -n ai-infrastructure -o wide

# Test internal connectivity
kubectl exec -it deployment/ai-routing-api -n ai-infrastructure -- curl http://ai-stt-service:8002/health
```

### **5. Firewall Issues**

```bash
# Check firewall status
sudo ufw status

# Check open ports
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :30000

# Test port connectivity
telnet YOUR_CLUSTER_IP 80
telnet YOUR_CLUSTER_IP 443
telnet YOUR_CLUSTER_IP 30001
```

## 🔄 **Updates and Maintenance**

### **1. Update Configuration**

```bash
# Update ConfigMap
kubectl apply -f k8s/configmap.yaml

# Restart deployments
kubectl rollout restart deployment -n ai-infrastructure
```

### **2. Scale Services**

```bash
# Scale routing API
kubectl scale deployment ai-routing-api --replicas=3 -n ai-infrastructure

# Scale STT service
kubectl scale deployment ai-stt-service --replicas=2 -n ai-infrastructure
```

### **3. Update Certificates**

```bash
# Force certificate renewal
kubectl delete certificate ai-infrastructure-tls -n ai-infrastructure
kubectl apply -f k8s/certificate.yaml
```

## 📚 **Integration Examples**

### **1. Python Client**

```python
import requests

# External access
BASE_URL = "https://ai-api.yourdomain.com"

def query_ai(text, modality="text"):
    response = requests.post(f"{BASE_URL}/route", json={
        "query": text,
        "modality": modality
    })
    return response.json()

# Usage
result = query_ai("Write a Python function to sort a list")
print(result["result"])
```

### **2. JavaScript Client**

```javascript
// External access
const BASE_URL = 'https://ai-api.yourdomain.com';

async function queryAI(text, modality = 'text') {
    const response = await fetch(`${BASE_URL}/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, modality })
    });
    return await response.json();
}

// Usage
const result = await queryAI('Write a Python function to sort a list');
console.log(result.result);
```

### **3. cURL Examples**

```bash
# External access examples
curl -X POST https://ai-api.yourdomain.com/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, world!", "modality": "text"}'

curl -X POST https://ai-stt.yourdomain.com/transcribe \
  -F "file=@audio.wav" \
  -F "language=hi"

curl -X POST https://ai-tts.yourdomain.com/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "language": "hi", "gender": "female"}'
```

## 🎯 **Best Practices**

### **1. Security**

- Use HTTPS in production
- Configure proper CORS policies
- Implement rate limiting
- Use network policies
- Regular security updates

### **2. Performance**

- Use CDN for static content
- Implement caching
- Monitor response times
- Scale services as needed
- Use connection pooling

### **3. Monitoring**

- Set up health checks
- Monitor certificate expiration
- Track API usage
- Set up alerting
- Regular backup

### **4. DNS**

- Use short TTL for testing
- Use longer TTL for production
- Monitor DNS propagation
- Use multiple DNS providers
- Regular DNS health checks

## 🆘 **Support**

For issues and questions:

1. **Check the troubleshooting section** above
2. **Review Kubernetes logs** for errors
3. **Verify DNS configuration** and propagation
4. **Test network connectivity** and firewall rules
5. **Check certificate status** and validity
6. **Monitor ingress controller** logs
7. **Verify service endpoints** and pod readiness

---

**Status**: ✅ **Production Ready**  
**Last Updated**: September 5, 2025  
**Version**: 1.0.0
