"""
Routing API Implementation

This module provides FastAPI endpoints for the intelligent model routing system.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..routing.query_classifier import QueryClassifier, ClassificationResult, UseCase
from ..routing.model_router import ModelRouter, RoutingDecision
from ..routing.dynamic_loader import DynamicModelLoader
from ..routing.backends import VLLMBackend, TransformersBackend

logger = logging.getLogger(__name__)


# Pydantic models for API
class QueryRequest(BaseModel):
    """Request model for query routing."""
    query: str = Field(..., description="The input query to process")
    modality: Optional[str] = Field(None, description="Input modality hint (text, image, audio, video)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    prefer_loaded: Optional[bool] = Field(False, description="Prefer already loaded models")
    prefer_fast: Optional[bool] = Field(False, description="Prefer faster models")


class QueryResponse(BaseModel):
    """Response model for query routing."""
    success: bool
    result: Optional[str] = None
    use_case: Optional[str] = None
    selected_model: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    inference_time: Optional[float] = None
    model_switch_time: Optional[float] = None
    error_message: Optional[str] = None


class ModelLoadRequest(BaseModel):
    """Request model for model loading."""
    model_id: str = Field(..., description="ID of the model to load")
    priority: Optional[int] = Field(0, description="Loading priority")


class ModelLoadResponse(BaseModel):
    """Response model for model loading."""
    success: bool
    model_id: str
    load_time: float
    memory_usage: float
    error_message: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    loaded_models: List[str]
    total_models: int
    memory_usage: Dict[str, Any]
    routing_stats: Dict[str, Any]
    backend_status: Dict[str, Any]


class RoutingAPI:
    """
    Main routing API class that orchestrates the routing system.
    """
    
    def __init__(self):
        """Initialize the routing API."""
        self.app = FastAPI(
            title="Intelligent Model Routing API",
            description="API for intelligent model routing and inference",
            version="1.0.0"
        )
        
        # Initialize components
        self.query_classifier = QueryClassifier()
        self.model_router = ModelRouter()
        self.dynamic_loader = DynamicModelLoader()
        self.vllm_backend = VLLMBackend()
        self.transformers_backend = TransformersBackend()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'model_switches': 0,
            'average_inference_time': 0.0,
            'average_switch_time': 0.0
        }
        
        # Setup API
        self._setup_middleware()
        self._setup_routes()
        self._setup_error_handlers()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "Intelligent Model Routing API",
                "version": "1.0.0",
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                # Check backend health
                vllm_health = await self.vllm_backend.health_check()
                transformers_health = await self.transformers_backend.health_check()
                
                return {
                    "status": "healthy" if vllm_health or transformers_health else "unhealthy",
                    "vllm_backend": vllm_health,
                    "transformers_backend": transformers_health,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/route", response_model=QueryResponse)
        async def route_query(request: QueryRequest):
            """Route a query to the appropriate model."""
            start_time = time.time()
            
            try:
                self.stats['total_requests'] += 1
                
                # Classify the query
                classification = await self.query_classifier.classify_query(
                    query=request.query,
                    modality=request.modality,
                    context=request.context
                )
                
                # Route to appropriate model
                routing_decision = await self.model_router.route_query(
                    classification=classification,
                    context={
                        'prefer_loaded': request.prefer_loaded,
                        'prefer_fast': request.prefer_fast
                    }
                )
                
                # Check if model needs to be loaded
                model_switch_start = time.time()
                if not routing_decision.selected_model.is_loaded:
                    load_result = await self.dynamic_loader.load_model(
                        routing_decision.selected_model,
                        priority=10
                    )
                    
                    if not load_result.success:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to load model: {load_result.error_message}"
                        )
                    
                    self.stats['model_switches'] += 1
                
                model_switch_time = time.time() - model_switch_start
                
                # Perform inference
                inference_start = time.time()
                backend = self._get_backend_for_model(routing_decision.selected_model)
                
                inference_result = await backend.inference(
                    model_id=routing_decision.selected_model.model_id,
                    input_data=request.query,
                    max_tokens=request.context.get('max_tokens', 100) if request.context else 100,
                    temperature=request.context.get('temperature', 0.7) if request.context else 0.7
                )
                
                inference_time = time.time() - inference_start
                total_time = time.time() - start_time
                
                if not inference_result.success:
                    self.stats['failed_requests'] += 1
                    raise HTTPException(
                        status_code=500,
                        detail=f"Inference failed: {inference_result.error_message}"
                    )
                
                # Update statistics
                self.stats['successful_requests'] += 1
                self._update_average_times(inference_time, model_switch_time)
                
                # Update model usage
                self.model_router.update_model_status(
                    routing_decision.selected_model.model_id,
                    True
                )
                
                return QueryResponse(
                    success=True,
                    result=inference_result.result,
                    use_case=classification.use_case.value,
                    selected_model=routing_decision.selected_model.model_id,
                    confidence=routing_decision.confidence,
                    reasoning=routing_decision.reasoning,
                    inference_time=inference_time,
                    model_switch_time=model_switch_time
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.stats['failed_requests'] += 1
                logger.error(f"Error routing query: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models/load", response_model=ModelLoadResponse)
        async def load_model(request: ModelLoadRequest, background_tasks: BackgroundTasks):
            """Load a specific model."""
            try:
                # Get model info from router
                available_models = self.model_router._get_available_models("agent")  # Default use case
                model_info = None
                
                for model in available_models:
                    if model.model_id == request.model_id:
                        model_info = model
                        break
                
                if not model_info:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Model {request.model_id} not found"
                    )
                
                # Load the model
                load_result = await self.dynamic_loader.load_model(
                    model_info,
                    priority=request.priority
                )
                
                if not load_result.success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to load model: {load_result.error_message}"
                    )
                
                return ModelLoadResponse(
                    success=True,
                    model_id=request.model_id,
                    load_time=load_result.load_time,
                    memory_usage=load_result.memory_usage
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/models/{model_id}")
        async def unload_model(model_id: str):
            """Unload a specific model."""
            try:
                success = await self.dynamic_loader.unload_model(model_id)
                
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to unload model {model_id}"
                    )
                
                return {"success": True, "message": f"Model {model_id} unloaded"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models", response_model=List[str])
        async def list_loaded_models():
            """List currently loaded models."""
            try:
                return await self.dynamic_loader.get_loaded_models()
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status", response_model=SystemStatusResponse)
        async def get_system_status():
            """Get system status."""
            try:
                # Get system information
                system_status = await self.dynamic_loader.get_system_status()
                vllm_info = await self.vllm_backend.get_system_info()
                transformers_info = await self.transformers_backend.get_system_info()
                model_stats = self.model_router.get_model_usage_stats()
                
                return SystemStatusResponse(
                    status="healthy",
                    loaded_models=system_status['loaded_models'],
                    total_models=system_status['total_models'],
                    memory_usage=system_status['memory_usage'],
                    routing_stats=self.stats,
                    backend_status={
                        'vllm': vllm_info,
                        'transformers': transformers_info
                    }
                )
                
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/use-cases")
        async def list_use_cases():
            """List supported use cases."""
            try:
                use_cases = self.query_classifier.get_supported_use_cases()
                return {
                    "use_cases": [
                        {
                            "id": use_case.value,
                            "description": self.query_classifier.get_use_case_description(use_case)
                        }
                        for use_case in use_cases
                    ]
                }
            except Exception as e:
                logger.error(f"Error listing use cases: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models/available")
        async def list_available_models():
            """List all available models."""
            try:
                # This would return all models from the registry
                return {
                    "models": [
                        {
                            "model_id": "microsoft/phi-2",
                            "use_case": "agent",
                            "backend": "vllm",
                            "memory_required": "5GB",
                            "performance_score": 78
                        },
                        {
                            "model_id": "Qwen/Qwen2.5-7B-Instruct",
                            "use_case": "agent",
                            "backend": "vllm",
                            "memory_required": "15GB",
                            "performance_score": 95
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"Error listing available models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _setup_error_handlers(self):
        """Setup error handlers."""
        from .error_handlers import setup_error_handlers
        setup_error_handlers(self.app)
    
    def _get_backend_for_model(self, model_info) -> Union[VLLMBackend, TransformersBackend]:
        """Get the appropriate backend for a model."""
        if model_info.backend.value == "vllm":
            return self.vllm_backend
        elif model_info.backend.value == "transformers":
            return self.transformers_backend
        else:
            # Default to vLLM
            return self.vllm_backend
    
    def _update_average_times(self, inference_time: float, switch_time: float):
        """Update average inference and switch times."""
        total_requests = self.stats['successful_requests']
        
        # Update average inference time
        current_avg = self.stats['average_inference_time']
        self.stats['average_inference_time'] = (
            (current_avg * (total_requests - 1) + inference_time) / total_requests
        )
        
        # Update average switch time (only when switching occurs)
        if switch_time > 0:
            switches = self.stats['model_switches']
            if switches > 0:
                current_avg_switch = self.stats['average_switch_time']
                self.stats['average_switch_time'] = (
                    (current_avg_switch * (switches - 1) + switch_time) / switches
                )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    routing_api = RoutingAPI()
    return routing_api.app


# Example usage
if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
