#!/bin/bash

# Wan Video Generation Setup Script
# This script sets up the Wan video generation service with all necessary components

set -e

echo "🎬 Setting up Wan Video Generation Service..."
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Docker is installed and running
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is installed and running"

# Check if Docker Compose is available
print_status "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

print_success "Docker Compose is available"

# Check if NVIDIA Docker runtime is available
print_status "Checking NVIDIA Docker runtime..."
if ! docker info | grep -q nvidia; then
    print_warning "NVIDIA Docker runtime not detected. GPU acceleration may not work."
    print_warning "Please install nvidia-docker2 for GPU support."
fi

# Create necessary directories
print_status "Creating necessary directories..."
sudo mkdir -p /opt/ai-models/wan
sudo chown -R $USER:$USER /opt/ai-models

print_success "Directories created"

# Check available disk space
print_status "Checking available disk space..."
AVAILABLE_SPACE=$(df /opt | tail -1 | awk '{print $4}')
REQUIRED_SPACE=150000000  # ~150GB in KB

if [ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]; then
    print_warning "Low disk space detected. Wan models require ~150GB of free space."
    print_warning "Available: $(($AVAILABLE_SPACE / 1024 / 1024))GB, Required: ~150GB"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Setup cancelled due to insufficient disk space"
        exit 1
    fi
fi

print_success "Disk space check passed"

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/download_wan_models.py
chmod +x scripts/test_wan_service.py

print_success "Scripts made executable"

# Build Docker images
print_status "Building Docker images..."
if command -v docker-compose &> /dev/null; then
    docker-compose build wan-service
else
    docker compose build wan-service
fi

print_success "Docker images built"

# Start services
print_status "Starting services..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d wan-service
else
    docker compose up -d wan-service
fi

print_success "Services started"

# Wait for service to be ready
print_status "Waiting for Wan service to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
if curl -f http://localhost:8004/health &> /dev/null; then
    print_success "Wan service is healthy"
else
    print_warning "Wan service health check failed. Service may still be starting up."
fi

# Display next steps
echo ""
echo "🎉 Wan Video Generation Service Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Download models:"
echo "   python scripts/download_wan_models.py --list"
echo "   python scripts/download_wan_models.py --model t2v-A14B"
echo ""
echo "2. Test the service:"
echo "   python scripts/test_wan_service.py --test health"
echo "   python scripts/test_wan_service.py --test t2v"
echo ""
echo "3. Access the API:"
echo "   curl http://localhost:8004/health"
echo "   curl http://localhost:8004/models"
echo ""
echo "4. View documentation:"
echo "   cat docs/WAN-INTEGRATION-GUIDE.md"
echo ""
echo "Service URLs:"
echo "- Wan Service: http://localhost:8004"
echo "- API Documentation: http://localhost:8004/docs"
echo ""
echo "Logs:"
echo "- Service logs: docker-compose logs -f wan-service"
echo "- Check status: docker-compose ps"
echo ""

# Check if models are available
print_status "Checking for available models..."
if python3 scripts/download_wan_models.py --installed | grep -q "Total installed: 0"; then
    print_warning "No models are currently installed."
    print_warning "Run 'python scripts/download_wan_models.py --all' to download all models."
    print_warning "Note: This will download ~150GB of model data."
else
    print_success "Some models are already installed"
fi

echo ""
print_success "Setup completed successfully! 🚀"
