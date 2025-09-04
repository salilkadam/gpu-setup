"""
Dynamic Model Loading System

This module provides dynamic loading and unloading of models with
hot-swapping capabilities and memory management.
"""

import asyncio
import logging
import time
import subprocess
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import psutil
from pathlib import Path

from .model_router import ModelInfo, BackendType

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model loading status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class ModelState:
    """Current state of a model."""
    model_id: str
    status: ModelStatus
    backend: BackendType
    load_time: Optional[float] = None
    last_used: Optional[float] = None
    memory_usage: Optional[float] = None
    error_message: Optional[str] = None
    health_score: float = 1.0


@dataclass
class LoadingResult:
    """Result of model loading operation."""
    success: bool
    model_id: str
    load_time: float
    memory_usage: float
    error_message: Optional[str] = None
    health_check_passed: bool = False


class DynamicModelLoader:
    """
    Dynamic model loader with hot-swapping capabilities and memory management.
    """
    
    def __init__(self, vllm_base_url: str = "http://localhost:8000"):
        """
        Initialize the dynamic model loader.
        
        Args:
            vllm_base_url: Base URL for vLLM API
        """
        self.vllm_base_url = vllm_base_url
        self.model_states: Dict[str, ModelState] = {}
        self.loading_queue: asyncio.Queue = asyncio.Queue()
        self.memory_manager = MemoryManager()
        self.health_monitor = HealthMonitor()
        self.max_concurrent_models = 3
        self.model_cache_dir = Path("/opt/ai-models/models")
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        asyncio.create_task(self._monitor_model_health())
        asyncio.create_task(self._process_loading_queue())
        asyncio.create_task(self._cleanup_unused_models())
    
    async def load_model(
        self, 
        model_info: ModelInfo, 
        priority: int = 0
    ) -> LoadingResult:
        """
        Load a model dynamically.
        
        Args:
            model_info: Information about the model to load
            priority: Loading priority (higher = more priority)
            
        Returns:
            LoadingResult with loading status and metrics
        """
        model_id = model_info.model_id
        
        # Check if model is already loaded
        if model_id in self.model_states:
            state = self.model_states[model_id]
            if state.status == ModelStatus.LOADED:
                logger.info(f"Model {model_id} is already loaded")
                return LoadingResult(
                    success=True,
                    model_id=model_id,
                    load_time=0.0,
                    memory_usage=state.memory_usage or 0.0,
                    health_check_passed=True
                )
            elif state.status == ModelStatus.LOADING:
                logger.info(f"Model {model_id} is already loading")
                # Wait for loading to complete
                return await self._wait_for_loading(model_id)
        
        # Check memory availability
        if not await self._check_memory_availability(model_info):
            # Try to unload unused models
            await self._free_memory_for_model(model_info)
        
        # Add to loading queue
        await self.loading_queue.put((priority, model_info))
        
        # Wait for loading to complete
        return await self._wait_for_loading(model_id)
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model to free memory.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            True if successfully unloaded, False otherwise
        """
        if model_id not in self.model_states:
            logger.warning(f"Model {model_id} not found in states")
            return False
        
        state = self.model_states[model_id]
        if state.status != ModelStatus.LOADED:
            logger.warning(f"Model {model_id} is not loaded (status: {state.status})")
            return False
        
        try:
            # Update status
            state.status = ModelStatus.UNLOADING
            
            # Unload from backend
            success = await self._unload_from_backend(model_id, state.backend)
            
            if success:
                state.status = ModelStatus.UNLOADED
                state.memory_usage = None
                state.load_time = None
                logger.info(f"Successfully unloaded model {model_id}")
                return True
            else:
                state.status = ModelStatus.ERROR
                state.error_message = "Failed to unload from backend"
                logger.error(f"Failed to unload model {model_id}")
                return False
                
        except Exception as e:
            state.status = ModelStatus.ERROR
            state.error_message = str(e)
            logger.error(f"Error unloading model {model_id}: {e}")
            return False
    
    async def switch_model(
        self, 
        from_model_id: str, 
        to_model_info: ModelInfo
    ) -> LoadingResult:
        """
        Switch from one model to another with hot-swapping.
        
        Args:
            from_model_id: ID of the current model
            to_model_info: Information about the target model
            
        Returns:
            LoadingResult for the new model
        """
        logger.info(f"Switching from {from_model_id} to {to_model_info.model_id}")
        
        # Load the new model first
        load_result = await self.load_model(to_model_info, priority=10)
        
        if load_result.success:
            # Unload the old model
            if from_model_id != to_model_info.model_id:
                await self.unload_model(from_model_id)
            
            logger.info(f"Successfully switched to {to_model_info.model_id}")
        
        return load_result
    
    async def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models."""
        return [
            model_id for model_id, state in self.model_states.items()
            if state.status == ModelStatus.LOADED
        ]
    
    async def get_model_status(self, model_id: str) -> Optional[ModelState]:
        """Get current status of a specific model."""
        return self.model_states.get(model_id)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        loaded_models = await self.get_loaded_models()
        memory_info = self.memory_manager.get_memory_info()
        
        return {
            'loaded_models': loaded_models,
            'total_models': len(self.model_states),
            'memory_usage': memory_info,
            'max_concurrent_models': self.max_concurrent_models,
            'loading_queue_size': self.loading_queue.qsize()
        }
    
    async def _process_loading_queue(self):
        """Process the model loading queue."""
        while True:
            try:
                # Get next item from queue
                priority, model_info = await self.loading_queue.get()
                
                # Check if we can load more models
                loaded_count = len(await self.get_loaded_models())
                if loaded_count >= self.max_concurrent_models:
                    # Unload least recently used model
                    await self._unload_lru_model()
                
                # Load the model
                await self._load_model_internal(model_info)
                
                # Mark task as done
                self.loading_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing loading queue: {e}")
                await asyncio.sleep(1)
    
    async def _load_model_internal(self, model_info: ModelInfo) -> LoadingResult:
        """Internal method to load a model."""
        model_id = model_info.model_id
        start_time = time.time()
        
        try:
            # Initialize model state
            self.model_states[model_id] = ModelState(
                model_id=model_id,
                status=ModelStatus.LOADING,
                backend=model_info.backend
            )
            
            # Load from backend
            success = await self._load_from_backend(model_info)
            
            load_time = time.time() - start_time
            
            if success:
                # Update state
                state = self.model_states[model_id]
                state.status = ModelStatus.LOADED
                state.load_time = load_time
                state.last_used = time.time()
                state.memory_usage = await self._get_model_memory_usage(model_id)
                
                # Run health check
                health_passed = await self.health_monitor.check_model_health(model_id)
                state.health_score = 1.0 if health_passed else 0.5
                
                logger.info(f"Successfully loaded model {model_id} in {load_time:.2f}s")
                
                return LoadingResult(
                    success=True,
                    model_id=model_id,
                    load_time=load_time,
                    memory_usage=state.memory_usage or 0.0,
                    health_check_passed=health_passed
                )
            else:
                # Update state with error
                state = self.model_states[model_id]
                state.status = ModelStatus.ERROR
                state.error_message = "Failed to load from backend"
                
                logger.error(f"Failed to load model {model_id}")
                
                return LoadingResult(
                    success=False,
                    model_id=model_id,
                    load_time=load_time,
                    memory_usage=0.0,
                    error_message="Failed to load from backend"
                )
                
        except Exception as e:
            # Update state with error
            if model_id in self.model_states:
                self.model_states[model_id].status = ModelStatus.ERROR
                self.model_states[model_id].error_message = str(e)
            
            logger.error(f"Error loading model {model_id}: {e}")
            
            return LoadingResult(
                success=False,
                model_id=model_id,
                load_time=time.time() - start_time,
                memory_usage=0.0,
                error_message=str(e)
            )
    
    async def _load_from_backend(self, model_info: ModelInfo) -> bool:
        """Load model from the appropriate backend."""
        if model_info.backend == BackendType.VLLM:
            return await self._load_vllm_model(model_info)
        elif model_info.backend == BackendType.TRANSFORMERS:
            return await self._load_transformers_model(model_info)
        elif model_info.backend == BackendType.CUSTOM:
            return await self._load_custom_model(model_info)
        else:
            logger.error(f"Unsupported backend: {model_info.backend}")
            return False
    
    async def _load_vllm_model(self, model_info: ModelInfo) -> bool:
        """Load model using vLLM backend."""
        try:
            # Check if model path exists
            model_path = self.model_cache_dir / model_info.model_id.replace("/", "-")
            if not model_path.exists():
                logger.error(f"Model path not found: {model_path}")
                return False
            
            # Update docker-compose to load the new model
            await self._update_docker_compose_model(str(model_path))
            
            # Restart vLLM service
            await self._restart_vllm_service()
            
            # Wait for model to load
            await self._wait_for_vllm_ready()
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading vLLM model {model_info.model_id}: {e}")
            return False
    
    async def _load_transformers_model(self, model_info: ModelInfo) -> bool:
        """Load model using Transformers backend."""
        # This would implement Transformers library loading
        # For now, return True as placeholder
        logger.info(f"Loading Transformers model: {model_info.model_id}")
        return True
    
    async def _load_custom_model(self, model_info: ModelInfo) -> bool:
        """Load model using custom backend."""
        # This would implement custom model loading
        # For now, return True as placeholder
        logger.info(f"Loading custom model: {model_info.model_id}")
        return True
    
    async def _unload_from_backend(self, model_id: str, backend: BackendType) -> bool:
        """Unload model from the appropriate backend."""
        if backend == BackendType.VLLM:
            return await self._unload_vllm_model(model_id)
        elif backend == BackendType.TRANSFORMERS:
            return await self._unload_transformers_model(model_id)
        elif backend == BackendType.CUSTOM:
            return await self._unload_custom_model(model_id)
        else:
            logger.error(f"Unsupported backend: {backend}")
            return False
    
    async def _unload_vllm_model(self, model_id: str) -> bool:
        """Unload model from vLLM backend."""
        try:
            # For vLLM, we can't unload individual models without restarting
            # This is a limitation of the current setup
            logger.info(f"vLLM model {model_id} will be unloaded on next restart")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading vLLM model {model_id}: {e}")
            return False
    
    async def _update_docker_compose_model(self, model_path: str):
        """Update docker-compose.yml to load the specified model."""
        try:
            # Read current docker-compose.yml
            with open('docker-compose.yml', 'r') as f:
                content = f.read()
            
            # Update the model path in the command
            import re
            pattern = r'--model\s+/app/models/[^\s]+'
            replacement = f'--model {model_path}'
            updated_content = re.sub(pattern, replacement, content)
            
            # Write back to file
            with open('docker-compose.yml', 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Updated docker-compose.yml to load model: {model_path}")
            
        except Exception as e:
            logger.error(f"Error updating docker-compose.yml: {e}")
            raise
    
    async def _restart_vllm_service(self):
        """Restart the vLLM service."""
        try:
            # Stop vLLM service
            subprocess.run(['docker-compose', 'stop', 'vllm-inference-server'], 
                         check=True, capture_output=True)
            
            # Start vLLM service
            subprocess.run(['docker-compose', 'up', '-d', 'vllm-inference-server'], 
                         check=True, capture_output=True)
            
            logger.info("Restarted vLLM service")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error restarting vLLM service: {e}")
            raise
    
    async def _wait_for_vllm_ready(self, timeout: int = 60):
        """Wait for vLLM service to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.vllm_base_url}/health") as response:
                        if response.status == 200:
                            logger.info("vLLM service is ready")
                            return
                
            except Exception as e:
                logger.debug(f"vLLM not ready yet: {e}")
            
            await asyncio.sleep(2)
        
        raise TimeoutError("vLLM service did not become ready within timeout")
    
    async def _wait_for_loading(self, model_id: str, timeout: int = 120) -> LoadingResult:
        """Wait for a model to finish loading."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if model_id in self.model_states:
                state = self.model_states[model_id]
                
                if state.status == ModelStatus.LOADED:
                    return LoadingResult(
                        success=True,
                        model_id=model_id,
                        load_time=state.load_time or 0.0,
                        memory_usage=state.memory_usage or 0.0,
                        health_check_passed=state.health_score > 0.5
                    )
                elif state.status == ModelStatus.ERROR:
                    return LoadingResult(
                        success=False,
                        model_id=model_id,
                        load_time=time.time() - start_time,
                        memory_usage=0.0,
                        error_message=state.error_message
                    )
            
            await asyncio.sleep(1)
        
        return LoadingResult(
            success=False,
            model_id=model_id,
            load_time=timeout,
            memory_usage=0.0,
            error_message="Loading timeout"
        )
    
    async def _check_memory_availability(self, model_info: ModelInfo) -> bool:
        """Check if there's enough memory to load the model."""
        required_memory = self._parse_memory_requirement(model_info.memory_required)
        available_memory = self.memory_manager.get_available_memory()
        
        return required_memory <= available_memory
    
    async def _free_memory_for_model(self, model_info: ModelInfo):
        """Free memory by unloading unused models."""
        required_memory = self._parse_memory_requirement(model_info.memory_required)
        
        # Get models sorted by last used time
        unused_models = sorted(
            [(model_id, state) for model_id, state in self.model_states.items()
             if state.status == ModelStatus.LOADED],
            key=lambda x: x[1].last_used or 0
        )
        
        freed_memory = 0.0
        for model_id, state in unused_models:
            if freed_memory >= required_memory:
                break
            
            if await self.unload_model(model_id):
                freed_memory += state.memory_usage or 0.0
    
    async def _unload_lru_model(self):
        """Unload the least recently used model."""
        loaded_models = [
            (model_id, state) for model_id, state in self.model_states.items()
            if state.status == ModelStatus.LOADED
        ]
        
        if loaded_models:
            # Sort by last used time
            lru_model = min(loaded_models, key=lambda x: x[1].last_used or 0)
            await self.unload_model(lru_model[0])
    
    async def _monitor_model_health(self):
        """Monitor health of loaded models."""
        while True:
            try:
                for model_id, state in self.model_states.items():
                    if state.status == ModelStatus.LOADED:
                        health_passed = await self.health_monitor.check_model_health(model_id)
                        state.health_score = 1.0 if health_passed else 0.5
                        
                        if not health_passed:
                            logger.warning(f"Model {model_id} health check failed")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_unused_models(self):
        """Clean up unused models periodically."""
        while True:
            try:
                current_time = time.time()
                unused_threshold = 3600  # 1 hour
                
                for model_id, state in self.model_states.items():
                    if (state.status == ModelStatus.LOADED and 
                        state.last_used and 
                        current_time - state.last_used > unused_threshold):
                        
                        logger.info(f"Cleaning up unused model: {model_id}")
                        await self.unload_model(model_id)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                await asyncio.sleep(300)
    
    def _parse_memory_requirement(self, memory_str: str) -> float:
        """Parse memory requirement string to GB."""
        memory_str = memory_str.lower().replace('gb', '').replace('g', '').strip()
        try:
            return float(memory_str)
        except ValueError:
            return 5.0  # Default fallback
    
    async def _get_model_memory_usage(self, model_id: str) -> float:
        """Get current memory usage of a model."""
        # This would typically query the backend for actual memory usage
        # For now, return estimated usage based on model size
        return 5.0  # Default estimate


class MemoryManager:
    """Manage system memory for model loading."""
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get system memory information."""
        memory = psutil.virtual_memory()
        return {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent_used': memory.percent
        }
    
    def get_available_memory(self) -> float:
        """Get available memory in GB."""
        memory = psutil.virtual_memory()
        return memory.available / (1024**3)


class HealthMonitor:
    """Monitor health of loaded models."""
    
    def __init__(self, vllm_base_url: str = "http://localhost:8000"):
        self.vllm_base_url = vllm_base_url
    
    async def check_model_health(self, model_id: str) -> bool:
        """Check if a model is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vllm_base_url}/health") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed for {model_id}: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    async def test_loader():
        """Test the dynamic model loader."""
        loader = DynamicModelLoader()
        
        # Test model info
        from .model_router import ModelInfo, BackendType
        
        test_model = ModelInfo(
            model_id="microsoft/phi-2",
            backend=BackendType.VLLM,
            memory_required="5GB",
            performance_score=78,
            capabilities=["text_generation"],
            supported_languages=["english"],
            load_time="2.1s",
            inference_speed="excellent"
        )
        
        # Test loading
        result = await loader.load_model(test_model)
        print(f"Load result: {result}")
        
        # Test system status
        status = await loader.get_system_status()
        print(f"System status: {status}")
        
        # Test unloading
        success = await loader.unload_model(test_model.model_id)
        print(f"Unload success: {success}")
    
    # Run test
    asyncio.run(test_loader())
