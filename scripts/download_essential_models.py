#!/usr/bin/env python3
"""
Download Essential Models Script
===============================

This script downloads only the essential models that are confirmed to work:
1. MiniCPM-V-4 (7GB) - Multimodal vision-language model
2. Qwen2.5-7B-Instruct - Text generation
3. Whisper Large v3 - Speech-to-text
4. Coqui TTS models - Text-to-speech

Models are downloaded to /opt/ai-models/models/ directory structure.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EssentialModelDownloader:
    """Downloads only the essential working models"""
    
    def __init__(self):
        self.base_dir = Path("/opt/ai-models/models")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Define essential models that are confirmed to work
        self.essential_models = {
            "multimodal": {
                "description": "Multimodal Vision-Language Model",
                "models": {
                    "minicpm-v-4": "openbmb/MiniCPM-V-4"
                }
            },
            "text_generation": {
                "description": "Text Generation Models",
                "models": {
                    "qwen2.5-7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
                    "phi-2": "microsoft/phi-2"
                }
            },
            "speech_to_text": {
                "description": "Speech-to-Text Models",
                "models": {
                    "whisper-large-v3": "openai/whisper-large-v3"
                }
            },
            "text_to_speech": {
                "description": "Text-to-Speech Models",
                "models": {
                    "coqui-tts": "microsoft/speecht5_tts"
                }
            }
        }
    
    def install_huggingface_hub(self):
        """Install huggingface_hub if not available"""
        try:
            from huggingface_hub import snapshot_download
            logger.info("✅ huggingface_hub already available")
        except ImportError:
            logger.info("📦 Installing huggingface_hub...")
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
            from huggingface_hub import snapshot_download
            logger.info("✅ huggingface_hub installed successfully")
    
    def download_model(self, model_name: str, model_id: str, category: str) -> bool:
        """Download a single model"""
        try:
            model_path = self.base_dir / category / model_name
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
    
    def download_essential_models(self) -> dict:
        """Download all essential models"""
        logger.info("🎯 Starting download of essential models...")
        logger.info("=" * 60)
        
        results = {}
        
        for category, info in self.essential_models.items():
            logger.info(f"\n🚀 Downloading models for: {info['description']}")
            logger.info("-" * 50)
            
            category_results = {}
            models = info["models"]
            
            for model_name, model_id in models.items():
                success = self.download_model(model_name, model_id, category)
                category_results[model_name] = success
                time.sleep(2)  # Small delay between downloads
            
            results[category] = category_results
            
            # Summary for this category
            successful = sum(category_results.values())
            total = len(category_results)
            logger.info(f"📊 {category.upper()}: {successful}/{total} models downloaded successfully")
        
        return results
    
    def generate_summary_report(self, results: dict):
        """Generate a summary report of all downloads"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 ESSENTIAL MODELS DOWNLOAD SUMMARY")
        logger.info("=" * 60)
        
        total_models = 0
        successful_downloads = 0
        
        for category, models in results.items():
            logger.info(f"\n🎯 {category.upper()}: {self.essential_models[category]['description']}")
            logger.info("-" * 40)
            
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
        
        # Show disk usage
        try:
            import shutil
            total_size = sum(f.stat().st_size for f in self.base_dir.rglob('*') if f.is_file())
            size_gb = total_size / (1024**3)
            logger.info(f"  Total Downloaded Size: {size_gb:.2f} GB")
        except Exception as e:
            logger.warning(f"Could not calculate disk usage: {e}")
    
    def run(self):
        """Main execution method"""
        try:
            # Install dependencies
            self.install_huggingface_hub()
            
            # Download essential models
            results = self.download_essential_models()
            
            # Generate summary report
            self.generate_summary_report(results)
            
            logger.info("\n🎉 Essential model download process completed!")
            
        except Exception as e:
            logger.error(f"❌ Fatal error during download process: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    downloader = EssentialModelDownloader()
    downloader.run()

if __name__ == "__main__":
    main()
