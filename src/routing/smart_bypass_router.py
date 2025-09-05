"""
Smart Bypass Router - Optimized for Real-Time Conversations

This router implements intelligent bypassing where:
1. First request: Full routing decision + session establishment
2. Subsequent requests: Direct bypass to model endpoint
3. Route re-evaluation: Only when conversation context changes

This eliminates the routing layer bottleneck for ongoing conversations.
"""

import asyncio
import aiohttp
import time
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation state for routing decisions."""
    NEW = "new"
    CONTINUING = "continuing"
    CONTEXT_CHANGED = "context_changed"
    ENDED = "ended"


@dataclass
class ConversationSession:
    """Session information for conversation bypass."""
    session_id: str
    use_case: str
    endpoint: str
    model_id: str
    confidence: float
    created_at: datetime
    last_accessed: datetime
    request_count: int = 0
    context_hash: str = ""
    bypass_enabled: bool = True


@dataclass
class BypassRoutingResult:
    """Result of bypass routing."""
    endpoint: str
    use_case: str
    model_id: str
    confidence: float
    routing_time: float
    bypass_used: bool
    session_id: Optional[str] = None
    new_session: bool = False


class SmartBypassRouter:
    """
    Smart bypass router that eliminates routing overhead for ongoing conversations.
    
    Architecture:
    1. First request: Full routing + session creation
    2. Subsequent requests: Direct bypass to endpoint
    3. Context change: Re-evaluate routing
    4. Session timeout: Cleanup and re-route
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize the smart bypass router.
        
        Args:
            redis_url: Redis URL for session storage
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.model_endpoints = {
            "agent": {
                "endpoint": "http://192.168.0.21:8000",
                "model_id": "/app/models/minicpm-v-4",
                "port": 8000
            },
            "multimodal": {
                "endpoint": "http://192.168.0.21:8000", 
                "model_id": "/app/models/minicpm-v-4",
                "port": 8000
            },
            "avatar": {
                "endpoint": "http://192.168.0.21:8000",  # Shared with multimodal
                "model_id": "/app/models/minicpm-v-4",
                "port": 8000
            },
            "video": {
                "endpoint": "http://192.168.0.21:8000",  # Shared with multimodal
                "model_id": "/app/models/minicpm-v-4", 
                "port": 8000
            },
            "stt": {
                "endpoint": "http://192.168.0.21:8002",
                "model_id": "whisper-large-v3",
                "port": 8002
            },
            "tts": {
                "endpoint": "http://192.168.0.21:8003",
                "model_id": "coqui-tts",
                "port": 8003
            }
        }
        
        # Fast classification patterns
        self.fast_patterns = {
            "avatar": ["avatar", "lip", "face", "talking", "head", "facial", "mouth", "sync"],
            "stt": ["transcribe", "speech", "audio", "voice", "listen", "hear", "dictate"],
            "tts": ["speech", "voice", "speak", "tts", "synthesize", "narrate", "read"],
            "agent": ["code", "write", "generate", "analyze", "function", "script", "program"],
            "multimodal": ["image", "picture", "visual", "see", "look", "describe", "caption"],
            "video": ["video", "movie", "clip", "frame", "motion", "temporal", "sequence"]
        }
        
        # Session configuration
        self.session_timeout = 1800  # 30 minutes
        self.context_change_threshold = 0.3  # 30% confidence drop triggers re-routing
        self.max_requests_per_session = 1000
        
        # Performance monitoring
        self.stats = {
            "total_requests": 0,
            "bypass_requests": 0,
            "full_routing_requests": 0,
            "session_creations": 0,
            "session_timeouts": 0,
            "context_changes": 0,
            "average_routing_time": 0.0,
            "average_bypass_time": 0.0
        }
    
    async def route_query(
        self, 
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> BypassRoutingResult:
        """
        Route query with smart bypass optimization.
        
        Args:
            query: The input query
            session_id: Optional session ID for conversation continuity
            user_id: Optional user ID for session management
            modality: Optional modality hint
            context: Optional context information
            
        Returns:
            BypassRoutingResult with routing information
        """
        start_time = time.time()
        
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = self._generate_session_id(query, user_id)
            
            # Check for existing session
            session = await self._get_session(session_id)
            
            if session and session.bypass_enabled:
                # Check if we can use bypass
                bypass_result = await self._check_bypass_eligibility(
                    session, query, modality, context
                )
                
                if bypass_result["eligible"]:
                    # Use bypass - direct to endpoint
                    routing_time = time.time() - start_time
                    await self._update_session_usage(session_id)
                    
                    self.stats["bypass_requests"] += 1
                    self._update_bypass_stats(routing_time)
                    
                    return BypassRoutingResult(
                        endpoint=session.endpoint,
                        use_case=session.use_case,
                        model_id=session.model_id,
                        confidence=session.confidence,
                        routing_time=routing_time,
                        bypass_used=True,
                        session_id=session_id,
                        new_session=False
                    )
                else:
                    # Context changed - need re-routing
                    logger.info(f"Context changed for session {session_id}: {bypass_result['reason']}")
                    self.stats["context_changes"] += 1
            
            # Full routing required (new session or context change)
            use_case, confidence = await self._fast_classify(query, modality, context)
            endpoint_info = self.model_endpoints[use_case]
            
            routing_time = time.time() - start_time
            
            # Create or update session
            new_session = session is None
            session = ConversationSession(
                session_id=session_id,
                use_case=use_case,
                endpoint=endpoint_info["endpoint"],
                model_id=endpoint_info["model_id"],
                confidence=confidence,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                request_count=1,
                context_hash=self._calculate_context_hash(query, modality, context),
                bypass_enabled=True
            )
            
            await self._save_session(session)
            
            if new_session:
                self.stats["session_creations"] += 1
            else:
                self.stats["context_changes"] += 1
            
            self.stats["full_routing_requests"] += 1
            self._update_routing_stats(routing_time)
            
            return BypassRoutingResult(
                endpoint=endpoint_info["endpoint"],
                use_case=use_case,
                model_id=endpoint_info["model_id"],
                confidence=confidence,
                routing_time=routing_time,
                bypass_used=False,
                session_id=session_id,
                new_session=new_session
            )
            
        except Exception as e:
            logger.error(f"Error in smart bypass routing: {e}")
            # Fallback to agent endpoint
            return BypassRoutingResult(
                endpoint=self.model_endpoints["agent"]["endpoint"],
                use_case="agent",
                model_id=self.model_endpoints["agent"]["model_id"],
                confidence=0.5,
                routing_time=time.time() - start_time,
                bypass_used=False,
                session_id=session_id,
                new_session=True
            )
    
    async def _check_bypass_eligibility(
        self, 
        session: ConversationSession, 
        query: str, 
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if bypass is eligible for the current request.
        
        Returns:
            Dict with eligibility status and reason
        """
        # Check session timeout
        if datetime.now() - session.last_accessed > timedelta(seconds=self.session_timeout):
            return {"eligible": False, "reason": "session_timeout"}
        
        # Check request limit
        if session.request_count >= self.max_requests_per_session:
            return {"eligible": False, "reason": "request_limit_exceeded"}
        
        # Check context change
        current_context_hash = self._calculate_context_hash(query, modality, context)
        if current_context_hash != session.context_hash:
            # Re-classify to check if use case changed
            new_use_case, new_confidence = await self._fast_classify(query, modality, context)
            
            if new_use_case != session.use_case:
                return {"eligible": False, "reason": "use_case_changed"}
            
            # Check confidence drop
            confidence_drop = session.confidence - new_confidence
            if confidence_drop > self.context_change_threshold:
                return {"eligible": False, "reason": "confidence_drop"}
        
        return {"eligible": True, "reason": "context_unchanged"}
    
    async def _fast_classify(
        self, 
        query: str, 
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """Ultra-fast classification using keyword matching."""
        normalized_query = query.lower().strip()
        
        # Apply modality-based adjustments
        modality_boost = {}
        if modality:
            if modality == "image":
                modality_boost["multimodal"] = 0.3
                modality_boost["avatar"] = 0.2
            elif modality == "audio":
                modality_boost["stt"] = 0.3
                modality_boost["tts"] = 0.2
            elif modality == "video":
                modality_boost["video"] = 0.3
                modality_boost["multimodal"] = 0.2
        
        # Score each use case
        scores = {}
        for use_case, patterns in self.fast_patterns.items():
            score = 0.0
            
            for pattern in patterns:
                if pattern in normalized_query:
                    score += 1.0
            
            if patterns:
                score = score / len(patterns)
            
            if use_case in modality_boost:
                score += modality_boost[use_case]
            
            scores[use_case] = min(score, 1.0)
        
        # Find best use case
        best_use_case = max(scores, key=scores.get)
        confidence = scores[best_use_case]
        
        if confidence < 0.1:
            best_use_case = "agent"
            confidence = 0.5
        
        return best_use_case, confidence
    
    def _generate_session_id(self, query: str, user_id: Optional[str] = None) -> str:
        """Generate a unique session ID."""
        content = f"{query}:{user_id or 'anonymous'}:{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _calculate_context_hash(
        self, 
        query: str, 
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Calculate a hash for context comparison."""
        content = f"{query.lower()}:{modality or 'none'}:{json.dumps(context or {}, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    async def _get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session from Redis."""
        try:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                return ConversationSession(
                    session_id=data["session_id"],
                    use_case=data["use_case"],
                    endpoint=data["endpoint"],
                    model_id=data["model_id"],
                    confidence=data["confidence"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_accessed=datetime.fromisoformat(data["last_accessed"]),
                    request_count=data["request_count"],
                    context_hash=data["context_hash"],
                    bypass_enabled=data["bypass_enabled"]
                )
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
        return None
    
    async def _save_session(self, session: ConversationSession):
        """Save session to Redis."""
        try:
            session_data = {
                "session_id": session.session_id,
                "use_case": session.use_case,
                "endpoint": session.endpoint,
                "model_id": session.model_id,
                "confidence": session.confidence,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "request_count": session.request_count,
                "context_hash": session.context_hash,
                "bypass_enabled": session.bypass_enabled
            }
            
            self.redis_client.setex(
                f"session:{session.session_id}",
                self.session_timeout,
                json.dumps(session_data)
            )
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
    
    async def _update_session_usage(self, session_id: str):
        """Update session usage statistics."""
        try:
            session = await self._get_session(session_id)
            if session:
                session.last_accessed = datetime.now()
                session.request_count += 1
                await self._save_session(session)
        except Exception as e:
            logger.error(f"Error updating session usage {session_id}: {e}")
    
    def _update_routing_stats(self, routing_time: float):
        """Update full routing statistics."""
        self.stats["total_requests"] += 1
        total_routing_time = self.stats["average_routing_time"] * (self.stats["full_routing_requests"] - 1)
        self.stats["average_routing_time"] = (total_routing_time + routing_time) / self.stats["full_routing_requests"]
    
    def _update_bypass_stats(self, bypass_time: float):
        """Update bypass statistics."""
        self.stats["total_requests"] += 1
        if self.stats["bypass_requests"] > 1:
            total_bypass_time = self.stats["average_bypass_time"] * (self.stats["bypass_requests"] - 1)
            self.stats["average_bypass_time"] = (total_bypass_time + bypass_time) / self.stats["bypass_requests"]
        else:
            self.stats["average_bypass_time"] = bypass_time
    
    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions."""
        try:
            # Redis TTL handles expiration automatically
            # This method can be used for additional cleanup if needed
            pass
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_requests = self.stats["total_requests"]
        bypass_rate = (self.stats["bypass_requests"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "routing_stats": self.stats.copy(),
            "bypass_rate_percent": bypass_rate,
            "session_count": len(await self._get_all_session_keys()),
            "model_endpoints": self.model_endpoints
        }
    
    async def _get_all_session_keys(self) -> List[str]:
        """Get all session keys from Redis."""
        try:
            return self.redis_client.keys("session:*")
        except Exception as e:
            logger.error(f"Error getting session keys: {e}")
            return []
    
    async def end_session(self, session_id: str):
        """End a conversation session."""
        try:
            self.redis_client.delete(f"session:{session_id}")
            logger.info(f"Session {session_id} ended")
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")


# Example usage and testing
if __name__ == "__main__":
    async def test_smart_bypass_router():
        """Test the smart bypass router."""
        router = SmartBypassRouter()
        
        # Simulate a conversation
        conversation_queries = [
            "Write a Python function to sort a list",
            "Can you add error handling to that function?",
            "What about adding type hints?",
            "Make it more efficient with a different algorithm",
            "Now write a test for this function"
        ]
        
        print("🚀 Testing Smart Bypass Router...")
        print("=" * 60)
        
        session_id = None
        for i, query in enumerate(conversation_queries):
            result = await router.route_query(query, session_id=session_id)
            
            if result.new_session:
                session_id = result.session_id
                print(f"🆕 NEW SESSION: {session_id}")
            
            print(f"Query {i+1}: {query[:50]}...")
            print(f"Use Case: {result.use_case}")
            print(f"Endpoint: {result.endpoint}")
            print(f"Bypass Used: {'✅' if result.bypass_used else '❌'}")
            print(f"Routing Time: {result.routing_time*1000:.1f}ms")
            print("-" * 40)
        
        # Test performance stats
        stats = await router.get_performance_stats()
        print(f"\n📊 Performance Stats:")
        print(f"Total Requests: {stats['routing_stats']['total_requests']}")
        print(f"Bypass Rate: {stats['bypass_rate_percent']:.1f}%")
        print(f"Average Routing Time: {stats['routing_stats']['average_routing_time']*1000:.1f}ms")
        print(f"Average Bypass Time: {stats['routing_stats']['average_bypass_time']*1000:.1f}ms")
        print(f"Session Creations: {stats['routing_stats']['session_creations']}")
        print(f"Context Changes: {stats['routing_stats']['context_changes']}")
        
        # End session
        if session_id:
            await router.end_session(session_id)
            print(f"\n🔚 Session {session_id} ended")
    
    # Run test
    asyncio.run(test_smart_bypass_router())
