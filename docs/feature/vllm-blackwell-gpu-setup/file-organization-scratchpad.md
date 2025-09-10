# File Organization Scratchpad

## Current File Organization Plan

### Root Directory Cleanup
- **Dockerfiles**: Move to `docker/` directory
- **Test Scripts**: Move to `tests/` directory  
- **Configuration Files**: Organize in `config/` directory
- **Documentation**: Keep in `docs/` directory
- **Scripts**: Keep in `scripts/` directory

### File Categories to Organize

#### 1. Dockerfiles (Move to `docker/`)
- `Dockerfile.audio` → `docker/Dockerfile.audio`
- `Dockerfile.image-test` → `docker/Dockerfile.image-test`
- `Dockerfile.model-downloader` → `docker/Dockerfile.model-downloader`
- `Dockerfile.routing` → `docker/Dockerfile.routing`
- `Dockerfile.test` → `docker/Dockerfile.test`
- `Dockerfile.video-test` → `docker/Dockerfile.video-test`
- `Dockerfile.vllm-test` → `docker/Dockerfile.vllm-test`

#### 2. Test Scripts (Move to `tests/`)
- `test_image_processing.py` → `tests/integration/test_image_processing.py`
- `test_real_llm_responses.py` → `tests/integration/test_real_llm_responses.py`
- `test_video_processing.py` → `tests/integration/test_video_processing.py`
- `test-minicpm-vllm.py` → `tests/integration/test_minicpm_vllm.py`

#### 3. Configuration Files (Move to `config/`)
- `docker-compose.yml` → Keep in root (main compose file)
- `docker-compose-realtime.yml` → Keep in root (alternative compose file)
- `cuda-keyring_1.1-1_all.deb` → `config/cuda-keyring_1.1-1_all.deb`

#### 4. Documentation Files (Move to `docs/`)
- `GPU_SERVER_SETUP_DOCUMENTATION.md` → `docs/GPU_SERVER_SETUP_DOCUMENTATION.md`
- `ssh_fixes.md` → `docs/ssh_fixes.md`
- `SSH_QUICK_REFERENCE.md` → `docs/SSH_QUICK_REFERENCE.md`
- `STORAGE-SETUP.md` → `docs/STORAGE-SETUP.md`

#### 5. Archive Files
- `outdated-files-archive.zip` → `archive/outdated-files-archive.zip`

### Directory Structure After Organization
```
gpu-setup/
├── docker/                    # All Dockerfiles
├── config/                    # Configuration files
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── src/                       # Source code
├── tests/                     # Test files
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── archive/                   # Archived files
├── docker-compose.yml         # Main compose file
├── docker-compose-realtime.yml # Alternative compose file
└── README.md                  # Main documentation
```

## Files to Keep in Root
- `docker-compose.yml` (main compose file)
- `docker-compose-realtime.yml` (alternative compose file)
- `README.md` (main documentation)
- `requirements-*.txt` (Python requirements)

## Files to Archive
- `outdated-files-archive.zip` (already archived)
- Any temporary or test files that are no longer needed

## Notes
- All test results are already in `test-results/` directory
- Source code is already well organized in `src/` directory
- Documentation is already organized in `docs/` directory
- Scripts are already organized in `scripts/` directory

## ✅ COMPLETED ORGANIZATION (2025-09-10)

### Files Successfully Moved:
- **Dockerfiles**: All moved to `docker/` directory
- **Test Scripts**: All moved to `tests/integration/` directory
- **Configuration Files**: Moved to `config/` directory
- **Documentation**: Moved to `docs/` directory
- **Archive Files**: Moved to `archive/` directory

### Current Clean Root Structure:
```
gpu-setup/
├── docker/                    # ✅ All Dockerfiles organized
├── config/                    # ✅ Configuration files
├── docs/                      # ✅ Documentation
├── scripts/                   # ✅ Utility scripts
├── src/                       # ✅ Source code
├── tests/                     # ✅ Test files
│   ├── unit/                  # ✅ Unit tests
│   └── integration/           # ✅ Integration tests
├── archive/                   # ✅ Archived files
├── docker-compose.yml         # ✅ Main compose file
├── docker-compose-realtime.yml # ✅ Alternative compose file
└── README.md                  # ✅ Main documentation
```

### Files in Root (Clean):
- `docker-compose.yml` (main compose file)
- `docker-compose-realtime.yml` (alternative compose file)
- `README.md` (main documentation)
- `requirements-*.txt` (Python requirements)
- Standard directories: `src/`, `scripts/`, `docs/`, `k8s/`, `grafana/`, `prometheus/`, `nginx/`, `logs/`, `test-results/`

**Status**: ✅ FILE ORGANIZATION COMPLETED
