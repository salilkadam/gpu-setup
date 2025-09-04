"""
vLLM Backend Implementation

This module provides the vLLM backend implementation for the routing system.
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .base_backend import BaseBackend, BackendResult, BackendStatus, ModelInfo

logger = logging.getLogger(__name__)


@dataclass
class VLLMConfig:
    """vLLM backend configuration."""
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    health_check_interval: int = 10
    model_switch_timeout: int = 60


class VLLMBackend(BaseBackend):
    """
    vLLM backend implementation.
    
    This backend interfaces with vLLM's OpenAI-compatible API
    for model loading, inference, and management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the vLLM backend.
        
        Args:
            config: Backend configuration
        """
        super().__init__(config)
        self.vllm_config = VLLMConfig(**self.config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.current_model: Optional[str] = None
        
    async def initialize(self) -> bool:
        """
        Initialize the vLLM backend.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.status = BackendStatus.INITIALIZING
            
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.vllm_config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Check if vLLM is available
            if await self.health_check():
                self.status = BackendStatus.READY
                logger.info("vLLM backend initialized successfully")
                return True
            else:
                self.status = BackendStatus.ERROR
                logger.error("vLLM backend health check failed")
                return False
                
        except Exception as e:
            self.status = BackendStatus.ERROR
            logger.error(f"Error initializing vLLM backend: {e}")
            return False
    
    async def load_model(self, model_info: ModelInfo) -> bool:
        """
        Load a model into vLLM.
        
        Args:
            model_info: Information about the model to load
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if not self.is_ready():
                logger.error("vLLM backend is not ready")
                return False
            
            self.status = BackendStatus.LOADING
            
            # For vLLM, we need to restart the service with the new model
            # This is a limitation of the current setup
            success = await self._switch_model(model_info.model_path)
            
            if success:
                self.loaded_models[model_info.model_id] = model_info
                self.current_model = model_info.model_id
                self.status = BackendStatus.LOADED
                logger.info(f"Successfully loaded model: {model_info.model_id}")
                return True
            else:
                self.status = BackendStatus.ERROR
                logger.error(f"Failed to load model: {model_info.model_id}")
                return False
                
        except Exception as e:
            self.status = BackendStatus.ERROR
            logger.error(f"Error loading model {model_info.model_id}: {e}")
            return False
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from vLLM.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            True if model unloaded successfully, False otherwise
        """
        try:
            if model_id not in self.loaded_models:
                logger.warning(f"Model {model_id} is not loaded")
                return True
            
            # For vLLM, we can't unload individual models without restarting
            # This is a limitation of the current setup
            if model_id == self.current_model:
                self.current_model = None
            
            del self.loaded_models[model_id]
            logger.info(f"Model {model_id} unloaded")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading model {model_id}: {e}")
            return False
    
    async def inference(
        self, 
        model_id: str, 
        input_data: Any, 
        **kwargs
    ) -> BackendResult:
        """
        Perform inference using vLLM.
        
        Args:
            model_id: ID of the model to use
            input_data: Input data for inference
            **kwargs: Additional inference parameters
            
        Returns:
            BackendResult with inference results
        """
        start_time = time.time()
        
        try:
            if not self.is_ready():
                return BackendResult(
                    success=False,
                    error_message="vLLM backend is not ready"
                )
            
            if model_id not in self.loaded_models:
                return BackendResult(
                    success=False,
                    error_message=f"Model {model_id} is not loaded"
                )
            
            # Prepare inference request
            request_data = self._prepare_inference_request(input_data, **kwargs)
            
            # Make inference request
            result = await self._make_inference_request(request_data)
            
            inference_time = time.time() - start_time
            
            if result['success']:
                return BackendResult(
                    success=True,
                    result=result['response'],
                    inference_time=inference_time,
                    model_id=model_id,
                    metadata=result.get('metadata', {})
                )
            else:
                return BackendResult(
                    success=False,
                    error_message=result['error'],
                    inference_time=inference_time,
                    model_id=model_id
                )
                
        except Exception as e:
            inference_time = time.time() - start_time
            logger.error(f"Error during inference: {e}")
            return BackendResult(
                success=False,
                error_message=str(e),
                inference_time=inference_time,
                model_id=model_id
            )
    
    async def health_check(self) -> bool:
        """
        Check if vLLM is healthy.
        
        Returns:
            True if vLLM is healthy, False otherwise
        """
        try:
            if not self.session:
                return False
            
            async with self.session.get(f"{self.vllm_config.base_url}/health") as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")
            return False
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get information about a loaded model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            ModelInfo if model is loaded, None otherwise
        """
        return self.loaded_models.get(model_id)
    
    async def list_loaded_models(self) -> List[str]:
        """
        Get list of currently loaded models.
        
        Returns:
            List of model IDs
        """
        return list(self.loaded_models.keys())
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information from vLLM.
        
        Returns:
            Dictionary with system information
        """
        try:
            if not self.session:
                return {'error': 'Session not initialized'}
            
            # Get models info
            async with self.session.get(f"{self.vllm_config.base_url}/v1/models") as response:
                if response.status == 200:
                    models_data = await response.json()
                else:
                    models_data = {'error': f'HTTP {response.status}'}
            
            return {
                'backend_type': 'vllm',
                'status': self.status.value,
                'current_model': self.current_model,
                'loaded_models': list(self.loaded_models.keys()),
                'vllm_models': models_data,
                'base_url': self.vllm_config.base_url
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'backend_type': 'vllm',
                'status': self.status.value,
                'error': str(e)
            }
    
    async def _switch_model(self, model_path: str) -> bool:
        """
        Switch to a different model by restarting vLLM service.
        
        Args:
            model_path: Path to the new model
            
        Returns:
            True if switch successful, False otherwise
        """
        try:
            # This would typically involve:
            # 1. Updating docker-compose.yml
            # 2. Restarting the vLLM service
            # 3. Waiting for the new model to load
            
            # For now, we'll simulate this process
            logger.info(f"Switching to model: {model_path}")
            
            # Wait for model to be ready
            await asyncio.sleep(2)  # Simulate loading time
            
            # Check if the new model is available
            if await self.health_check():
                logger.info(f"Successfully switched to model: {model_path}")
                return True
            else:
                logger.error(f"Failed to switch to model: {model_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error switching model: {e}")
            return False
    
    def _prepare_inference_request(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Prepare inference request for vLLM API.
        
        Args:
            input_data: Input data for inference
            **kwargs: Additional parameters
            
        Returns:
            Prepared request data
        """
        # Determine request type based on input
        if isinstance(input_data, str):
            # Text completion request
            request_data = {
                "model": self.current_model or "default",
                "prompt": input_data,
                "max_tokens": kwargs.get('max_tokens', 100),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.9),
                "stream": kwargs.get('stream', False)
            }
        elif isinstance(input_data, dict):
            # Chat completion request
            request_data = {
                "model": self.current_model or "default",
                "messages": input_data.get('messages', []),
                "max_tokens": kwargs.get('max_tokens', 100),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.9),
                "stream": kwargs.get('stream', False)
            }
        else:
            # Default to text completion
            request_data = {
                "model": self.current_model or "default",
                "prompt": str(input_data),
                "max_tokens": kwargs.get('max_tokens', 100),
                "temperature": kwargs.get('temperature', 0.7)
            }
        
        return request_data
    
    async def _make_inference_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make inference request to vLLM API.
        
        Args:
            request_data: Prepared request data
            
        Returns:
            Response data
        """
        try:
            if not self.session:
                return {'success': False, 'error': 'Session not initialized'}
            
            # Determine endpoint based on request type
            if 'messages' in request_data:
                endpoint = "/v1/chat/completions"
            else:
                endpoint = "/v1/completions"
            
            url = f"{self.vllm_config.base_url}{endpoint}"
            
            async with self.session.post(url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'response': result,
                        'metadata': {
                            'status_code': response.status,
                            'endpoint': endpoint
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error making inference request: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cleanup(self):
        """Cleanup vLLM backend resources."""
        try:
            # Stop health monitoring
            await self.stop_health_monitoring()
            
            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None
            
            # Clear loaded models
            self.loaded_models.clear()
            self.current_model = None
            
            self.status = BackendStatus.UNINITIALIZED
            logger.info("vLLM backend cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up vLLM backend: {e}")


# Example usage and testing
if __name__ == "__main__":
    async def test_vllm_backend():
        """Test the vLLM backend."""
        config = {
            'base_url': 'http://localhost:8000',
            'timeout': 30,
            'max_retries': 3
        }
        
        backend = VLLMBackend(config)
        
        # Test initialization
        success = await backend.initialize()
        print(f"Initialization: {success}")
        
        if success:
            # Test system info
            info = await backend.get_system_info()
            print(f"System info: {info}")
            
            # Test health check
            health = await backend.health_check()
            print(f"Health check: {health}")
        
        # Test cleanup
        await backend.cleanup()
        print("Cleanup completed")
    
    # Run test
    asyncio.run(test_vllm_backend())
