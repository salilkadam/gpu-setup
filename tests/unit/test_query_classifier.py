"""
Unit tests for the Query Classifier.

This module tests the query classification functionality.
"""

import pytest
import asyncio
from src.routing.query_classifier import QueryClassifier, UseCase, ClassificationResult


class TestQueryClassifier:
    """Test cases for QueryClassifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create a QueryClassifier instance for testing."""
        return QueryClassifier()
    
    @pytest.mark.asyncio
    async def test_classify_agent_query(self, classifier):
        """Test classification of agent-related queries."""
        query = "Write a Python function to sort a list"
        result = await classifier.classify_query(query)
        
        assert result.use_case == UseCase.AGENT
        assert result.confidence > 0.5
        assert "text" in result.detected_modalities
        assert result.language == "english"
    
    @pytest.mark.asyncio
    async def test_classify_avatar_query(self, classifier):
        """Test classification of avatar-related queries."""
        query = "Generate a talking head avatar with lip sync"
        result = await classifier.classify_query(query)
        
        assert result.use_case == UseCase.AVATAR
        assert result.confidence > 0.5
        assert result.language == "english"
    
    @pytest.mark.asyncio
    async def test_classify_stt_query(self, classifier):
        """Test classification of speech-to-text queries."""
        query = "Transcribe this audio file to text"
        result = await classifier.classify_query(query)
        
        assert result.use_case == UseCase.STT
        assert result.confidence > 0.5
        assert "audio" in result.detected_modalities
    
    @pytest.mark.asyncio
    async def test_classify_tts_query(self, classifier):
        """Test classification of text-to-speech queries."""
        query = "Convert this text to speech in Hindi"
        result = await classifier.classify_query(query)
        
        assert result.use_case == UseCase.TTS
        assert result.confidence > 0.5
        assert result.language == "hindi"
    
    @pytest.mark.asyncio
    async def test_classify_multimodal_query(self, classifier):
        """Test classification of multimodal queries."""
        query = "Analyze this image and describe what you see"
        result = await classifier.classify_query(query)
        
        assert result.use_case == UseCase.MULTIMODAL
        assert result.confidence > 0.5
        assert "image" in result.detected_modalities
    
    @pytest.mark.asyncio
    async def test_classify_video_query(self, classifier):
        """Test classification of video-related queries."""
        query = "Process this video and extract key frames"
        result = await classifier.classify_query(query)
        
        assert result.use_case == UseCase.VIDEO
        assert result.confidence > 0.5
        assert "video" in result.detected_modalities
    
    @pytest.mark.asyncio
    async def test_language_detection(self, classifier):
        """Test language detection functionality."""
        # Test Hindi
        hindi_query = "हिंदी में जवाब दें"
        result = await classifier.classify_query(hindi_query)
        assert result.language == "hindi"
        
        # Test Tamil
        tamil_query = "தமிழில் பதில் கொடுங்கள்"
        result = await classifier.classify_query(tamil_query)
        assert result.language == "tamil"
        
        # Test English (default)
        english_query = "Answer in English"
        result = await classifier.classify_query(english_query)
        assert result.language == "english"
    
    @pytest.mark.asyncio
    async def test_complexity_assessment(self, classifier):
        """Test complexity assessment functionality."""
        # Test high complexity
        complex_query = "Perform a comprehensive analysis of the system architecture"
        result = await classifier.classify_query(complex_query)
        assert result.complexity == "high"
        
        # Test low complexity
        simple_query = "Give me a simple summary"
        result = await classifier.classify_query(simple_query)
        assert result.complexity == "low"
        
        # Test medium complexity (default)
        medium_query = "Write a function"
        result = await classifier.classify_query(medium_query)
        assert result.complexity == "medium"
    
    @pytest.mark.asyncio
    async def test_modality_detection(self, classifier):
        """Test modality detection functionality."""
        # Test image modality
        image_query = "Look at this picture"
        result = await classifier.classify_query(image_query, modality="image")
        assert "image" in result.detected_modalities
        
        # Test audio modality
        audio_query = "Listen to this audio"
        result = await classifier.classify_query(audio_query, modality="audio")
        assert "audio" in result.detected_modalities
        
        # Test video modality
        video_query = "Watch this video"
        result = await classifier.classify_query(video_query, modality="video")
        assert "video" in result.detected_modalities
    
    @pytest.mark.asyncio
    async def test_context_influence(self, classifier):
        """Test how context influences classification."""
        query = "Process this data"
        
        # Without context
        result1 = await classifier.classify_query(query)
        
        # With image context
        result2 = await classifier.classify_query(query, context={"has_image": True})
        
        # With audio context
        result3 = await classifier.classify_query(query, context={"has_audio": True})
        
        # Results should be different based on context
        assert result1.use_case != result2.use_case or result1.confidence != result2.confidence
        assert result1.use_case != result3.use_case or result1.confidence != result3.confidence
    
    @pytest.mark.asyncio
    async def test_error_handling(self, classifier):
        """Test error handling in classification."""
        # Test with empty query
        result = await classifier.classify_query("")
        assert result.use_case == UseCase.AGENT  # Default fallback
        assert result.confidence == 0.5  # Default confidence
        
        # Test with None query
        result = await classifier.classify_query(None)
        assert result.use_case == UseCase.AGENT  # Default fallback
        assert result.confidence == 0.5  # Default confidence
    
    def test_get_supported_use_cases(self, classifier):
        """Test getting supported use cases."""
        use_cases = classifier.get_supported_use_cases()
        
        assert len(use_cases) == 6
        assert UseCase.AVATAR in use_cases
        assert UseCase.STT in use_cases
        assert UseCase.TTS in use_cases
        assert UseCase.AGENT in use_cases
        assert UseCase.MULTIMODAL in use_cases
        assert UseCase.VIDEO in use_cases
    
    def test_get_use_case_description(self, classifier):
        """Test getting use case descriptions."""
        description = classifier.get_use_case_description(UseCase.AGENT)
        assert "Content generation" in description
        
        description = classifier.get_use_case_description(UseCase.AVATAR)
        assert "Talking head" in description
        
        description = classifier.get_use_case_description(UseCase.STT)
        assert "Speech-to-text" in description


# Example test execution
if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        """Run the tests manually."""
        classifier = QueryClassifier()
        
        # Test agent query
        result = await classifier.classify_query("Write a Python function")
        print(f"Agent query: {result.use_case.value}, confidence: {result.confidence}")
        
        # Test avatar query
        result = await classifier.classify_query("Generate talking head avatar")
        print(f"Avatar query: {result.use_case.value}, confidence: {result.confidence}")
        
        # Test STT query
        result = await classifier.classify_query("Transcribe audio to text")
        print(f"STT query: {result.use_case.value}, confidence: {result.confidence}")
        
        # Test TTS query
        result = await classifier.classify_query("Convert text to speech")
        print(f"TTS query: {result.use_case.value}, confidence: {result.confidence}")
        
        # Test multimodal query
        result = await classifier.classify_query("Analyze this image")
        print(f"Multimodal query: {result.use_case.value}, confidence: {result.confidence}")
        
        # Test video query
        result = await classifier.classify_query("Process this video")
        print(f"Video query: {result.use_case.value}, confidence: {result.confidence}")
    
    asyncio.run(run_tests())
