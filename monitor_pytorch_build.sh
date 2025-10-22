#!/bin/bash

# PyTorch Build Progress Monitor
# Real-time monitoring of PyTorch compilation with sm_120 support

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_progress() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

# Function to get build progress
get_build_progress() {
    if [ -f "/tmp/pytorch_build.log" ]; then
        # Count total objects built
        local total_objects=$(grep -c "Building.*object\|Linking.*executable\|Linking.*shared" /tmp/pytorch_build.log 2>/dev/null || echo "0")
        
        # Get current phase
        local current_phase="Unknown"
        if grep -q "Cloning PyTorch repository" /tmp/pytorch_build.log; then
            current_phase="Git Clone"
        elif grep -q "Initializing git submodules" /tmp/pytorch_build.log; then
            current_phase="Submodules"
        elif grep -q "Installing build dependencies" /tmp/pytorch_build.log; then
            current_phase="Dependencies"
        elif grep -q "Building PyTorch" /tmp/pytorch_build.log; then
            current_phase="Compilation"
        elif grep -q "PyTorch build completed successfully" /tmp/pytorch_build.log; then
            current_phase="Completed"
        fi
        
        echo "$total_objects|$current_phase"
    else
        echo "0|No Log"
    fi
}

# Function to check if sm_120 is being built
check_sm120_support() {
    if [ -f "/tmp/pytorch_build.log" ]; then
        if grep -q "compute_120,code=sm_120" /tmp/pytorch_build.log; then
            echo "✅ sm_120 support confirmed"
        else
            echo "❌ sm_120 support not found"
        fi
    else
        echo "❓ sm_120 status unknown"
    fi
}

# Function to get active processes
get_active_processes() {
    local processes=$(docker exec ai-wan-service ps aux | grep -E "(python|git|cmake|make)" | grep -v grep | wc -l 2>/dev/null || echo "0")
    echo "$processes"
}

# Function to get build size
get_build_size() {
    if [ -d "/tmp/pytorch" ]; then
        local size=$(docker exec ai-wan-service du -sh /tmp/pytorch/ 2>/dev/null | cut -f1 || echo "0")
        echo "$size"
    else
        echo "0"
    fi
}

# Function to estimate time remaining
estimate_time_remaining() {
    local total_objects=$(echo "$1" | cut -d'|' -f1)
    local current_phase=$(echo "$1" | cut -d'|' -f2)
    
    case $current_phase in
        "Git Clone"|"Submodules")
            echo "30-45 minutes (submodules)"
            ;;
        "Dependencies")
            echo "10-15 minutes (dependencies)"
            ;;
        "Compilation")
            if [ "$total_objects" -gt 0 ]; then
                local progress=$((total_objects * 100 / 8196))
                local remaining=$((100 - progress))
                echo "~$((remaining * 2)) minutes (compilation)"
            else
                echo "2-3 hours (compilation)"
            fi
            ;;
        "Completed")
            echo "Build complete!"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# Main monitoring loop
monitor_build() {
    print_status "🚀 PyTorch Build Monitor Started"
    print_status "Monitoring build with CUDA 12.8 and sm_120 support"
    echo ""
    
    local last_progress=""
    local last_update=$(date +%s)
    
    while true; do
        clear
        echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${WHITE}║                        PyTorch Build Progress Monitor                        ║${NC}"
        echo -e "${WHITE}║                    CUDA 12.8 + sm_120 Support Build                         ║${NC}"
        echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        # Get current progress
        local progress=$(get_build_progress)
        local total_objects=$(echo "$progress" | cut -d'|' -f1)
        local current_phase=$(echo "$progress" | cut -d'|' -f2)
        local active_processes=$(get_active_processes)
        local build_size=$(get_build_size)
        local sm120_status=$(check_sm120_support)
        local time_remaining=$(estimate_time_remaining "$progress")
        
        # Display progress information
        print_progress "📊 Build Progress: $total_objects objects built"
        print_progress "🔄 Current Phase: $current_phase"
        print_progress "⚡ Active Processes: $active_processes"
        print_progress "💾 Build Size: $build_size"
        print_progress "🎯 GPU Support: $sm120_status"
        print_progress "⏱️  Estimated Time Remaining: $time_remaining"
        echo ""
        
        # Show recent log entries
        print_status "📝 Recent Build Activity:"
        if [ -f "/tmp/pytorch_build.log" ]; then
            docker exec ai-wan-service tail -5 /tmp/pytorch_build.log 2>/dev/null | while read line; do
                echo -e "${CYAN}  $line${NC}"
            done
        else
            print_warning "  No build log found"
        fi
        echo ""
        
        # Check for completion
        if [ "$current_phase" = "Completed" ]; then
            print_success "🎉 PyTorch build completed successfully!"
            print_success "✅ sm_120 support is now available for RTX 5090/RTX PRO 6000"
            break
        fi
        
        # Check for errors
        if [ -f "/tmp/pytorch_build.log" ]; then
            if docker exec ai-wan-service grep -q "ERROR\|Failed\|error:" /tmp/pytorch_build.log 2>/dev/null; then
                print_error "❌ Build errors detected! Check the log for details."
                echo ""
                print_error "Recent errors:"
                docker exec ai-wan-service grep -i "error\|failed" /tmp/pytorch_build.log | tail -3 2>/dev/null | while read line; do
                    echo -e "${RED}  $line${NC}"
                done
            fi
        fi
        
        echo ""
        print_status "Press Ctrl+C to stop monitoring"
        print_status "Last updated: $(date '+%H:%M:%S')"
        
        # Update every 10 seconds
        sleep 10
    done
}

# Function to show build summary
show_summary() {
    echo ""
    echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║                            Build Summary                                    ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ -f "/tmp/pytorch_build.log" ]; then
        local start_time=$(docker exec ai-wan-service head -1 /tmp/pytorch_build.log 2>/dev/null | grep -o '[0-9][0-9]:[0-9][0-9]:[0-9][0-9]' | head -1)
        local end_time=$(docker exec ai-wan-service tail -1 /tmp/pytorch_build.log 2>/dev/null | grep -o '[0-9][0-9]:[0-9][0-9]:[0-9][0-9]' | head -1)
        
        print_status "Build started: $start_time"
        print_status "Build ended: $end_time"
        print_status "Total objects built: $(grep -c "Building.*object\|Linking.*executable\|Linking.*shared" /tmp/pytorch_build.log 2>/dev/null || echo "0")"
        print_status "sm_120 support: $(check_sm120_support)"
    fi
}

# Main execution
case "${1:-monitor}" in
    "monitor")
        monitor_build
        show_summary
        ;;
    "status")
        progress=$(get_build_progress)
        total_objects=$(echo "$progress" | cut -d'|' -f1)
        current_phase=$(echo "$progress" | cut -d'|' -f2)
        print_status "Current progress: $total_objects objects built"
        print_status "Current phase: $current_phase"
        print_status "sm_120 support: $(check_sm120_support)"
        ;;
    "log")
        if [ -f "/tmp/pytorch_build.log" ]; then
            docker exec ai-wan-service tail -20 /tmp/pytorch_build.log
        else
            print_error "Build log not found"
        fi
        ;;
    "help")
        echo "Usage: $0 [monitor|status|log|help]"
        echo "  monitor - Real-time monitoring (default)"
        echo "  status  - Quick status check"
        echo "  log     - Show recent build log"
        echo "  help    - Show this help"
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac


