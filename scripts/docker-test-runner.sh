#!/bin/bash

# Docker Test Runner for vLLM Inference Server
# Runs all tests in Docker containers without requiring local Python installation

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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
NETWORK_NAME="ai-network"

# Create test results directory
mkdir -p "$TEST_RESULTS_DIR"

# Function to check if Docker network exists
check_network() {
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        print_warning "Docker network '$NETWORK_NAME' not found. Creating it..."
        docker network create "$NETWORK_NAME"
        print_success "Network '$NETWORK_NAME' created"
    fi
}

# Function to run Python script in Docker
run_python_in_docker() {
    local script_name="$1"
    local args="${@:2}"
    
    print_status "Running $script_name in Docker with args: $args"
    
    docker run --rm \
        --network "$NETWORK_NAME" \
        -v "$SCRIPT_DIR:/app/scripts:ro" \
        -v "$TEST_RESULTS_DIR:/app/test-results" \
        -e MODELS_DIR=/opt/ai-models \
        -e CACHE_DIR=/opt/ai-models/cache \
        python:3.10-slim \
        bash -c "
            pip install requests pytest && 
            cd /app && 
            python scripts/$script_name $args
        "
}

# Function to run health tests
run_health_tests() {
    print_status "Running health tests..."
    
    # Check if inference server is running
    if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_error "Inference server is not running. Please start it first."
        return 1
    fi
    
    run_python_in_docker "test-inference-server.py" "health"
    print_success "Health tests completed"
}

# Function to run model tests
run_model_tests() {
    print_status "Running model tests..."
    run_python_in_docker "test-inference-server.py" "models"
    print_success "Model tests completed"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_status "Running comprehensive tests..."
    run_python_in_docker "test-inference-server.py" "comprehensive"
    print_success "Comprehensive tests completed"
}

# Function to run demo
run_demo() {
    print_status "Running demo..."
    run_python_in_docker "demo-inference-server.py" "full"
    print_success "Demo completed"
}

# Function to run specific test
run_specific_test() {
    local test_type="$1"
    
    case "$test_type" in
        health)
            run_health_tests
            ;;
        models)
            run_model_tests
            ;;
        comprehensive)
            run_comprehensive_tests
            ;;
        demo)
            run_demo
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_info "Available test types: health, models, comprehensive, demo"
            exit 1
            ;;
    esac
}

# Function to run all tests
run_all_tests() {
    print_status "Running all tests..."
    
    local tests=("health" "models" "comprehensive" "demo")
    local failed_tests=()
    
    for test in "${tests[@]}"; do
        print_status "Running $test test..."
        if run_specific_test "$test"; then
            print_success "$test test passed"
        else
            print_error "$test test failed"
            failed_tests+=("$test")
        fi
        echo ""
    done
    
    # Summary
    if [ ${#failed_tests[@]} -eq 0 ]; then
        print_success "All tests passed! 🎉"
    else
        print_error "Some tests failed: ${failed_tests[*]}"
        exit 1
    fi
}

# Function to run custom Python script
run_custom_script() {
    local script_name="$1"
    local args="${@:2}"
    
    if [ ! -f "$SCRIPT_DIR/$script_name" ]; then
        print_error "Script not found: $script_name"
        exit 1
    fi
    
    print_status "Running custom script: $script_name"
    run_python_in_docker "$script_name" "$args"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [ARGS...]"
    echo ""
    echo "Commands:"
    echo "  health                    - Run health tests"
    echo "  models                    - Run model tests"
    echo "  comprehensive            - Run comprehensive tests"
    echo "  demo                     - Run demo"
    echo "  all                      - Run all tests"
    echo "  custom <script> [args]   - Run custom Python script"
    echo "  help                     - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 health                # Run health tests"
    echo "  $0 models                # Run model tests"
    echo "  $0 comprehensive         # Run comprehensive tests"
    echo "  $0 demo                  # Run demo"
    echo "  $0 all                   # Run all tests"
    echo "  $0 custom test-inference-server.py health  # Run custom script"
    echo ""
    echo "Note: All tests run in Docker containers. No local Python required."
}

# Main script logic
main() {
    # Check if Docker is available
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Ensure network exists
    check_network
    
    case "${1:-help}" in
        health)
            run_health_tests
            ;;
        models)
            run_model_tests
            ;;
        comprehensive)
            run_comprehensive_tests
            ;;
        demo)
            run_demo
            ;;
        all)
            run_all_tests
            ;;
        custom)
            if [ -z "$2" ]; then
                print_error "Please specify script name for custom command"
                exit 1
            fi
            run_custom_script "${@:2}"
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"
