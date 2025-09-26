"""
Real-Time Routing API with Smart Bypass

This API implements the smart bypass mechanism for ultra-low latency
real-time conversations with session-based routing optimization.
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..routing.smart_bypass_router import SmartBypassRouter, BypassRoutingResult
from ..routing.realtime_router import RealtimeRouter

logger = logging.getLogger(__name__)


# Pydantic models for API
class RealtimeQueryRequest(BaseModel):
    """Request model for real-time query routing."""
    query: str = Field(..., description="The input query to process")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID for session management")
    modality: Optional[str] = Field(None, description="Input modality hint (text, image, audio, video)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    max_tokens: Optional[int] = Field(100, description="Maximum tokens for response")
    temperature: Optional[float] = Field(0.7, description="Temperature for response generation")


class RealtimeQueryResponse(BaseModel):
    """Response model for real-time query routing."""
    success: bool
    result: Optional[str] = None
    use_case: Optional[str] = None
    selected_model: Optional[str] = None
    endpoint: Optional[str] = None
    confidence: Optional[float] = None
    routing_time: Optional[float] = None
    bypass_used: Optional[bool] = None
    session_id: Optional[str] = None
    new_session: Optional[bool] = None
    inference_time: Optional[float] = None
    total_time: Optional[float] = None
    error_message: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    use_case: str
    model_id: str
    endpoint: str
    confidence: float
    request_count: int
    created_at: str
    last_accessed: str
    bypass_enabled: bool


class PerformanceStats(BaseModel):
    """Performance statistics model."""
    total_requests: int
    bypass_requests: int
    full_routing_requests: int
    session_creations: int
    context_changes: int
    bypass_rate_percent: float
    average_routing_time: float
    average_bypass_time: float
    average_inference_time: float
    average_total_time: float


class RealtimeRoutingAPI:
    """
    Real-time routing API with smart bypass optimization.
    """
    
    def __init__(self, redis_url: str = None):
        """Initialize the real-time routing API."""
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://ai-redis:6379")
        self.app = FastAPI(
            title="Real-Time Model Routing API",
            description="Ultra-low latency routing with smart bypass for real-time conversations",
            version="1.0.0"
        )
        
        # Initialize components
        self.bypass_router = SmartBypassRouter(redis_url)
        self.fallback_router = RealtimeRouter()
        
        # Performance tracking
        self.total_inference_time = 0.0
        self.total_requests = 0
        
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
                "message": "Real-Time Model Routing API with Smart Bypass",
                "version": "1.0.0",
                "status": "running",
                "features": [
                    "Smart bypass for ongoing conversations",
                    "Session-based routing optimization",
                    "Ultra-low latency (<50ms routing)",
                    "Context-aware re-routing",
                    "Real-time performance monitoring"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                # Check Redis connection
                await self.bypass_router.cleanup_expired_sessions()
                
                # Check model endpoints
                health_status = await self.fallback_router.health_check()
                
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "bypass_router": "connected",
                    "model_endpoints": health_status
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/route", response_model=RealtimeQueryResponse)
        async def route_query(
            request: RealtimeQueryRequest,
            background_tasks: BackgroundTasks,
            x_session_id: Optional[str] = Header(None)
        ):
            """Route a query with smart bypass optimization."""
            start_time = time.time()
            
            try:
                # Use header session ID if not provided in body
                session_id = request.session_id or x_session_id
                
                # Route with smart bypass
                routing_result = await self.bypass_router.route_query(
                    query=request.query,
                    session_id=session_id,
                    user_id=request.user_id,
                    modality=request.modality,
                    context=request.context
                )
                
                routing_time = time.time() - start_time
                
                # Perform inference
                inference_start = time.time()
                inference_result = await self._perform_inference(
                    routing_result, request
                )
                inference_time = time.time() - inference_start
                total_time = time.time() - start_time
                
                # Update performance tracking
                self._update_performance_stats(inference_time, total_time)
                
                # Schedule background tasks
                if routing_result.new_session:
                    background_tasks.add_task(
                        self._log_session_creation, 
                        routing_result.session_id
                    )
                
                if routing_result.bypass_used:
                    background_tasks.add_task(
                        self._log_bypass_usage, 
                        routing_result.session_id
                    )
                
                return RealtimeQueryResponse(
                    success=True,
                    result=inference_result,
                    use_case=routing_result.use_case,
                    selected_model=routing_result.model_id,
                    endpoint=routing_result.endpoint,
                    confidence=routing_result.confidence,
                    routing_time=routing_time,
                    bypass_used=routing_result.bypass_used,
                    session_id=routing_result.session_id,
                    new_session=routing_result.new_session,
                    inference_time=inference_time,
                    total_time=total_time
                )
                
            except Exception as e:
                logger.error(f"Error routing query: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/sessions/{session_id}", response_model=SessionInfo)
        async def get_session_info(session_id: str):
            """Get information about a specific session."""
            try:
                session = await self.bypass_router._get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                return SessionInfo(
                    session_id=session.session_id,
                    use_case=session.use_case,
                    model_id=session.model_id,
                    endpoint=session.endpoint,
                    confidence=session.confidence,
                    request_count=session.request_count,
                    created_at=session.created_at.isoformat(),
                    last_accessed=session.last_accessed.isoformat(),
                    bypass_enabled=session.bypass_enabled
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session info: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/sessions/{session_id}")
        async def end_session(session_id: str):
            """End a conversation session."""
            try:
                await self.bypass_router.end_session(session_id)
                return {"success": True, "message": f"Session {session_id} ended"}
                
            except Exception as e:
                logger.error(f"Error ending session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats", response_model=PerformanceStats)
        async def get_performance_stats():
            """Get performance statistics."""
            try:
                stats = await self.bypass_router.get_performance_stats()
                routing_stats = stats["routing_stats"]
                
                return PerformanceStats(
                    total_requests=routing_stats["total_requests"],
                    bypass_requests=routing_stats["bypass_requests"],
                    full_routing_requests=routing_stats["full_routing_requests"],
                    session_creations=routing_stats["session_creations"],
                    context_changes=routing_stats["context_changes"],
                    bypass_rate_percent=stats["bypass_rate_percent"],
                    average_routing_time=routing_stats["average_routing_time"],
                    average_bypass_time=routing_stats["average_bypass_time"],
                    average_inference_time=self._get_average_inference_time(),
                    average_total_time=self._get_average_total_time()
                )
                
            except Exception as e:
                logger.error(f"Error getting performance stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/use-cases")
        async def list_use_cases():
            """List supported use cases."""
            try:
                use_cases = self.fallback_router.get_available_use_cases()
                return {
                    "use_cases": [
                        {
                            "id": use_case,
                            "description": self._get_use_case_description(use_case),
                            "endpoint": self.fallback_router.model_endpoints.get(use_case, {}).get("endpoint")
                        }
                        for use_case in use_cases
                    ]
                }
            except Exception as e:
                logger.error(f"Error listing use cases: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/cleanup")
        async def cleanup_sessions():
            """Manually cleanup expired sessions."""
            try:
                await self.bypass_router.cleanup_expired_sessions()
                return {"success": True, "message": "Session cleanup completed"}
                
            except Exception as e:
                logger.error(f"Error cleaning up sessions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _setup_error_handlers(self):
        """Setup error handlers."""
        from .error_handlers import setup_error_handlers
        setup_error_handlers(self.app)
    
    async def _perform_inference(
        self, 
        routing_result: BypassRoutingResult, 
        request: RealtimeQueryRequest
    ) -> str:
        """Perform inference using the routed endpoint."""
        try:
            import aiohttp
            
            # Prepare inference request for chat completions API
            inference_data = {
                "model": routing_result.model_id,
                "messages": [
                    {"role": "user", "content": request.query}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "stream": False
            }
            
            # Make inference request to chat completions endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{routing_result.endpoint}/v1/chat/completions",
                    json=inference_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error performing inference: {e}")
            return f"Error: {str(e)}"
    
    def _update_performance_stats(self, inference_time: float, total_time: float):
        """Update performance statistics."""
        self.total_requests += 1
        self.total_inference_time += inference_time
    
    def _get_average_inference_time(self) -> float:
        """Get average inference time."""
        if self.total_requests > 0:
            return self.total_inference_time / self.total_requests
        return 0.0
    
    def _get_average_total_time(self) -> float:
        """Get average total time."""
        # This would be calculated from actual request times
        # For now, return a placeholder
        return 0.0
    
    def _get_use_case_description(self, use_case: str) -> str:
        """Get description for a use case."""
        descriptions = {
            "agent": "Content generation and executing agents",
            "avatar": "Talking head avatars and lip sync generation",
            "stt": "Speech-to-text conversion for Indian languages",
            "tts": "Text-to-speech synthesis for Indian languages",
            "multimodal": "Multi-modal temporal agentic RAG",
            "video": "Video-to-text understanding and content generation"
        }
        return descriptions.get(use_case, "Unknown use case")
    
    async def _log_session_creation(self, session_id: str):
        """Log session creation."""
        logger.info(f"New session created: {session_id}")
    
    async def _log_bypass_usage(self, session_id: str):
        """Log bypass usage."""
        logger.debug(f"Bypass used for session: {session_id}")


def create_app(redis_url: str = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    routing_api = RealtimeRoutingAPI(redis_url)
    return routing_api.app


# Example usage
if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
