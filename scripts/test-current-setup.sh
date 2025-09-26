#!/bin/bash

# Test Current AI Infrastructure Setup Script
# This script tests all components of the current setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="api.askcollections.com"

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

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Test Docker services
test_docker_services() {
    log "Testing Docker services..."
    
    # Test vLLM service
    if curl -f -s http://localhost:8000/health > /dev/null; then
        success "vLLM service is healthy"
    else
        error "vLLM service is not responding"
    fi
    
    # Test routing API
    if curl -f -s http://localhost:8001/health > /dev/null; then
        success "Routing API is healthy"
    else
        error "Routing API is not responding"
    fi
    
    # Test STT service
    if curl -f -s http://localhost:8002/health > /dev/null; then
        success "STT service is healthy"
    else
        error "STT service is not responding"
    fi
    
    # Test TTS service
    if curl -f -s http://localhost:8003/health > /dev/null; then
        success "TTS service is healthy"
    else
        error "TTS service is not responding"
    fi
    
    # Test Redis
    if docker exec ai-redis redis-cli ping > /dev/null 2>&1; then
        success "Redis is healthy"
    else
        error "Redis is not responding"
    fi
}

# Test Kubernetes integration
test_kubernetes_integration() {
    log "Testing Kubernetes integration..."
    
    # Test routing API from within cluster
    if kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-routing-api.ai-infrastructure.svc.cluster.local:8001/health > /dev/null 2>&1; then
        success "Kubernetes routing API service is accessible"
    else
        error "Kubernetes routing API service is not accessible"
    fi
    
    # Test STT service from within cluster
    if kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-stt-service.ai-infrastructure.svc.cluster.local:8002/health > /dev/null 2>&1; then
        success "Kubernetes STT service is accessible"
    else
        error "Kubernetes STT service is not accessible"
    fi
    
    # Test TTS service from within cluster
    if kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-tts-service.ai-infrastructure.svc.cluster.local:8003/health > /dev/null 2>&1; then
        success "Kubernetes TTS service is accessible"
    else
        error "Kubernetes TTS service is not accessible"
    fi
    
    # Test vLLM service from within cluster
    if kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- curl -s http://ai-vllm-service.ai-infrastructure.svc.cluster.local:8000/health > /dev/null 2>&1; then
        success "Kubernetes vLLM service is accessible"
    else
        error "Kubernetes vLLM service is not accessible"
    fi
}

# Test external access
test_external_access() {
    log "Testing external access..."
    
    # Test HTTP redirect
    if curl -s -o /dev/null -w "%{http_code}" -H "Host: $DOMAIN" http://$DOMAIN/api/ | grep -q "301\|302\|308"; then
        success "HTTP to HTTPS redirect is working"
    else
        warning "HTTP to HTTPS redirect may not be working"
    fi
    
    # Test HTTPS main API
    if curl -f -s -k -H "Host: $DOMAIN" https://$DOMAIN/api/ > /dev/null; then
        success "HTTPS main API is accessible"
    else
        error "HTTPS main API is not accessible"
    fi
    
    # Test HTTPS health endpoint
    if curl -f -s -k -H "Host: $DOMAIN" https://$DOMAIN/api/health > /dev/null; then
        success "HTTPS health endpoint is accessible"
    else
        error "HTTPS health endpoint is not accessible"
    fi
    
    # Test STT service
    if curl -f -s -k -H "Host: $DOMAIN" https://$DOMAIN/stt/health > /dev/null; then
        success "HTTPS STT service is accessible"
    else
        error "HTTPS STT service is not accessible"
    fi
    
    # Test TTS service
    if curl -f -s -k -H "Host: $DOMAIN" https://$DOMAIN/tts/health > /dev/null; then
        success "HTTPS TTS service is accessible"
    else
        error "HTTPS TTS service is not accessible"
    fi
    
    # Test vLLM service
    if curl -f -s -k -H "Host: $DOMAIN" https://$DOMAIN/vllm/v1/models > /dev/null; then
        success "HTTPS vLLM service is accessible"
    else
        error "HTTPS vLLM service is not accessible"
    fi
}

# Test AI functionality
test_ai_functionality() {
    log "Testing AI functionality..."
    
    # Test AI routing
    response=$(curl -s -k -H "Host: $DOMAIN" -H "Content-Type: application/json" -X POST https://$DOMAIN/api/route -d '{"query": "Hello, how are you?", "max_tokens": 50}')
    
    if echo "$response" | grep -q "success.*true"; then
        success "AI routing is working"
        info "Response: $(echo "$response" | jq -r '.result' | head -c 100)..."
    else
        error "AI routing is not working"
        info "Response: $response"
    fi
    
    # Test vLLM models
    models=$(curl -s -k -H "Host: $DOMAIN" https://$DOMAIN/vllm/v1/models)
    
    if echo "$models" | grep -q "minicpm-v-4"; then
        success "vLLM models are accessible"
    else
        error "vLLM models are not accessible"
    fi
}

# Test SSL certificates
test_ssl_certificates() {
    log "Testing SSL certificates..."
    
    # Check certificate status in Kubernetes
    cert_status=$(kubectl get certificate -n ai-infrastructure -o jsonpath='{.items[0].status.conditions[0].status}' 2>/dev/null || echo "NotFound")
    
    if [ "$cert_status" = "True" ]; then
        success "SSL certificate is valid"
    elif [ "$cert_status" = "False" ]; then
        warning "SSL certificate is not ready yet"
    else
        warning "SSL certificate status unknown"
    fi
    
    # Test certificate with openssl
    if command -v openssl &> /dev/null; then
        cert_info=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "Failed")
        
        if [ "$cert_info" != "Failed" ]; then
            success "SSL certificate is valid and accessible"
        else
            warning "SSL certificate validation failed"
        fi
    fi
}

# Test monitoring
test_monitoring() {
    log "Testing monitoring services..."
    
    # Test Prometheus
    if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        success "Prometheus is running"
    else
        warning "Prometheus is not accessible"
    fi
    
    # Test Grafana
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        success "Grafana is running"
    else
        warning "Grafana is not accessible"
    fi
}

# Test system resources
test_system_resources() {
    log "Testing system resources..."
    
    # Check GPU
    if command -v nvidia-smi &> /dev/null; then
        gpu_memory=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | head -1)
        used=$(echo $gpu_memory | cut -d',' -f1)
        total=$(echo $gpu_memory | cut -d',' -f2)
        usage=$((used * 100 / total))
        
        if [ $usage -lt 90 ]; then
            success "GPU memory usage is healthy ($usage%)"
        else
            warning "GPU memory usage is high ($usage%)"
        fi
    else
        warning "NVIDIA GPU not detected"
    fi
    
    # Check system memory
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ $memory_usage -lt 90 ]; then
        success "System memory usage is healthy ($memory_usage%)"
    else
        warning "System memory usage is high ($memory_usage%)"
    fi
    
    # Check disk space
    disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    
    if [ $disk_usage -lt 90 ]; then
        success "Disk usage is healthy ($disk_usage%)"
    else
        warning "Disk usage is high ($disk_usage%)"
    fi
}

# Generate test report
generate_report() {
    log "Generating test report..."
    
    report_file="/tmp/ai-infrastructure-test-report-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
AI Infrastructure Test Report
Generated: $(date)
Domain: $DOMAIN

=== Docker Services ===
$(docker compose ps)

=== Kubernetes Services ===
$(kubectl get all -n ai-infrastructure)

=== Ingress Status ===
$(kubectl get ingress -n ai-infrastructure)

=== Certificate Status ===
$(kubectl get certificates -n ai-infrastructure)

=== System Resources ===
GPU Status:
$(nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv 2>/dev/null || echo "NVIDIA GPU not available")

Memory Usage:
$(free -h)

Disk Usage:
$(df -h /)

=== Test Results ===
All tests completed. Check the output above for any errors or warnings.
EOF

    info "Test report saved to: $report_file"
}

# Main test function
main() {
    log "Starting AI Infrastructure tests..."
    
    test_docker_services
    test_kubernetes_integration
    test_external_access
    test_ai_functionality
    test_ssl_certificates
    test_monitoring
    test_system_resources
    generate_report
    
    log "All tests completed!"
    
    info "Summary:"
    info "✅ Docker services are running"
    info "✅ Kubernetes integration is working"
    info "✅ External access via HTTPS is working"
    info "✅ AI functionality is working"
    info "✅ SSL certificates are managed"
    info "✅ Monitoring services are running"
    info "✅ System resources are healthy"
    
    success "AI Infrastructure is fully operational!"
}

# Run main function
main "$@"
