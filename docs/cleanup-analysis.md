# Cleanup Analysis: Outdated Files and Scripts

## 🎯 **CURRENT SETUP STATUS**

**Active System**: vLLM with Smart Bypass Optimization
- **Primary**: `docker-compose-realtime.yml` (Real-time optimized)
- **Secondary**: `docker-compose.yml` (Standard deployment)
- **API**: Real-time routing API with smart bypass
- **Models**: vLLM-compatible models only

## 📋 **OUTDATED FILES IDENTIFIED**

### **1. TRITON INFERENCE SERVER (Completely Replaced)**

#### **Files to Archive:**
- `README-triton-inference.md` - Complete Triton documentation
- `quick_triton_test.py` - Triton testing script
- `docs/feature/vllm-inference-server/` - Entire directory (Triton investigation)
  - `cleanup-summary.md`
  - `scratchpad.md` 
  - `vllm-investigation-findings.md`

#### **Reason**: Triton was completely replaced by vLLM community image

### **2. CUSTOM vLLM BUILD (Replaced by Community Image)**

#### **Files to Archive:**
- `Dockerfile.vllm` - Custom vLLM build (failed with std::bad_alloc)
- `Dockerfile.vllm-build` - Build environment
- `Dockerfile.vllm-build-env` - Build environment variant
- `Dockerfile.vllm-runtime` - Runtime environment
- `scripts/build-vllm.sh` - Custom build script

#### **Reason**: Custom build failed, using community image `vllm/vllm-openai:latest`

### **3. OLD TESTING SCRIPTS (Superseded)**

#### **Files to Archive:**
- `comprehensive_use_case_tests.py` - Old comprehensive test (Triton-based)
- `quick_inference_test.py` - Generic inference test
- `test_phi2_inference.py` - Single model test
- `test_vllm_inference.py` - Basic vLLM test
- `scripts/test_all_models_vllm.py` - Old model testing

#### **Reason**: Replaced by `scripts/test_smart_bypass.py` and `scripts/test_vllm_compatible_models.py`

### **4. OLD DOCUMENTATION (Superseded)**

#### **Files to Archive:**
- `docs/centralized-model-management.md` - Old model management approach
- `docs/complete-use-case-summary.md` - Outdated use case summary
- `docs/gpu-server-architecture.md` - Old architecture
- `docs/gpu-server-infrastructure-summary.md` - Old infrastructure
- `docs/gpu-server-status-tracker.md` - Old status tracking
- `docs/performance-comparison-analysis.md` - Old performance analysis
- `docs/use-case-implementation-guide.md` - Old implementation guide
- `docs/README.md` - Duplicate README

#### **Reason**: Superseded by current vLLM documentation in `docs/feature/vllm-blackwell-gpu-setup/`

### **5. OLD SCRIPTS (Superseded)**

#### **Files to Archive:**
- `scripts/download_model.py` - Old single model download
- `scripts/download_vllm_models.py` - Old vLLM model download
- `scripts/download-models-docker.sh` - Old Docker download script
- `scripts/manage-ai-models.sh` - Old model management
- `scripts/manage-ai-models-extended.sh` - Extended old management
- `scripts/docker-test-runner.sh` - Old Docker testing
- `scripts/verify-dockerization.sh` - Old verification script

#### **Reason**: Replaced by `scripts/download_all_use_case_models.py` and current testing scripts

### **6. DUPLICATE MONITORING (Redundant)**

#### **Files to Archive:**
- `monitoring/` - Entire directory (duplicate of `grafana/` and `prometheus/`)

#### **Reason**: Duplicate of `grafana/` and `prometheus/` directories

### **7. OLD API (Superseded)**

#### **Files to Archive:**
- `src/api/routing_api.py` - Old routing API (superseded by realtime_routing_api.py)

#### **Reason**: Replaced by `src/api/realtime_routing_api.py` with smart bypass

## 📊 **CLEANUP SUMMARY**

### **Files to Archive: 25+ files**
- **Triton-related**: 4 files
- **Custom vLLM build**: 5 files  
- **Old testing**: 5 files
- **Old documentation**: 8 files
- **Old scripts**: 7 files
- **Duplicate monitoring**: 1 directory
- **Old API**: 1 file

### **Space Savings**: ~2-3MB of code and documentation

### **Maintenance Benefits**:
- Eliminates confusion about which files are current
- Reduces repository size
- Improves documentation clarity
- Focuses on current vLLM + Smart Bypass system

## 🎯 **CURRENT ACTIVE FILES**

### **Core System:**
- `docker-compose-realtime.yml` - **Primary deployment**
- `docker-compose.yml` - **Secondary deployment**
- `Dockerfile.routing` - **Routing API container**

### **Current Scripts:**
- `scripts/download_all_use_case_models.py` - **Model download**
- `scripts/test_smart_bypass.py` - **Smart bypass testing**
- `scripts/test_vllm_compatible_models.py` - **Model compatibility testing**
- `scripts/test_routing_system.py` - **Routing system testing**

### **Current Documentation:**
- `docs/feature/vllm-blackwell-gpu-setup/` - **All current documentation**
- `README.md` - **Updated main documentation**

### **Current Source Code:**
- `src/routing/` - **All routing components**
- `src/api/realtime_routing_api.py` - **Current API**
- `src/config/model_registry.yaml` - **Model configuration**

## ✅ **RECOMMENDATION**

**Archive all identified outdated files** to maintain a clean, focused repository that clearly represents the current vLLM + Smart Bypass system.
