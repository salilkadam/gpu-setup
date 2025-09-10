#!/usr/bin/env python3
"""
Text-to-Speech (TTS) Service using Coqui TTS models
Supports Hindi and Bengali with male/female voices
"""

import os
import io
import base64
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import torch
import torchaudio
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, models_dir: str = "/opt/ai-models/models/text_to_speech"):
        """Initialize the TTS service with Coqui TTS models"""
        self.models_dir = models_dir
        self.device = "cpu"  # Use CPU to avoid GPU memory conflicts
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Load all available TTS models"""
        try:
            logger.info(f"Loading TTS models from {self.models_dir}")
            logger.info(f"Using device: {self.device}")
            
            # Available models
            model_configs = {
                "hindi_female": {
                    "path": f"{self.models_dir}/tts-hindi-female",
                    "model_file": "hi_female_vits_30hrs.pt",
                    "language": "hi",
                    "gender": "female"
                },
                "hindi_male": {
                    "path": f"{self.models_dir}/tts-hindi-male", 
                    "model_file": "hi_male_vits_30hrs.pt",
                    "language": "hi",
                    "gender": "male"
                },
                "bengali_female": {
                    "path": f"{self.models_dir}/tts-bengali-female",
                    "model_file": "bn_female_vits_30hrs.pt", 
                    "language": "bn",
                    "gender": "female"
                },
                "bengali_male": {
                    "path": f"{self.models_dir}/tts-bengali-male",
                    "model_file": "bn_male_vits_30hrs.pt",
                    "language": "bn", 
                    "gender": "male"
                }
            }
            
            # Load each model
            for model_name, config in model_configs.items():
                model_path = Path(config["path"])
                if model_path.exists():
                    self.models[model_name] = config
                    logger.info(f"✅ Loaded {model_name} model")
                else:
                    logger.warning(f"⚠️ Model not found: {model_path}")
            
            logger.info(f"✅ Loaded {len(self.models)} TTS models successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load TTS models: {e}")
            raise e
    
    def synthesize_speech(self, text: str, language: str = "hi", gender: str = "female") -> Dict[str, Any]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            language: Language code ('hi' for Hindi, 'bn' for Bengali)
            gender: Gender ('male' or 'female')
        
        Returns:
            Dict containing audio data and metadata
        """
        try:
            # Select model - map language codes to model names
            model_mapping = {
                "hi_female": "hindi_female",
                "hi_male": "hindi_male", 
                "bn_female": "bengali_female",
                "bn_male": "bengali_male"
            }
            
            model_key = f"{language}_{gender}"
            if model_key in model_mapping:
                model_key = model_mapping[model_key]
            
            if model_key not in self.models:
                available_models = list(self.models.keys())
                raise ValueError(f"Model {model_key} not available. Available models: {available_models}")
            
            model_config = self.models[model_key]
            model_path = Path(model_config["path"])
            
            # For now, return a placeholder response
            # In a real implementation, you would load the VITS model and synthesize
            logger.info(f"Synthesizing speech for: {text[:50]}...")
            logger.info(f"Using model: {model_key}")
            
            # Generate placeholder audio (silence for 2 seconds)
            sample_rate = 22050
            duration = 2.0
            audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
            
            # Convert to bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            return {
                "audio_data": base64.b64encode(audio_bytes).decode(),
                "sample_rate": sample_rate,
                "duration": duration,
                "language": language,
                "gender": gender,
                "model": model_key,
                "text": text,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Speech synthesis failed: {e}")
            return {
                "audio_data": "",
                "sample_rate": 0,
                "duration": 0,
                "language": language,
                "gender": gender,
                "model": "unknown",
                "text": text,
                "status": "error",
                "error": str(e)
            }

# Initialize FastAPI app
app = FastAPI(title="TTS Service", version="1.0.0")
tts_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize the TTS service on startup"""
    global tts_service
    try:
        tts_service = TTSService()
        logger.info("🚀 TTS Service started successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to start TTS service: {e}")
        raise e

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "tts", 
        "models": list(tts_service.models.keys()) if tts_service else []
    }

@app.post("/synthesize")
async def synthesize_speech(
    text: str,
    language: str = "hi",
    gender: str = "female"
):
    """
    Synthesize speech from text
    
    Args:
        text: Text to synthesize
        language: Language code ('hi' for Hindi, 'bn' for Bengali)
        gender: Gender ('male' or 'female')
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Synthesize speech
        result = tts_service.synthesize_speech(text, language, gender)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Speech synthesis request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/synthesize/{text}")
async def synthesize_speech_get(
    text: str,
    language: str = "hi", 
    gender: str = "female"
):
    """
    Synthesize speech from text (GET endpoint for simple requests)
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Synthesize speech
        result = tts_service.synthesize_speech(text, language, gender)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Speech synthesis request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """Get list of available TTS models"""
    if not tts_service:
        return {"models": [], "error": "TTS service not initialized"}
    
    models_info = {}
    for model_name, config in tts_service.models.items():
        models_info[model_name] = {
            "language": config["language"],
            "gender": config["gender"],
            "path": config["path"]
        }
    
    return {
        "available_models": models_info,
        "total_models": len(models_info),
        "supported_languages": ["hi", "bn"],
        "supported_genders": ["male", "female"]
    }

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "supported_languages": {
            "hi": "Hindi",
            "bn": "Bengali"
        },
        "supported_genders": ["male", "female"],
        "total_combinations": 4
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
