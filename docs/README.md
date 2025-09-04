# GPU Server Infrastructure Documentation

## Overview

This documentation provides comprehensive information about the GPU server infrastructure setup, architecture, current status, and operational procedures. The GPU server is a high-performance compute node within the Kubernetes cluster, equipped with NVIDIA GPUs for AI/ML workloads.

## Documentation Structure

### 📋 [GPU Server Infrastructure Summary](./gpu-server-infrastructure-summary.md)
**Comprehensive overview of the current GPU server setup**

- **System Information**: Hardware specifications, OS details, and resource allocation
- **Software Stack**: NVIDIA drivers, container runtime, and Kubernetes configuration
- **Infrastructure Components**: GPU monitoring, protection services, and management tools
- **Current Issues**: Identified problems and their impact on operations
- **Recommendations**: Actionable steps for improvement and optimization

**Use this document for**: Understanding the overall infrastructure state, identifying current issues, and planning improvements.

---

### 🏗️ [GPU Server Technical Architecture](./gpu-server-architecture.md)
**Detailed technical architecture and component relationships**

- **Architecture Overview**: Layered system design with hardware abstraction
- **Component Details**: In-depth analysis of each infrastructure layer
- **Data Flow**: Resource allocation, monitoring, and temperature management flows
- **Security Architecture**: Container and system security considerations
- **Performance Architecture**: Optimization strategies and best practices

**Use this document for**: Understanding system design, planning modifications, and troubleshooting architectural issues.

---

### 📊 [GPU Server Status Tracker](./gpu-server-status-tracker.md)
**Real-time status monitoring and issue tracking**

- **Current Status**: Overall infrastructure health and operational state
- **Active Issues**: Critical problems requiring immediate attention
- **Service Status**: System services, containers, and GPU hardware status
- **Configuration Status**: CDI, Kubernetes, and NVIDIA driver configuration
- **Next Actions**: Prioritized action items and timelines

**Use this document for**: Daily operations, issue tracking, and progress monitoring.

---

### 🤖 [Centralized AI Model Management](./centralized-model-management.md)
**Comprehensive guide to centralized model storage and management**

- **Model Storage**: Centralized location at `/opt/ai-models` for persistent access
- **Model Organization**: Categorized storage by model family and type
- **Management Tools**: Scripts for downloading, organizing, and maintaining models
- **Docker Integration**: Volume mounting and environment variable configuration
- **Best Practices**: Security, backup, and maintenance procedures

**Use this document for**: Setting up model storage, downloading models, and managing the model lifecycle.

---

## Quick Reference

### Current Infrastructure Status
- **Overall Status**: 🟡 Partially Operational
- **Hardware**: 🟢 Fully Operational (2 GPUs, 64 cores, 263GB RAM)
- **Kubernetes Integration**: 🔴 Requires Attention
- **Monitoring**: 🟢 Fully Operational

### Critical Issues
1. **GPU Resources Not Available**: GPUs not showing in Kubernetes
2. **Node Scheduling Disabled**: No new workloads can be scheduled
3. **Device Plugin Missing**: NVIDIA device plugin not deployed

### Immediate Actions Required
1. Deploy NVIDIA device plugin
2. Investigate node scheduling restrictions
3. Validate GPU resource discovery

### AI Model Management
- **Centralized Storage**: `/opt/ai-models` for persistent model access
- **Model Organization**: Categorized by family (llama2, mistral, codellama, phi, qwen)
- **Management Scripts**: `scripts/manage-ai-models.sh` for model operations

## Hardware Specifications

### GPU Configuration
| GPU | Model | Memory | Power | Status |
|-----|-------|---------|-------|---------|
| GPU 0 | NVIDIA GeForce RTX 5090 | 32GB GDDR7 | 575W | Healthy |
| GPU 1 | NVIDIA RTX PRO 6000 Black | 96GB GDDR6 | 600W | Healthy |

### System Resources
- **CPU**: 64 cores (x86_64)
- **Memory**: 263GB RAM
- **Storage**: 412TB ephemeral storage
- **Network**: 1Gbps+ connectivity

## Software Stack

### Core Components
- **OS**: Ubuntu 24.04.3 LTS
- **Kernel**: 6.8.0-79-generic
- **NVIDIA Driver**: 575.64.03
- **CUDA**: 12.9
- **Kubernetes**: K3s v1.33.3+k3s1
- **Container Runtime**: Docker 28.3.3 + containerd 2.0.5-k3s2

### Key Services
- **GPU Temperature Guardian**: Temperature monitoring and protection
- **GPU Fan Control**: Dynamic fan speed management
- **Emergency Cooling**: Hardware protection protocols
- **DCGM Exporter**: GPU metrics collection

## Operational Procedures

### Daily Operations
1. **Health Check**: Verify GPU status and service health
2. **Temperature Monitor**: Check GPU temperatures and fan operation
3. **Resource Usage**: Monitor GPU utilization and memory usage
4. **Service Status**: Verify all system services are running

### Issue Resolution
1. **Identify Issue**: Use status tracker to identify current problems
2. **Assess Impact**: Determine severity and affected components
3. **Execute Resolution**: Follow documented procedures for each issue type
4. **Verify Fix**: Confirm resolution and update status tracker

### Maintenance Procedures
1. **Regular Testing**: Run GPU stress tests and validation
2. **Performance Monitoring**: Track performance metrics and trends
3. **Configuration Updates**: Apply security patches and updates
4. **Backup Procedures**: Backup critical configurations and data

## Monitoring & Alerting

### Key Metrics
- **GPU Temperature**: Real-time monitoring with 75°C threshold
- **GPU Utilization**: Compute and memory usage tracking
- **Power Consumption**: Dynamic power monitoring
- **Service Health**: System service status and performance

### Alerting
- **Temperature Alerts**: Automatic workload termination on threshold breach
- **Performance Alerts**: GPU utilization and performance issues
- **Health Alerts**: Service failures and recovery events
- **Capacity Alerts**: Resource exhaustion and scaling needs

## Troubleshooting Guide

### Common Issues

#### GPU Not Visible in Kubernetes
- **Symptoms**: `nvidia.com/gpu: 0` in node description
- **Causes**: Device plugin not deployed, CDI configuration issues
- **Solutions**: Deploy NVIDIA device plugin, verify CDI setup

#### Node Scheduling Disabled
- **Symptoms**: Node shows `SchedulingDisabled` status
- **Causes**: Taints, node conditions, or policy restrictions
- **Solutions**: Check node taints, resolve conditions, verify policies

#### High GPU Temperature
- **Symptoms**: Temperature above 75°C, automatic workload termination
- **Causes**: High utilization, cooling system issues, ambient temperature
- **Solutions**: Check fan operation, reduce workload, improve cooling

### Diagnostic Commands
```bash
# Check GPU status
nvidia-smi

# Verify Kubernetes node status
kubectl describe node gpu-server

# Check service status
systemctl status gpu-temperature-guardian

# Monitor GPU metrics
curl localhost:9400/metrics
```

## Contact Information

### Support Team
- **Infrastructure Team**: Primary support for GPU server issues
- **System Administrator**: Escalation contact for critical issues
- **Documentation Owner**: Infrastructure Team

### Review Schedule
- **Active Issues**: Daily review and status updates
- **Stable Operation**: Weekly review and health checks
- **Documentation**: Monthly review and updates

## Document Maintenance

### Version Control
- **Current Version**: 1.0
- **Last Updated**: September 2, 2025
- **Next Review**: September 3, 2025

### Update Process
1. **Review Changes**: Assess infrastructure modifications
2. **Update Documents**: Modify relevant documentation
3. **Version Control**: Update version numbers and dates
4. **Team Review**: Validate changes with infrastructure team

---

**For questions or updates to this documentation, please contact the Infrastructure Team.**

**Last Updated**: September 2, 2025  
**Document Version**: 1.0  
**Infrastructure Status**: Partially Operational
