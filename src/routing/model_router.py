"""
Model Router System

This module provides intelligent model selection and routing based on
use case, performance, and resource availability.
"""

import asyncio
import yaml
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import psutil
import time

from .query_classifier import UseCase, ClassificationResult

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Enumeration of supported backends."""
    VLLM = "vllm"
    TRANSFORMERS = "transformers"
    CUSTOM = "custom"


@dataclass
class ModelInfo:
    """Information about a specific model."""
    model_id: str
    backend: BackendType
    memory_required: str
    performance_score: int
    capabilities: List[str]
    supported_languages: List[str]
    load_time: str
    inference_speed: str
    is_loaded: bool = False
    last_used: Optional[float] = None
    usage_count: int = 0


@dataclass
class RoutingDecision:
    """Result of model routing decision."""
    selected_model: ModelInfo
    confidence: float
    reasoning: str
    fallback_models: List[ModelInfo]
    estimated_load_time: float
    resource_impact: Dict[str, Any]


class ModelRouter:
    """
    Intelligent model router that selects the most appropriate model
    based on use case, performance, and resource availability.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model router.
        
        Args:
            config_path: Path to model registry configuration file
        """
        self.config_path = config_path or "src/config/model_registry.yaml"
        self.model_registry = self._load_model_registry()
        self.routing_config = self._load_routing_config()
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.performance_cache: Dict[str, float] = {}
        self.resource_monitor = ResourceMonitor()
        
    def _load_model_registry(self) -> Dict[str, Any]:
        """Load model registry from configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('models', {})
        except Exception as e:
            logger.error(f"Error loading model registry: {e}")
            return {}
    
    def _load_routing_config(self) -> Dict[str, Any]:
        """Load routing configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('routing', {})
        except Exception as e:
            logger.error(f"Error loading routing config: {e}")
            return {
                "default_confidence_threshold": 0.7,
                "fallback_confidence_threshold": 0.3,
                "max_concurrent_models": 3,
                "model_switch_timeout": 10,
                "memory_threshold": 0.8,
                "performance_weight": 0.4,
                "availability_weight": 0.3,
                "resource_weight": 0.3
            }
    
    async def route_query(
        self, 
        classification: ClassificationResult,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a query to the most appropriate model.
        
        Args:
            classification: Result from query classification
            context: Optional context information
            
        Returns:
            RoutingDecision with selected model and reasoning
        """
        try:
            use_case = classification.use_case.value
            confidence = classification.confidence
            
            # Get available models for this use case
            available_models = self._get_available_models(use_case)
            
            if not available_models:
                raise ValueError(f"No models available for use case: {use_case}")
            
            # Score and rank models
            scored_models = await self._score_models(
                available_models, classification, context
            )
            
            # Select best model
            selected_model, selection_confidence = self._select_best_model(
                scored_models, confidence
            )
            
            # Get fallback models
            fallback_models = self._get_fallback_models(
                scored_models, selected_model
            )
            
            # Estimate resource impact
            resource_impact = await self._estimate_resource_impact(selected_model)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                selected_model, classification, selection_confidence, resource_impact
            )
            
            return RoutingDecision(
                selected_model=selected_model,
                confidence=selection_confidence,
                reasoning=reasoning,
                fallback_models=fallback_models,
                estimated_load_time=self._parse_load_time(selected_model.load_time),
                resource_impact=resource_impact
            )
            
        except Exception as e:
            logger.error(f"Error routing query: {e}")
            # Return fallback decision
            return await self._get_fallback_decision(classification)
    
    def _get_available_models(self, use_case: str) -> List[ModelInfo]:
        """Get available models for a specific use case."""
        if use_case not in self.model_registry:
            return []
        
        models = []
        use_case_config = self.model_registry[use_case]
        
        # Add primary model
        if 'primary' in use_case_config:
            models.append(self._create_model_info(
                use_case_config['primary'], 'primary'
            ))
        
        # Add fallback models
        for fallback_type in ['fallback', 'coding', 'custom']:
            if fallback_type in use_case_config:
                models.append(self._create_model_info(
                    use_case_config[fallback_type], fallback_type
                ))
        
        return models
    
    def _create_model_info(self, model_config: Dict[str, Any], model_type: str) -> ModelInfo:
        """Create ModelInfo from configuration."""
        return ModelInfo(
            model_id=model_config['model_id'],
            backend=BackendType(model_config['backend']),
            memory_required=model_config['memory_required'],
            performance_score=model_config['performance_score'],
            capabilities=model_config.get('capabilities', []),
            supported_languages=model_config.get('supported_languages', []),
            load_time=model_config.get('load_time', '2.0s'),
            inference_speed=model_config.get('inference_speed', 'good'),
            is_loaded=model_config['model_id'] in self.loaded_models,
            last_used=self.loaded_models.get(model_config['model_id'], {}).get('last_used'),
            usage_count=self.loaded_models.get(model_config['model_id'], {}).get('usage_count', 0)
        )
    
    async def _score_models(
        self, 
        models: List[ModelInfo], 
        classification: ClassificationResult,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ModelInfo, float]]:
        """Score models based on various criteria."""
        scored_models = []
        
        for model in models:
            score = 0.0
            
            # Performance score (40% weight)
            performance_score = model.performance_score / 100.0
            score += performance_score * self.routing_config['performance_weight']
            
            # Availability score (30% weight)
            availability_score = 1.0 if model.is_loaded else 0.5
            score += availability_score * self.routing_config['availability_weight']
            
            # Resource score (30% weight)
            resource_score = await self._calculate_resource_score(model)
            score += resource_score * self.routing_config['resource_weight']
            
            # Language compatibility bonus
            if classification.language in model.supported_languages:
                score += 0.1
            
            # Capability matching bonus
            required_capabilities = self._get_required_capabilities(classification)
            matching_capabilities = len(set(required_capabilities) & set(model.capabilities))
            if matching_capabilities > 0:
                score += (matching_capabilities / len(required_capabilities)) * 0.1
            
            # Context-based adjustments
            if context:
                if context.get('prefer_loaded', False) and model.is_loaded:
                    score += 0.1
                
                if context.get('prefer_fast', False) and model.inference_speed == 'excellent':
                    score += 0.1
            
            scored_models.append((model, score))
        
        # Sort by score (descending)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return scored_models
    
    async def _calculate_resource_score(self, model: ModelInfo) -> float:
        """Calculate resource availability score for a model."""
        try:
            # Get current system resources
            memory_info = self.resource_monitor.get_memory_info()
            gpu_info = self.resource_monitor.get_gpu_info()
            
            # Parse memory requirement
            required_memory = self._parse_memory_requirement(model.memory_required)
            
            # Calculate available memory
            available_memory = memory_info['available_gb']
            available_gpu_memory = gpu_info.get('available_gb', 0)
            
            # Score based on memory availability
            if required_memory <= available_gpu_memory:
                memory_score = 1.0
            elif required_memory <= available_memory:
                memory_score = 0.7
            else:
                memory_score = 0.3
            
            # Adjust for already loaded models
            if model.is_loaded:
                memory_score = 1.0  # Already loaded, no additional memory needed
            
            return memory_score
            
        except Exception as e:
            logger.error(f"Error calculating resource score: {e}")
            return 0.5  # Default score
    
    def _get_required_capabilities(self, classification: ClassificationResult) -> List[str]:
        """Get required capabilities based on classification."""
        capabilities_map = {
            UseCase.AVATAR: ['multimodal', 'vision', 'text_generation'],
            UseCase.STT: ['audio_processing', 'speech_to_text', 'multilingual'],
            UseCase.TTS: ['audio_processing', 'text_to_speech', 'multilingual'],
            UseCase.AGENT: ['text_generation', 'code_generation', 'reasoning'],
            UseCase.MULTIMODAL: ['multimodal', 'vision', 'text_generation', 'rag'],
            UseCase.VIDEO: ['multimodal', 'video_understanding', 'temporal_analysis']
        }
        
        return capabilities_map.get(classification.use_case, ['text_generation'])
    
    def _select_best_model(
        self, 
        scored_models: List[Tuple[ModelInfo, float]], 
        classification_confidence: float
    ) -> Tuple[ModelInfo, float]:
        """Select the best model based on scores and confidence."""
        if not scored_models:
            raise ValueError("No models available for selection")
        
        best_model, best_score = scored_models[0]
        
        # Adjust confidence based on model score and classification confidence
        selection_confidence = (best_score + classification_confidence) / 2.0
        
        # Ensure minimum confidence threshold
        min_confidence = self.routing_config['default_confidence_threshold']
        if selection_confidence < min_confidence:
            logger.warning(f"Low confidence selection: {selection_confidence:.2f}")
        
        return best_model, selection_confidence
    
    def _get_fallback_models(
        self, 
        scored_models: List[Tuple[ModelInfo, float]], 
        selected_model: ModelInfo
    ) -> List[ModelInfo]:
        """Get fallback models in case the primary model fails."""
        fallback_models = []
        
        for model, score in scored_models[1:]:  # Skip the selected model
            if score >= self.routing_config['fallback_confidence_threshold']:
                fallback_models.append(model)
            
            # Limit number of fallback models
            if len(fallback_models) >= 2:
                break
        
        return fallback_models
    
    async def _estimate_resource_impact(self, model: ModelInfo) -> Dict[str, Any]:
        """Estimate the resource impact of loading a model."""
        try:
            memory_info = self.resource_monitor.get_memory_info()
            gpu_info = self.resource_monitor.get_gpu_info()
            
            required_memory = self._parse_memory_requirement(model.memory_required)
            
            impact = {
                'memory_required_gb': required_memory,
                'available_memory_gb': memory_info['available_gb'],
                'available_gpu_memory_gb': gpu_info.get('available_gb', 0),
                'will_fit_in_gpu': required_memory <= gpu_info.get('available_gb', 0),
                'will_fit_in_system': required_memory <= memory_info['available_gb'],
                'estimated_load_time': self._parse_load_time(model.load_time),
                'already_loaded': model.is_loaded
            }
            
            return impact
            
        except Exception as e:
            logger.error(f"Error estimating resource impact: {e}")
            return {'error': str(e)}
    
    def _generate_reasoning(
        self, 
        model: ModelInfo, 
        classification: ClassificationResult,
        confidence: float,
        resource_impact: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning for model selection."""
        reasoning_parts = []
        
        # Primary reason
        reasoning_parts.append(f"Selected {model.model_id} for {classification.use_case.value} use case")
        
        # Performance reason
        reasoning_parts.append(f"Performance score: {model.performance_score}/100")
        
        # Availability reason
        if model.is_loaded:
            reasoning_parts.append("Model is already loaded (fast access)")
        else:
            reasoning_parts.append("Model needs to be loaded")
        
        # Resource reason
        if resource_impact.get('will_fit_in_gpu', False):
            reasoning_parts.append("Sufficient GPU memory available")
        elif resource_impact.get('will_fit_in_system', False):
            reasoning_parts.append("Sufficient system memory available")
        else:
            reasoning_parts.append("Memory constraints may apply")
        
        # Language reason
        if classification.language in model.supported_languages:
            reasoning_parts.append(f"Supports {classification.language} language")
        
        # Confidence reason
        reasoning_parts.append(f"Selection confidence: {confidence:.2f}")
        
        return "; ".join(reasoning_parts)
    
    def _parse_memory_requirement(self, memory_str: str) -> float:
        """Parse memory requirement string to GB."""
        memory_str = memory_str.lower().replace('gb', '').replace('g', '').strip()
        try:
            return float(memory_str)
        except ValueError:
            return 5.0  # Default fallback
    
    def _parse_load_time(self, load_time_str: str) -> float:
        """Parse load time string to seconds."""
        load_time_str = load_time_str.lower().replace('s', '').strip()
        try:
            return float(load_time_str)
        except ValueError:
            return 2.0  # Default fallback
    
    async def _get_fallback_decision(self, classification: ClassificationResult) -> RoutingDecision:
        """Get fallback decision when routing fails."""
        # Try to get any available model for the use case
        available_models = self._get_available_models(classification.use_case.value)
        
        if available_models:
            fallback_model = available_models[0]  # Use first available
        else:
            # Use default agent model
            fallback_model = ModelInfo(
                model_id="microsoft/phi-2",
                backend=BackendType.VLLM,
                memory_required="5GB",
                performance_score=78,
                capabilities=["text_generation"],
                supported_languages=["english"],
                load_time="2.1s",
                inference_speed="excellent"
            )
        
        return RoutingDecision(
            selected_model=fallback_model,
            confidence=0.3,
            reasoning="Fallback selection due to routing error",
            fallback_models=[],
            estimated_load_time=2.0,
            resource_impact={'error': 'fallback_mode'}
        )
    
    def update_model_status(self, model_id: str, is_loaded: bool):
        """Update the loading status of a model."""
        if model_id in self.loaded_models:
            self.loaded_models[model_id]['is_loaded'] = is_loaded
            self.loaded_models[model_id]['last_used'] = time.time()
            if is_loaded:
                self.loaded_models[model_id]['usage_count'] += 1
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models."""
        return [model_id for model_id, info in self.loaded_models.items() 
                if info.get('is_loaded', False)]
    
    def get_model_usage_stats(self) -> Dict[str, Any]:
        """Get model usage statistics."""
        stats = {
            'total_models': len(self.loaded_models),
            'loaded_models': len(self.get_loaded_models()),
            'model_usage': {}
        }
        
        for model_id, info in self.loaded_models.items():
            stats['model_usage'][model_id] = {
                'is_loaded': info.get('is_loaded', False),
                'usage_count': info.get('usage_count', 0),
                'last_used': info.get('last_used')
            }
        
        return stats


class ResourceMonitor:
    """Monitor system resources for routing decisions."""
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get system memory information."""
        memory = psutil.virtual_memory()
        return {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent_used': memory.percent
        }
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU memory information."""
        try:
            # This would typically use nvidia-ml-py or similar
            # For now, return mock data
            return {
                'total_gb': 32.0,  # RTX 5090
                'available_gb': 25.0,
                'used_gb': 7.0,
                'percent_used': 21.9
            }
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return {
                'total_gb': 0,
                'available_gb': 0,
                'used_gb': 0,
                'percent_used': 0
            }


# Example usage and testing
if __name__ == "__main__":
    async def test_router():
        """Test the model router with sample classifications."""
        router = ModelRouter()
        
        # Mock classification results
        from .query_classifier import ClassificationResult, UseCase
        
        test_classifications = [
            ClassificationResult(
                use_case=UseCase.AGENT,
                confidence=0.9,
                detected_modalities=["text"],
                language="english",
                complexity="medium"
            ),
            ClassificationResult(
                use_case=UseCase.AVATAR,
                confidence=0.8,
                detected_modalities=["image", "text"],
                language="english",
                complexity="high"
            )
        ]
        
        for classification in test_classifications:
            decision = await router.route_query(classification)
            print(f"Use Case: {classification.use_case.value}")
            print(f"Selected Model: {decision.selected_model.model_id}")
            print(f"Confidence: {decision.confidence:.2f}")
            print(f"Reasoning: {decision.reasoning}")
            print(f"Fallback Models: {[m.model_id for m in decision.fallback_models]}")
            print("-" * 50)
    
    # Run test
    asyncio.run(test_router())
