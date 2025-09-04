"""
Base Backend Interface

This module defines the base interface for all inference backends.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class BackendStatus(Enum):
    """Backend status enumeration."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    UNLOADING = "unloading"


@dataclass
class BackendResult:
    """Result from backend inference."""
    success: bool
    result: Optional[Any] = None
    error_message: Optional[str] = None
    inference_time: float = 0.0
    memory_usage: float = 0.0
    model_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ModelInfo:
    """Model information for backend."""
    model_id: str
    model_path: str
    memory_required: float
    capabilities: List[str]
    supported_formats: List[str]
    config: Dict[str, Any] = None


class BaseBackend(ABC):
    """
    Base class for all inference backends.
    
    This class defines the interface that all backends must implement
    for model loading, inference, and management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the backend.
        
        Args:
            config: Backend-specific configuration
        """
        self.config = config or {}
        self.status = BackendStatus.UNINITIALIZED
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.timeout = self.config.get('timeout', 30)
        
        # Start health monitoring
        self._health_monitor_task = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the backend.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def load_model(self, model_info: ModelInfo) -> bool:
        """
        Load a model into the backend.
        
        Args:
            model_info: Information about the model to load
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from the backend.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            True if model unloaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def inference(
        self, 
        model_id: str, 
        input_data: Any, 
        **kwargs
    ) -> BackendResult:
        """
        Perform inference using the specified model.
        
        Args:
            model_id: ID of the model to use
            input_data: Input data for inference
            **kwargs: Additional inference parameters
            
        Returns:
            BackendResult with inference results
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the backend is healthy.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get information about a loaded model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            ModelInfo if model is loaded, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_loaded_models(self) -> List[str]:
        """
        Get list of currently loaded models.
        
        Returns:
            List of model IDs
        """
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information from the backend.
        
        Returns:
            Dictionary with system information
        """
        pass
    
    async def start_health_monitoring(self):
        """Start health monitoring task."""
        if self._health_monitor_task is None:
            self._health_monitor_task = asyncio.create_task(self._health_monitor())
    
    async def stop_health_monitoring(self):
        """Stop health monitoring task."""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
            self._health_monitor_task = None
    
    async def _health_monitor(self):
        """Background health monitoring task."""
        while True:
            try:
                if not await self.health_check():
                    logger.warning(f"Backend {self.__class__.__name__} health check failed")
                    self.status = BackendStatus.ERROR
                else:
                    if self.status == BackendStatus.ERROR:
                        logger.info(f"Backend {self.__class__.__name__} recovered")
                        self.status = BackendStatus.READY
                
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    def is_ready(self) -> bool:
        """Check if backend is ready for operations."""
        return self.status == BackendStatus.READY
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a specific model is loaded."""
        return model_id in self.loaded_models
    
    async def cleanup(self):
        """Cleanup backend resources."""
        try:
            # Stop health monitoring
            await self.stop_health_monitoring()
            
            # Unload all models
            for model_id in list(self.loaded_models.keys()):
                await self.unload_model(model_id)
            
            self.status = BackendStatus.UNINITIALIZED
            logger.info(f"Backend {self.__class__.__name__} cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up backend: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        if hasattr(self, '_health_monitor_task') and self._health_monitor_task:
            try:
                self._health_monitor_task.cancel()
            except:
                pass


# Example usage and testing
if __name__ == "__main__":
    class MockBackend(BaseBackend):
        """Mock backend for testing."""
        
        async def initialize(self) -> bool:
            self.status = BackendStatus.READY
            return True
        
        async def load_model(self, model_info: ModelInfo) -> bool:
            self.loaded_models[model_info.model_id] = model_info
            return True
        
        async def unload_model(self, model_id: str) -> bool:
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]
                return True
            return False
        
        async def inference(self, model_id: str, input_data: Any, **kwargs) -> BackendResult:
            if model_id not in self.loaded_models:
                return BackendResult(success=False, error_message="Model not loaded")
            
            return BackendResult(
                success=True,
                result=f"Mock result for {input_data}",
                inference_time=0.1,
                model_id=model_id
            )
        
        async def health_check(self) -> bool:
            return True
        
        async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
            return self.loaded_models.get(model_id)
        
        async def list_loaded_models(self) -> List[str]:
            return list(self.loaded_models.keys())
        
        async def get_system_info(self) -> Dict[str, Any]:
            return {
                'backend_type': 'mock',
                'status': self.status.value,
                'loaded_models': len(self.loaded_models)
            }
    
    async def test_backend():
        """Test the base backend interface."""
        backend = MockBackend()
        
        # Test initialization
        success = await backend.initialize()
        print(f"Initialization: {success}")
        
        # Test model loading
        model_info = ModelInfo(
            model_id="test-model",
            model_path="/path/to/model",
            memory_required=5.0,
            capabilities=["text_generation"],
            supported_formats=["text"]
        )
        
        success = await backend.load_model(model_info)
        print(f"Model loading: {success}")
        
        # Test inference
        result = await backend.inference("test-model", "Hello, world!")
        print(f"Inference result: {result}")
        
        # Test system info
        info = await backend.get_system_info()
        print(f"System info: {info}")
        
        # Test cleanup
        await backend.cleanup()
        print("Cleanup completed")
    
    # Run test
    asyncio.run(test_backend())
