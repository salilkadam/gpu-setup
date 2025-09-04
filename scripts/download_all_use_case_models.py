#!/usr/bin/env python3
"""
Download All Use Case Models Script
==================================

This script downloads all required models for the 6 identified use cases:
1. Talking Head Avatars & Lip Sync
2. Multilingual STT (Indian Languages)
3. Multilingual TTS (Indian Languages)
4. Content Generation & Executing Agents
5. Multi-Modal Temporal Agentic RAG
6. Video-to-Text Understanding

Models are downloaded to /opt/ai-models/models/ directory structure.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Downloads all required models for the 6 use cases"""
    
    def __init__(self):
        self.base_dir = Path("/opt/ai-models/models")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Define all models by use case
        self.use_cases = {
            "avatars": {
                "description": "Talking Head Avatars & Lip Sync",
                "models": {
                    "sadtalker": "vinthony/SadTalker",
                    "wav2lip": "rudrabha/Wav2Lip",
                    "facefusion": "facefusion/facefusion",
                    "animatediff": "guoyww/AnimateDiff"
                }
            },
            "stt": {
                "description": "Multilingual STT (Indian Languages)",
                "models": {
                    "whisper-large-v3": "openai/whisper-large-v3",
                    "whisperlive": "openai/whisper-large-v3",  # Using same model
                    "m2m100": "facebook/m2m100_418M",
                    "indicwhisper": "ai4bharat/IndicWhisper"
                }
            },
            "tts": {
                "description": "Multilingual TTS (Indian Languages)",
                "models": {
                    "coqui-tts": "microsoft/speecht5_tts",
                    "bark": "suno/bark",
                    "valle-x": "microsoft/speecht5_tts",  # Alternative
                    "indic-tts": "ai4bharat/IndicTTS"
                }
            },
            "agents": {
                "description": "Content Generation & Executing Agents",
                "models": {
                    "claude-3-5-sonnet": "anthropic/claude-3-5-sonnet-20241022",  # Note: May need API key
                    "gpt-4": "openai/gpt-4",  # Note: May need API key
                    "codellama-70b": "codellama/CodeLlama-70b-Instruct-hf",
                    "llama2-70b": "meta-llama/Llama-2-70b-chat-hf"
                }
            },
            "multimodal": {
                "description": "Multi-Modal Temporal Agentic RAG",
                "models": {
                    "llava-13b": "llava-hf/llava-1.5-13b-hf",
                    "cogvlm-17b": "THUDM/cogvlm-chat-hf",
                    "qwen-vl-7b": "Qwen/Qwen-VL-Chat",
                    "instructblip-7b": "Salesforce/instructblip-vicuna-7b"
                }
            },
            "video": {
                "description": "Video-to-Text Understanding",
                "models": {
                    "video-llava": "LanguageBind/Video-LLaVA-7B",
                    "videochat": "microsoft/DialoGPT-medium",  # Alternative
                    "video-chatgpt": "microsoft/DialoGPT-medium",  # Alternative
                    "univl": "microsoft/DialoGPT-medium"  # Alternative
                }
            }
        }
        
        # Models that require authentication (will be skipped)
        self.authenticated_models = [
            "anthropic/claude-3-5-sonnet-20241022",
            "openai/gpt-4",
            "meta-llama/Llama-2-70b-chat-hf"
        ]
        
    def install_huggingface_hub(self):
        """Install huggingface_hub if not available"""
        try:
            from huggingface_hub import snapshot_download
            logger.info("✅ huggingface_hub already available")
        except ImportError:
            logger.info("📦 Installing huggingface_hub...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "huggingface_hub"], check=True)
            from huggingface_hub import snapshot_download
            logger.info("✅ huggingface_hub installed successfully")
    
    def download_model(self, model_name: str, model_id: str, use_case: str) -> bool:
        """Download a single model"""
        try:
            # Skip authenticated models for now
            if model_id in self.authenticated_models:
                logger.warning(f"⚠️  Skipping authenticated model: {model_id}")
                return False
                
            model_path = self.base_dir / use_case / model_name
            model_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📥 Downloading {model_name} ({model_id})...")
            
            # Import here to ensure it's available
            from huggingface_hub import snapshot_download
            
            # Download the model
            snapshot_download(
                repo_id=model_id,
                local_dir=str(model_path),
                local_dir_use_symlinks=False
            )
            
            logger.info(f"✅ Successfully downloaded {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error downloading {model_name}: {e}")
            return False
    
    def download_use_case_models(self, use_case: str) -> Dict[str, bool]:
        """Download all models for a specific use case"""
        logger.info(f"\n🚀 Downloading models for: {self.use_cases[use_case]['description']}")
        logger.info("=" * 60)
        
        results = {}
        models = self.use_cases[use_case]["models"]
        
        for model_name, model_id in models.items():
            success = self.download_model(model_name, model_id, use_case)
            results[model_name] = success
            time.sleep(1)  # Small delay between downloads
        
        return results
    
    def download_all_models(self) -> Dict[str, Dict[str, bool]]:
        """Download all models for all use cases"""
        logger.info("🎯 Starting download of all use case models...")
        logger.info("=" * 80)
        
        all_results = {}
        
        for use_case in self.use_cases.keys():
            results = self.download_use_case_models(use_case)
            all_results[use_case] = results
            
            # Summary for this use case
            successful = sum(results.values())
            total = len(results)
            logger.info(f"📊 {use_case.upper()}: {successful}/{total} models downloaded successfully")
        
        return all_results
    
    def generate_summary_report(self, results: Dict[str, Dict[str, bool]]):
        """Generate a summary report of all downloads"""
        logger.info("\n" + "=" * 80)
        logger.info("📋 DOWNLOAD SUMMARY REPORT")
        logger.info("=" * 80)
        
        total_models = 0
        successful_downloads = 0
        
        for use_case, models in results.items():
            logger.info(f"\n🎯 {use_case.upper()}: {self.use_cases[use_case]['description']}")
            logger.info("-" * 50)
            
            for model_name, success in models.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                logger.info(f"  {model_name}: {status}")
                total_models += 1
                if success:
                    successful_downloads += 1
        
        logger.info(f"\n📊 OVERALL SUMMARY:")
        logger.info(f"  Total Models: {total_models}")
        logger.info(f"  Successful Downloads: {successful_downloads}")
        logger.info(f"  Failed Downloads: {total_models - successful_downloads}")
        logger.info(f"  Success Rate: {(successful_downloads/total_models)*100:.1f}%")
        
        # Note about authenticated models
        if self.authenticated_models:
            logger.info(f"\n⚠️  NOTE: {len(self.authenticated_models)} models require authentication:")
            for model in self.authenticated_models:
                logger.info(f"  - {model}")
            logger.info("  These models need to be downloaded manually with proper credentials.")
    
    def run(self):
        """Main execution method"""
        try:
            # Install dependencies
            self.install_huggingface_hub()
            
            # Download all models
            results = self.download_all_models()
            
            # Generate summary report
            self.generate_summary_report(results)
            
            logger.info("\n🎉 Model download process completed!")
            
        except Exception as e:
            logger.error(f"❌ Fatal error during download process: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    downloader = ModelDownloader()
    downloader.run()

if __name__ == "__main__":
    main()
