#!/bin/bash

# Real-time PyTorch Build Monitor
# Simple script to watch build progress

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
NC='\033[0m'

while true; do
    clear
    echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║                        PyTorch Build Progress Monitor                        ║${NC}"
    echo -e "${WHITE}║                    CUDA 12.8 + sm_120 Support Build                         ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Get current progress
    local objects_built=$(docker exec ai-wan-service grep -c "Building.*object\|Linking.*executable\|Linking.*shared" /tmp/pytorch_build.log 2>/dev/null || echo "0")
    local total_objects="8196"
    local progress_percent=$((objects_built * 100 / total_objects))
    local active_processes=$(docker exec ai-wan-service ps aux | grep -E "(python|git|cmake|make)" | grep -v grep | wc -l)
    local build_size=$(docker exec ai-wan-service du -sh /tmp/pytorch/ 2>/dev/null | cut -f1 || echo "0")
    
    # Display progress
    echo -e "${BLUE}📊 Progress: $objects_built/$total_objects objects built ($progress_percent%)${NC}"
    echo -e "${BLUE}⚡ Active Processes: $active_processes${NC}"
    echo -e "${BLUE}💾 Build Size: $build_size${NC}"
    echo ""
    
    # Check for completion
    if docker exec ai-wan-service grep -q "PyTorch build completed successfully" /tmp/pytorch_build.log 2>/dev/null; then
        echo -e "${GREEN}🎉 BUILD COMPLETED SUCCESSFULLY! 🎉${NC}"
        echo -e "${GREEN}✅ sm_120 support is now available for RTX 5090/RTX PRO 6000${NC}"
        break
    fi
    
    # Check for errors
    if docker exec ai-wan-service grep -q "ERROR\|Failed\|error:" /tmp/pytorch_build.log 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Build errors detected!${NC}"
        echo ""
        echo -e "${YELLOW}Recent errors:${NC}"
        docker exec ai-wan-service grep -i "error\|failed" /tmp/pytorch_build.log | tail -3 2>/dev/null
    fi
    
    # Show recent activity
    echo -e "${GREEN}📝 Recent Activity:${NC}"
    docker exec ai-wan-service tail -5 /tmp/pytorch_build.log 2>/dev/null | while read line; do
        echo -e "${WHITE}  $line${NC}"
    done
    
    echo ""
    echo -e "${GREEN}Last updated: $(date '+%H:%M:%S')${NC}"
    echo -e "${GREEN}Press Ctrl+C to stop monitoring${NC}"
    
    sleep 10
done


