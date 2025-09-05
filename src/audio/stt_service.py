#!/usr/bin/env python3
"""
Speech-to-Text (STT) Service using Whisper Large v3
Supports 99 languages including Indian languages
"""

import os
import io
import base64
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, model_path: str = "/opt/ai-models/models/whisper-large-v3"):
        """Initialize the STT service with Whisper Large v3"""
        self.model_path = model_path
        self.device = "cpu"  # Use CPU to avoid GPU memory conflicts
        self.model = None
        self.processor = None
        self.load_model()
    
    def load_model(self):
        """Load the Whisper model and processor"""
        try:
            logger.info(f"Loading Whisper model from {self.model_path}")
            logger.info(f"Using device: {self.device}")
            
            # Load processor and model
            self.processor = WhisperProcessor.from_pretrained(self.model_path)
            self.model = WhisperForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            # Move model to device
            self.model = self.model.to(self.device)
            
            logger.info("✅ Whisper model loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise e
    
    def transcribe_audio(self, audio_data: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Raw audio bytes
            language: Optional language code (e.g., 'hi', 'ta', 'bn', 'te')
        
        Returns:
            Dict containing transcription results
        """
        try:
            # Load audio using librosa
            audio_array, sample_rate = librosa.load(io.BytesIO(audio_data), sr=16000)
            
            # Process audio
            inputs = self.processor(
                audio_array, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                if language:
                    # Force specific language
                    generated_ids = self.model.generate(
                        inputs["input_features"],
                        language=language,
                        task="transcribe"
                    )
                else:
                    # Auto-detect language
                    generated_ids = self.model.generate(
                        inputs["input_features"],
                        task="transcribe"
                    )
            
            # Decode transcription
            transcription = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            # Get detected language if not specified
            detected_language = language
            if not detected_language:
                # Extract language from model output
                detected_language = self.processor.tokenizer.language
            
            return {
                "transcription": transcription,
                "language": detected_language,
                "confidence": 1.0,  # Whisper doesn't provide confidence scores
                "model": "whisper-large-v3",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return {
                "transcription": "",
                "language": language or "unknown",
                "confidence": 0.0,
                "model": "whisper-large-v3",
                "status": "error",
                "error": str(e)
            }

# Initialize FastAPI app
app = FastAPI(title="STT Service", version="1.0.0")
stt_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize the STT service on startup"""
    global stt_service
    try:
        stt_service = STTService()
        logger.info("🚀 STT Service started successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to start STT service: {e}")
        raise e

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stt", "model": "whisper-large-v3"}

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Transcribe uploaded audio file
    
    Args:
        file: Audio file (wav, mp3, m4a, etc.)
        language: Optional language code (hi, ta, bn, te, gu, mr, pa, ur, kn, ml, or, as)
    """
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Transcribe
        result = stt_service.transcribe_audio(audio_data, language)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"❌ Transcription request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe_base64")
async def transcribe_base64(
    audio_base64: str,
    language: Optional[str] = None
):
    """
    Transcribe base64 encoded audio
    
    Args:
        audio_base64: Base64 encoded audio data
        language: Optional language code
    """
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)
        
        # Transcribe
        result = stt_service.transcribe_audio(audio_data, language)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"❌ Base64 transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported Indian languages"""
    indian_languages = {
        "hi": "Hindi",
        "ta": "Tamil", 
        "te": "Telugu",
        "bn": "Bengali",
        "gu": "Gujarati",
        "mr": "Marathi",
        "pa": "Punjabi",
        "ur": "Urdu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "or": "Odia",
        "as": "Assamese"
    }
    
    return {
        "supported_languages": indian_languages,
        "total_languages": len(indian_languages),
        "model": "whisper-large-v3"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
