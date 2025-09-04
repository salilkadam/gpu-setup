"""
Query Classification System

This module provides intelligent classification of incoming queries to determine
the appropriate use case and model selection.
"""

import re
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UseCase(Enum):
    """Enumeration of supported use cases."""
    AVATAR = "avatar"
    STT = "stt"
    TTS = "tts"
    AGENT = "agent"
    MULTIMODAL = "multimodal"
    VIDEO = "video"


@dataclass
class ClassificationResult:
    """Result of query classification."""
    use_case: UseCase
    confidence: float
    detected_modalities: List[str]
    language: Optional[str] = None
    complexity: str = "medium"  # low, medium, high
    metadata: Dict[str, Any] = None


class QueryClassifier:
    """
    Intelligent query classifier that determines the appropriate use case
    and model selection based on query content and context.
    """
    
    def __init__(self):
        """Initialize the query classifier with intent patterns."""
        self.intent_patterns = self._load_intent_patterns()
        self.language_patterns = self._load_language_patterns()
        self.complexity_indicators = self._load_complexity_indicators()
        
    def _load_intent_patterns(self) -> Dict[UseCase, List[str]]:
        """Load intent detection patterns for each use case."""
        return {
            UseCase.AVATAR: [
                "lip sync", "talking head", "avatar", "face", "facial",
                "mouth", "speech animation", "face animation", "lip movement",
                "facial expression", "head movement", "gesture"
            ],
            UseCase.STT: [
                "speech to text", "transcribe", "transcription", "audio",
                "voice", "speech", "listen", "hear", "audio input",
                "voice recognition", "speech recognition", "dictation"
            ],
            UseCase.TTS: [
                "text to speech", "synthesize", "voice", "speak", "audio output",
                "voice generation", "speech synthesis", "narrate", "read aloud",
                "voice clone", "voice conversion"
            ],
            UseCase.AGENT: [
                "code", "programming", "debug", "analyze", "reasoning",
                "generate", "create", "write", "explain", "solve",
                "algorithm", "function", "class", "script", "api",
                "database", "query", "search", "filter", "process"
            ],
            UseCase.MULTIMODAL: [
                "image", "picture", "photo", "visual", "see", "look",
                "describe", "caption", "analyze image", "image analysis",
                "visual understanding", "image generation", "draw", "paint"
            ],
            UseCase.VIDEO: [
                "video", "temporal", "sequence", "motion", "movement",
                "frame", "clip", "movie", "animation", "video analysis",
                "video understanding", "video generation", "timeline"
            ]
        }
    
    def _load_language_patterns(self) -> Dict[str, List[str]]:
        """Load language detection patterns."""
        return {
            "hindi": ["हिंदी", "hindi", "हिन्दी"],
            "english": ["english", "eng", "en"],
            "tamil": ["தமிழ்", "tamil", "tam"],
            "telugu": ["తెలుగు", "telugu", "tel"],
            "bengali": ["বাংলা", "bengali", "ben"],
            "marathi": ["मराठी", "marathi", "mar"],
            "gujarati": ["ગુજરાતી", "gujarati", "guj"],
            "kannada": ["ಕನ್ನಡ", "kannada", "kan"],
            "malayalam": ["മലയാളം", "malayalam", "mal"],
            "punjabi": ["ਪੰਜਾਬੀ", "punjabi", "pun"]
        }
    
    def _load_complexity_indicators(self) -> Dict[str, List[str]]:
        """Load complexity indicators for query difficulty assessment."""
        return {
            "low": [
                "simple", "basic", "easy", "quick", "fast", "short",
                "brief", "summary", "overview"
            ],
            "high": [
                "complex", "advanced", "detailed", "comprehensive",
                "thorough", "in-depth", "analysis", "research",
                "optimization", "performance", "scalability"
            ]
        }
    
    async def classify_query(
        self, 
        query: str, 
        modality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classify a query to determine the appropriate use case.
        
        Args:
            query: The input query text
            modality: Optional modality hint (text, image, audio, video)
            context: Optional context information
            
        Returns:
            ClassificationResult with use case, confidence, and metadata
        """
        try:
            # Normalize query
            normalized_query = self._normalize_query(query)
            
            # Detect modalities
            detected_modalities = self._detect_modalities(normalized_query, modality)
            
            # Detect language
            language = self._detect_language(normalized_query)
            
            # Assess complexity
            complexity = self._assess_complexity(normalized_query)
            
            # Classify use case
            use_case, confidence = self._classify_use_case(
                normalized_query, detected_modalities, context
            )
            
            # Create metadata
            metadata = {
                "original_query": query,
                "normalized_query": normalized_query,
                "modality_hint": modality,
                "context": context or {},
                "classification_method": "pattern_matching"
            }
            
            return ClassificationResult(
                use_case=use_case,
                confidence=confidence,
                detected_modalities=detected_modalities,
                language=language,
                complexity=complexity,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            # Return default classification
            return ClassificationResult(
                use_case=UseCase.AGENT,
                confidence=0.5,
                detected_modalities=["text"],
                language="english",
                complexity="medium",
                metadata={"error": str(e)}
            )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query text for better pattern matching."""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove special characters but keep important ones
        normalized = re.sub(r'[^\w\s\-\.\,\!\?]', ' ', normalized)
        
        return normalized
    
    def _detect_modalities(self, query: str, modality_hint: Optional[str] = None) -> List[str]:
        """Detect input modalities from query text."""
        modalities = []
        
        # Check for modality hints
        if modality_hint:
            modalities.append(modality_hint.lower())
        
        # Detect from query text
        modality_keywords = {
            "image": ["image", "picture", "photo", "visual", "see", "look"],
            "audio": ["audio", "sound", "voice", "speech", "listen", "hear"],
            "video": ["video", "movie", "clip", "animation", "motion"],
            "text": ["text", "write", "type", "input", "prompt"]
        }
        
        for modality, keywords in modality_keywords.items():
            if any(keyword in query for keyword in keywords):
                if modality not in modalities:
                    modalities.append(modality)
        
        # Default to text if no modalities detected
        if not modalities:
            modalities = ["text"]
        
        return modalities
    
    def _detect_language(self, query: str) -> Optional[str]:
        """Detect the primary language of the query."""
        for language, patterns in self.language_patterns.items():
            if any(pattern in query for pattern in patterns):
                return language
        
        # Default to English if no specific language detected
        return "english"
    
    def _assess_complexity(self, query: str) -> str:
        """Assess the complexity of the query."""
        # Check for high complexity indicators
        if any(indicator in query for indicator in self.complexity_indicators["high"]):
            return "high"
        
        # Check for low complexity indicators
        if any(indicator in query for indicator in self.complexity_indicators["low"]):
            return "low"
        
        # Default to medium complexity
        return "medium"
    
    def _classify_use_case(
        self, 
        query: str, 
        modalities: List[str], 
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[UseCase, float]:
        """Classify the use case based on query content and modalities."""
        scores = {}
        
        # Score each use case based on pattern matching
        for use_case, patterns in self.intent_patterns.items():
            score = 0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                if pattern in query:
                    score += 1
            
            # Normalize score
            scores[use_case] = score / total_patterns if total_patterns > 0 else 0
        
        # Apply modality-based adjustments
        if "image" in modalities or "video" in modalities:
            scores[UseCase.MULTIMODAL] *= 1.5
            scores[UseCase.VIDEO] *= 1.3
            scores[UseCase.AVATAR] *= 1.2
        
        if "audio" in modalities:
            scores[UseCase.STT] *= 1.5
            scores[UseCase.TTS] *= 1.3
        
        # Apply context-based adjustments
        if context:
            if context.get("has_image", False):
                scores[UseCase.MULTIMODAL] *= 1.3
                scores[UseCase.AVATAR] *= 1.2
            
            if context.get("has_audio", False):
                scores[UseCase.STT] *= 1.3
                scores[UseCase.TTS] *= 1.2
            
            if context.get("has_video", False):
                scores[UseCase.VIDEO] *= 1.4
                scores[UseCase.MULTIMODAL] *= 1.2
        
        # Find the best use case
        best_use_case = max(scores, key=scores.get)
        confidence = scores[best_use_case]
        
        # Ensure minimum confidence threshold
        if confidence < 0.1:
            best_use_case = UseCase.AGENT
            confidence = 0.5
        
        return best_use_case, min(confidence, 1.0)
    
    def get_supported_use_cases(self) -> List[UseCase]:
        """Get list of supported use cases."""
        return list(UseCase)
    
    def get_use_case_description(self, use_case: UseCase) -> str:
        """Get description of a specific use case."""
        descriptions = {
            UseCase.AVATAR: "Talking head avatars and lip sync generation",
            UseCase.STT: "Speech-to-text conversion for Indian languages",
            UseCase.TTS: "Text-to-speech synthesis for Indian languages",
            UseCase.AGENT: "Content generation and executing agents",
            UseCase.MULTIMODAL: "Multi-modal temporal agentic RAG",
            UseCase.VIDEO: "Video-to-text understanding and content generation"
        }
        return descriptions.get(use_case, "Unknown use case")


# Example usage and testing
if __name__ == "__main__":
    async def test_classifier():
        """Test the query classifier with sample queries."""
        classifier = QueryClassifier()
        
        test_queries = [
            "Generate a talking head avatar with lip sync",
            "Transcribe this audio file to text",
            "Convert this text to speech in Hindi",
            "Write a Python function to sort a list",
            "Analyze this image and describe what you see",
            "Process this video and extract key frames"
        ]
        
        for query in test_queries:
            result = await classifier.classify_query(query)
            print(f"Query: {query}")
            print(f"Use Case: {result.use_case.value}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Modalities: {result.detected_modalities}")
            print(f"Language: {result.language}")
            print(f"Complexity: {result.complexity}")
            print("-" * 50)
    
    # Run test
    asyncio.run(test_classifier())
