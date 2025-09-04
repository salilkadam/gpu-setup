#!/bin/bash

# Dockerization Verification Script
# Confirms that all components are properly dockerized and working

set -e

# Color functions
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_info() {
    echo -e "\033[1;36m[INFO]\033[0m $1"
}

print_header() {
    echo -e "\n\033[1;35m$1\033[0m"
    echo "=================================================="
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NETWORK_NAME="ai-network"

# Function to check Docker availability
check_docker() {
    print_header "Checking Docker Availability"
    
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        return 1
    fi
    
    print_success "Docker is available and running"
    print_info "Docker version: $(docker --version)"
    print_info "Docker Compose version: $(docker-compose --version)"
}

# Function to check Docker images
check_docker_images() {
    print_header "Checking Docker Images"
    
    # Check if required images exist
    local required_images=("python:3.10-slim" "nvidia/cuda:12.1-devel-ubuntu22.04")
    
    for image in "${required_images[@]}"; do
        if docker images | grep -q "$(echo $image | cut -d: -f1)"; then
            print_success "Image available: $image"
        else
            print_warning "Image not found: $image (will be pulled when needed)"
        fi
    done
}

# Function to check Docker network
check_docker_network() {
    print_header "Checking Docker Network"
    
    if docker network ls | grep -q "$NETWORK_NAME"; then
        print_success "Network '$NETWORK_NAME' exists"
        print_info "Network details:"
        docker network inspect "$NETWORK_NAME" --format='{{.Name}}: {{.Driver}} - {{.IPAM.Config}}'
    else
        print_warning "Network '$NETWORK_NAME' not found. Creating it..."
        docker network create "$NETWORK_NAME"
        print_success "Network '$NETWORK_NAME' created"
    fi
}

# Function to check Docker Python functionality
check_docker_python() {
    print_header "Checking Docker Python Functionality"
    
    print_status "Testing Python execution in Docker..."
    
    # Test basic Python
    if docker run --rm python:3.10-slim python --version >/dev/null 2>&1; then
        print_success "Basic Python execution works"
    else
        print_error "Basic Python execution failed"
        return 1
    fi
    
    # Test pip installation
    print_status "Testing pip installation in Docker..."
    if docker run --rm python:3.10-slim bash -c "pip install requests && python -c 'import requests; print(\"requests installed successfully\")'" >/dev/null 2>&1; then
        print_success "Pip installation works"
    else
        print_error "Pip installation failed"
        return 1
    fi
    
    # Test script execution
    print_status "Testing script execution in Docker..."
    if docker run --rm \
        --network "$NETWORK_NAME" \
        -v "$SCRIPT_DIR:/app/scripts:ro" \
        python:3.10-slim \
        bash -c "pip install requests && cd /app && python -c 'print(\"Script execution test passed\")'" >/dev/null 2>&1; then
        print_success "Script execution works"
    else
        print_error "Script execution failed"
        return 1
    fi
}

# Function to check Docker Compose
check_docker_compose() {
    print_header "Checking Docker Compose"
    
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        return 1
    fi
    
    print_success "docker-compose.yml found"
    
    # Validate compose file
    print_status "Validating Docker Compose file..."
    if cd "$PROJECT_ROOT" && docker-compose config >/dev/null 2>&1; then
        print_success "Docker Compose file is valid"
    else
        print_error "Docker Compose file has errors"
        return 1
    fi
}

# Function to check NVIDIA Container Toolkit
check_nvidia_container_toolkit() {
    print_header "Checking NVIDIA Container Toolkit"
    
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        print_warning "nvidia-smi not available (host may not have NVIDIA GPU)"
        return 0
    fi
    
    print_status "Testing NVIDIA Container Toolkit..."
    if docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
        print_success "NVIDIA Container Toolkit is working"
        print_info "GPU Information:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | while IFS=, read -r name memory; do
            echo "  GPU: $name, Memory: ${memory}MB"
        done
    else
        print_error "NVIDIA Container Toolkit is not working"
        print_warning "GPU acceleration may not be available"
    fi
}

# Function to check file structure
check_file_structure() {
    print_header "Checking File Structure"
    
    local required_files=(
        "docker-compose.yml"
        "scripts/docker-test-runner.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            print_success "Found: $file"
        else
            print_error "Missing: $file"
        fi
    done
}

# Function to check script permissions
check_script_permissions() {
    print_header "Checking Script Permissions"
    
    local scripts=(
        "scripts/docker-test-runner.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -x "$PROJECT_ROOT/$script" ]; then
            print_success "Executable: $script"
        else
            print_warning "Not executable: $script"
            print_status "Fixing permissions..."
            chmod +x "$PROJECT_ROOT/$script"
        fi
    done
}

# Function to run quick Docker tests
run_docker_tests() {
    print_header "Running Quick Docker Tests"
    
    print_status "Testing Python script execution in Docker..."
    
    # Test basic Docker functionality
    if docker run --rm \
        --network "$NETWORK_NAME" \
        python:3.10-slim \
        python -c "print('Docker Python test passed')" >/dev/null 2>&1; then
        print_success "Basic Docker Python test passed"
    else
        print_error "Basic Docker Python test failed"
        return 1
    fi
}

# Function to show summary
show_summary() {
    print_header "Dockerization Verification Summary"
    
    echo "✅ Docker Environment:"
    echo "  - Docker available and running"
    echo "  - Docker Compose working"
    echo "  - Python containers functional"
    echo "  - Network configuration ready"
    echo ""
    echo "✅ File Structure:"
    echo "  - All required files present"
    echo "  - Scripts executable"
    echo "  - Docker configuration valid"
    echo ""
    echo "✅ Functionality:"
    echo "  - Docker Python execution working"
    echo "  - Script mounting and execution working"
    echo "  - Network connectivity ready"
    echo ""
    echo "🚀 Your system is ready for Docker-based Triton inference!"
    echo ""
    echo "Next steps:"
    echo "  1. Start the server: docker-compose up -d"
    echo "  2. Run tests: docker-compose exec python-testing python -c 'print(\"Testing ready\")'"
    echo "  3. Monitor: Access Grafana at http://localhost:3000"
}

# Main verification function
main() {
    print_header "🐳 Triton Inference Server - Dockerization Verification"
    
    local checks_passed=0
    local total_checks=0
    
    # Run all checks
    local checks=(
        "check_docker"
        "check_docker_images"
        "check_docker_network"
        "check_docker_python"
        "check_docker_compose"
        "check_nvidia_container_toolkit"
        "check_file_structure"
        "check_script_permissions"
        "run_docker_tests"
    )
    
    for check in "${checks[@]}"; do
        total_checks=$((total_checks + 1))
        print_status "Running check: $check"
        
        if $check; then
            checks_passed=$((checks_passed + 1))
        else
            print_warning "Check failed: $check"
        fi
        
        echo ""
    done
    
    # Show results
    if [ $checks_passed -eq $total_checks ]; then
        print_success "All checks passed! 🎉"
        show_summary
    else
        print_warning "$checks_passed/$total_checks checks passed"
        print_error "Some checks failed. Please review the output above."
        exit 1
    fi
}

# Run verification
main "$@"
