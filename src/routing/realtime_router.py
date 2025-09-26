"""
Real-Time Router for Ultra-Low Latency Conversations

This module provides optimized routing for real-time conversations
with <50ms routing overhead and <300ms total latency.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class UseCase(Enum):
    """Optimized use cases for real-time routing."""
    AGENT = "agent"
    AVATAR = "avatar"
    STT = "stt"
    TTS = "tts"
    MULTIMODAL = "multimodal"
    VIDEO = "video"


@dataclass
class RealtimeRoutingResult:
    """Result of real-time routing."""
    endpoint: str
    use_case: UseCase
    confidence: float
    routing_time: float
    model_id: str


class RealtimeRouter:
    """
    Ultra-fast router optimized for real-time conversations.
    
    Features:
    - <10ms classification
    - <50ms total routing
    - Pre-loaded model pool
    - Direct endpoint routing
    """
    
    def __init__(self):
        """Initialize the real-time router."""
        self.model_endpoints = {
            UseCase.AGENT: {
                "endpoint": "http://192.168.0.20:8000",
                "model_id": "/app/models/multimodal/minicpm-v-4",
                "port": 8000
            },
            UseCase.MULTIMODAL: {
                "endpoint": "http://192.168.0.20:8000", 
                "model_id": "/app/models/multimodal/minicpm-v-4",
                "port": 8000
            },
            UseCase.AVATAR: {
                "endpoint": "http://192.168.0.20:8000",  # Shared with multimodal
                "model_id": "/app/models/multimodal/minicpm-v-4",
                "port": 8000
            },
            UseCase.VIDEO: {
                "endpoint": "http://192.168.0.20:8000",  # Shared with multimodal
                "model_id": "/app/models/multimodal/minicpm-v-4", 
                "port": 8000
            },
            UseCase.STT: {
                "endpoint": "http://192.168.0.20:8002",
                "model_id": "whisper-large-v3",
                "port": 8002
            },
            UseCase.TTS: {
                "endpoint": "http://192.168.0.20:8003",
                "model_id": "coqui-tts",
                "port": 8003
            }
        }
        
        # Ultra-fast classification patterns (optimized for speed)
        self.fast_patterns = {
            UseCase.AVATAR: [
                "avatar", "lip", "face", "talking", "head", "facial", "mouth", "sync"
            ],
            UseCase.STT: [
                "transcribe", "speech", "audio", "voice", "listen", "hear", "dictate"
            ],
            UseCase.TTS: [
                "speech", "voice", "speak", "tts", "synthesize", "narrate", "read"
            ],
            UseCase.AGENT: [
                "code", "write", "generate", "analyze", "function", "script", "program"
            ],
            UseCase.MULTIMODAL: [
                "image", "picture", "visual", "see", "look", "describe", "caption"
            ],
            UseCase.VIDEO: [
                "video", "movie", "clip", "frame", "motion", "temporal", "sequence"
            ]
        }
        
        # Classification cache for repeated queries
        self.classification_cache: Dict[str, Tuple[UseCase, float]] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Performance monitoring
        self.routing_stats = {
            "total_requests": 0,
            "total_routing_time": 0.0,
            "average_routing_time": 0.0,
            "cache_hit_rate": 0.0
        }
    
    async def route_query(
        self, 
        query: str, 
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RealtimeRoutingResult:
        """
        Route a query with ultra-low latency.
        
        Args:
            query: The input query
            modality: Optional modality hint
            context: Optional context information
            
        Returns:
            RealtimeRoutingResult with endpoint and routing info
        """
        start_time = time.time()
        
        try:
            # Fast classification (<10ms target)
            use_case, confidence = await self._fast_classify(query, modality, context)
            
            # Get endpoint (instant)
            endpoint_info = self.model_endpoints[use_case]
            
            routing_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(routing_time)
            
            return RealtimeRoutingResult(
                endpoint=endpoint_info["endpoint"],
                use_case=use_case,
                confidence=confidence,
                routing_time=routing_time,
                model_id=endpoint_info["model_id"]
            )
            
        except Exception as e:
            logger.error(f"Error in real-time routing: {e}")
            # Fallback to agent endpoint
            return RealtimeRoutingResult(
                endpoint=self.model_endpoints[UseCase.AGENT]["endpoint"],
                use_case=UseCase.AGENT,
                confidence=0.5,
                routing_time=time.time() - start_time,
                model_id=self.model_endpoints[UseCase.AGENT]["model_id"]
            )
    
    async def _fast_classify(
        self, 
        query: str, 
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[UseCase, float]:
        """
        Ultra-fast classification using keyword matching.
        
        Target: <10ms classification time
        """
        # Check cache first
        cache_key = f"{query.lower()}:{modality or 'none'}"
        if cache_key in self.classification_cache:
            self.cache_hits += 1
            return self.classification_cache[cache_key]
        
        self.cache_misses += 1
        
        # Normalize query for fast matching
        normalized_query = query.lower().strip()
        
        # Apply modality-based adjustments
        modality_boost = {}
        if modality:
            if modality == "image":
                modality_boost[UseCase.MULTIMODAL] = 0.3
                modality_boost[UseCase.AVATAR] = 0.2
            elif modality == "audio":
                modality_boost[UseCase.STT] = 0.3
                modality_boost[UseCase.TTS] = 0.2
            elif modality == "video":
                modality_boost[UseCase.VIDEO] = 0.3
                modality_boost[UseCase.MULTIMODAL] = 0.2
        
        # Score each use case
        scores = {}
        for use_case, patterns in self.fast_patterns.items():
            score = 0.0
            
            # Pattern matching
            for pattern in patterns:
                if pattern in normalized_query:
                    score += 1.0
            
            # Normalize score
            if patterns:
                score = score / len(patterns)
            
            # Apply modality boost
            if use_case in modality_boost:
                score += modality_boost[use_case]
            
            scores[use_case] = min(score, 1.0)
        
        # Find best use case
        best_use_case = max(scores, key=scores.get)
        confidence = scores[best_use_case]
        
        # Ensure minimum confidence
        if confidence < 0.1:
            best_use_case = UseCase.AGENT
            confidence = 0.5
        
        # Cache result
        self.classification_cache[cache_key] = (best_use_case, confidence)
        
        # Limit cache size
        if len(self.classification_cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.classification_cache.keys())[:100]
            for key in oldest_keys:
                del self.classification_cache[key]
        
        return best_use_case, confidence
    
    def _update_stats(self, routing_time: float):
        """Update routing statistics."""
        self.routing_stats["total_requests"] += 1
        self.routing_stats["total_routing_time"] += routing_time
        self.routing_stats["average_routing_time"] = (
            self.routing_stats["total_routing_time"] / self.routing_stats["total_requests"]
        )
        
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            self.routing_stats["cache_hit_rate"] = self.cache_hits / total_cache_requests
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "routing_stats": self.routing_stats.copy(),
            "cache_size": len(self.classification_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "model_endpoints": {
                use_case.value: {
                    "endpoint": info["endpoint"],
                    "model_id": info["model_id"],
                    "port": info["port"]
                }
                for use_case, info in self.model_endpoints.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all model endpoints."""
        health_status = {}
        
        for use_case, info in self.model_endpoints.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{info['endpoint']}/health", timeout=2) as response:
                        health_status[use_case.value] = {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "endpoint": info["endpoint"],
                            "response_time": response.headers.get("X-Response-Time", "unknown")
                        }
            except Exception as e:
                health_status[use_case.value] = {
                    "status": "error",
                    "endpoint": info["endpoint"],
                    "error": str(e)
                }
        
        return health_status
    
    def get_available_use_cases(self) -> List[str]:
        """Get list of available use cases."""
        return [use_case.value for use_case in UseCase]
    
    def get_model_info(self, use_case: UseCase) -> Dict[str, Any]:
        """Get model information for a specific use case."""
        if use_case in self.model_endpoints:
            return self.model_endpoints[use_case].copy()
        return {}


# Example usage and testing
if __name__ == "__main__":
    async def test_realtime_router():
        """Test the real-time router."""
        router = RealtimeRouter()
        
        test_queries = [
            "Write a Python function to sort a list",
            "Generate a talking head avatar with lip sync",
            "Transcribe this audio file to text",
            "Convert this text to speech in Hindi",
            "Analyze this image and describe what you see",
            "Process this video and extract key frames"
        ]
        
        print("🚀 Testing Real-Time Router...")
        print("=" * 50)
        
        for query in test_queries:
            result = await router.route_query(query)
            print(f"Query: {query[:50]}...")
            print(f"Use Case: {result.use_case.value}")
            print(f"Endpoint: {result.endpoint}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Routing Time: {result.routing_time*1000:.1f}ms")
            print("-" * 30)
        
        # Test performance stats
        stats = await router.get_performance_stats()
        print(f"\n📊 Performance Stats:")
        print(f"Average Routing Time: {stats['routing_stats']['average_routing_time']*1000:.1f}ms")
        print(f"Cache Hit Rate: {stats['routing_stats']['cache_hit_rate']*100:.1f}%")
        print(f"Total Requests: {stats['routing_stats']['total_requests']}")
        
        # Test health check
        health = await router.health_check()
        print(f"\n🏥 Health Status:")
        for use_case, status in health.items():
            print(f"{use_case}: {status['status']}")
    
    # Run test
    asyncio.run(test_realtime_router())
