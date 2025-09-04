"""
Transformers Backend Implementation

This module provides the Transformers backend implementation for the routing system.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM,
    pipeline, Pipeline
)

from .base_backend import BaseBackend, BackendResult, BackendStatus, ModelInfo

logger = logging.getLogger(__name__)


class TransformersBackend(BaseBackend):
    """
    Transformers backend implementation.
    
    This backend uses the Hugging Face Transformers library
    for model loading, inference, and management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Transformers backend.
        
        Args:
            config: Backend configuration
        """
        super().__init__(config)
        self.device = config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.torch_dtype = config.get('torch_dtype', torch.float16 if self.device == 'cuda' else torch.float32)
        self.max_memory = config.get('max_memory', '20GB')
        self.pipelines: Dict[str, Pipeline] = {}
        
    async def initialize(self) -> bool:
        """
        Initialize the Transformers backend.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.status = BackendStatus.INITIALIZING
            
            # Check if CUDA is available
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                self.device = 'cpu'
                self.torch_dtype = torch.float32
            
            # Set memory management
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            
            self.status = BackendStatus.READY
            logger.info(f"Transformers backend initialized on {self.device}")
            return True
            
        except Exception as e:
            self.status = BackendStatus.ERROR
            logger.error(f"Error initializing Transformers backend: {e}")
            return False
    
    async def load_model(self, model_info: ModelInfo) -> bool:
        """
        Load a model using Transformers.
        
        Args:
            model_info: Information about the model to load
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if not self.is_ready():
                logger.error("Transformers backend is not ready")
                return False
            
            self.status = BackendStatus.LOADING
            
            # Load model and tokenizer
            model_id = model_info.model_id
            model_path = model_info.model_path
            
            logger.info(f"Loading model: {model_id} from {model_path}")
            
            # Determine model type and create pipeline
            pipeline_type = self._determine_pipeline_type(model_info.capabilities)
            
            if pipeline_type == "text-generation":
                pipeline_obj = pipeline(
                    "text-generation",
                    model=model_path,
                    device=self.device,
                    torch_dtype=self.torch_dtype,
                    max_memory=self.max_memory if self.device == 'cuda' else None
                )
            elif pipeline_type == "text2text-generation":
                pipeline_obj = pipeline(
                    "text2text-generation",
                    model=model_path,
                    device=self.device,
                    torch_dtype=self.torch_dtype,
                    max_memory=self.max_memory if self.device == 'cuda' else None
                )
            elif pipeline_type == "automatic-speech-recognition":
                pipeline_obj = pipeline(
                    "automatic-speech-recognition",
                    model=model_path,
                    device=self.device,
                    torch_dtype=self.torch_dtype
                )
            elif pipeline_type == "text-to-speech":
                pipeline_obj = pipeline(
                    "text-to-speech",
                    model=model_path,
                    device=self.device,
                    torch_dtype=self.torch_dtype
                )
            else:
                # Default to text generation
                pipeline_obj = pipeline(
                    "text-generation",
                    model=model_path,
                    device=self.device,
                    torch_dtype=self.torch_dtype,
                    max_memory=self.max_memory if self.device == 'cuda' else None
                )
            
            # Store pipeline
            self.pipelines[model_id] = pipeline_obj
            self.loaded_models[model_id] = model_info
            
            self.status = BackendStatus.LOADED
            logger.info(f"Successfully loaded model: {model_id}")
            return True
            
        except Exception as e:
            self.status = BackendStatus.ERROR
            logger.error(f"Error loading model {model_info.model_id}: {e}")
            return False
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from Transformers.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            True if model unloaded successfully, False otherwise
        """
        try:
            if model_id not in self.loaded_models:
                logger.warning(f"Model {model_id} is not loaded")
                return True
            
            # Remove pipeline
            if model_id in self.pipelines:
                del self.pipelines[model_id]
            
            # Remove model info
            del self.loaded_models[model_id]
            
            # Clear CUDA cache if using GPU
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            
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
        Perform inference using Transformers.
        
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
                    error_message="Transformers backend is not ready"
                )
            
            if model_id not in self.loaded_models:
                return BackendResult(
                    success=False,
                    error_message=f"Model {model_id} is not loaded"
                )
            
            if model_id not in self.pipelines:
                return BackendResult(
                    success=False,
                    error_message=f"Pipeline for model {model_id} not found"
                )
            
            # Get pipeline
            pipeline_obj = self.pipelines[model_id]
            
            # Prepare input
            if isinstance(input_data, str):
                # Text input
                inputs = input_data
            elif isinstance(input_data, dict):
                # Structured input
                inputs = input_data
            else:
                inputs = str(input_data)
            
            # Perform inference
            result = await self._run_inference(pipeline_obj, inputs, **kwargs)
            
            inference_time = time.time() - start_time
            
            return BackendResult(
                success=True,
                result=result,
                inference_time=inference_time,
                model_id=model_id,
                metadata={
                    'pipeline_type': pipeline_obj.task,
                    'device': self.device
                }
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
        Check if Transformers backend is healthy.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            # Check if device is available
            if self.device == 'cuda' and not torch.cuda.is_available():
                return False
            
            # Check if we have any loaded models
            if not self.loaded_models:
                return True  # No models loaded, but backend is healthy
            
            # Test inference on a simple input
            for model_id in self.loaded_models:
                if model_id in self.pipelines:
                    try:
                        # Simple health check
                        test_input = "Hello"
                        pipeline_obj = self.pipelines[model_id]
                        
                        # Run a quick inference
                        if hasattr(pipeline_obj, 'tokenizer') and hasattr(pipeline_obj, 'model'):
                            # For text generation models
                            tokens = pipeline_obj.tokenizer.encode(test_input, return_tensors='pt')
                            if self.device == 'cuda':
                                tokens = tokens.to(self.device)
                            
                            with torch.no_grad():
                                _ = pipeline_obj.model(tokens)
                        
                        return True
                        
                    except Exception as e:
                        logger.error(f"Health check failed for model {model_id}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Transformers health check failed: {e}")
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
        Get system information from Transformers backend.
        
        Returns:
            Dictionary with system information
        """
        try:
            info = {
                'backend_type': 'transformers',
                'status': self.status.value,
                'device': self.device,
                'torch_dtype': str(self.torch_dtype),
                'loaded_models': list(self.loaded_models.keys()),
                'pipelines': list(self.pipelines.keys())
            }
            
            # Add CUDA info if available
            if self.device == 'cuda' and torch.cuda.is_available():
                info['cuda_info'] = {
                    'device_count': torch.cuda.device_count(),
                    'current_device': torch.cuda.current_device(),
                    'device_name': torch.cuda.get_device_name(),
                    'memory_allocated': torch.cuda.memory_allocated() / (1024**3),  # GB
                    'memory_reserved': torch.cuda.memory_reserved() / (1024**3)    # GB
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'backend_type': 'transformers',
                'status': self.status.value,
                'error': str(e)
            }
    
    def _determine_pipeline_type(self, capabilities: List[str]) -> str:
        """
        Determine the appropriate pipeline type based on model capabilities.
        
        Args:
            capabilities: List of model capabilities
            
        Returns:
            Pipeline type string
        """
        if 'speech_to_text' in capabilities or 'audio_processing' in capabilities:
            return 'automatic-speech-recognition'
        elif 'text_to_speech' in capabilities:
            return 'text-to-speech'
        elif 'text_generation' in capabilities:
            return 'text-generation'
        elif 'translation' in capabilities or 'summarization' in capabilities:
            return 'text2text-generation'
        else:
            return 'text-generation'  # Default
    
    async def _run_inference(self, pipeline_obj: Pipeline, inputs: Any, **kwargs) -> Any:
        """
        Run inference using a pipeline.
        
        Args:
            pipeline_obj: Transformers pipeline object
            inputs: Input data
            **kwargs: Additional parameters
            
        Returns:
            Inference result
        """
        try:
            # Run inference in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: pipeline_obj(inputs, **kwargs)
            )
            return result
            
        except Exception as e:
            logger.error(f"Error running inference: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup Transformers backend resources."""
        try:
            # Stop health monitoring
            await self.stop_health_monitoring()
            
            # Unload all models
            for model_id in list(self.loaded_models.keys()):
                await self.unload_model(model_id)
            
            # Clear CUDA cache
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            
            self.status = BackendStatus.UNINITIALIZED
            logger.info("Transformers backend cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up Transformers backend: {e}")


# Example usage and testing
if __name__ == "__main__":
    async def test_transformers_backend():
        """Test the Transformers backend."""
        config = {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'torch_dtype': torch.float16 if torch.cuda.is_available() else torch.float32,
            'max_memory': '10GB'
        }
        
        backend = TransformersBackend(config)
        
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
    asyncio.run(test_transformers_backend())
