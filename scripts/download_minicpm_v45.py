#!/usr/bin/env python3
"""
Download MiniCPM-V-4.5 Model
Downloads the latest MiniCPM-V-4.5 model with enhanced video processing capabilities.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MiniCPMV45Downloader:
    def __init__(self):
        self.model_id = "openbmb/MiniCPM-V-4_5"
        self.base_dir = Path("/opt/ai-models/models")
        self.model_dir = self.base_dir / "multimodal" / "minicpm-v-4_5"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def install_huggingface_hub(self):
        """Install huggingface_hub if not available"""
        try:
            from huggingface_hub import snapshot_download
            logger.info("✅ huggingface_hub already available")
        except ImportError:
            logger.info("📦 Installing huggingface_hub...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "--break-system-packages", "huggingface_hub"
            ], check=True)
            from huggingface_hub import snapshot_download
            logger.info("✅ huggingface_hub installed successfully")
    
    def check_disk_space(self):
        """Check available disk space"""
        statvfs = os.statvfs('/opt/ai-models')
        free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        logger.info(f"💾 Available disk space: {free_space_gb:.1f} GB")
        
        # MiniCPM-V-4.5 is ~8.7B parameters, estimate ~15-20GB needed
        if free_space_gb < 25:
            logger.warning(f"⚠️ Low disk space: {free_space_gb:.1f} GB available")
            logger.warning("   MiniCPM-V-4.5 requires ~15-20GB. Consider freeing up space.")
            return False
        return True
    
    def download_model(self):
        """Download MiniCPM-V-4.5 model"""
        try:
            logger.info("🚀 Starting MiniCPM-V-4.5 download...")
            logger.info(f"📥 Model ID: {self.model_id}")
            logger.info(f"📁 Download location: {self.model_dir}")
            logger.info("=" * 60)
            
            from huggingface_hub import snapshot_download
            
            # Download with progress tracking
            snapshot_download(
                repo_id=self.model_id,
                local_dir=str(self.model_dir),
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            logger.info("✅ MiniCPM-V-4.5 download completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error downloading MiniCPM-V-4.5: {e}")
            return False
    
    def verify_download(self):
        """Verify the downloaded model"""
        try:
            logger.info("🔍 Verifying download...")
            
            # Check for essential files
            essential_files = [
                "config.json",
                "tokenizer.json", 
                "tokenizer_config.json",
                "model.safetensors.index.json"
            ]
            
            missing_files = []
            for file in essential_files:
                file_path = self.model_dir / file
                if not file_path.exists():
                    missing_files.append(file)
                else:
                    logger.info(f"  ✅ {file}")
            
            if missing_files:
                logger.error(f"❌ Missing essential files: {missing_files}")
                return False
            
            # Check for model files
            safetensors_files = list(self.model_dir.glob("*.safetensors"))
            if not safetensors_files:
                logger.error("❌ No .safetensors files found")
                return False
            
            logger.info(f"  ✅ Found {len(safetensors_files)} model files")
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in self.model_dir.rglob('*') if f.is_file())
            size_gb = total_size / (1024**3)
            logger.info(f"  📊 Total model size: {size_gb:.1f} GB")
            
            logger.info("✅ Model verification completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying download: {e}")
            return False
    
    def create_model_info(self):
        """Create model information file"""
        try:
            info_content = f"""# MiniCPM-V-4.5 Model Information

## Model Details
- **Model ID**: {self.model_id}
- **Parameters**: 8.7B
- **Architecture**: minicpmv with 3D-Resampler
- **Download Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Location**: {self.model_dir}

## Capabilities
- **Video Processing**: Temporal context understanding
- **3D-Resampler**: 96x compression rate for video tokens
- **High Refresh Rate**: Up to 10 FPS video understanding
- **Long Video Support**: Efficient extended sequence processing
- **Multi-image Processing**: Simultaneous image handling
- **OCR**: Enhanced text extraction
- **Multilingual**: Multiple language support

## Key Improvements over V-4
- ✅ Temporal context processing (vs frame-by-frame)
- ✅ 3D-Resampler architecture
- ✅ Joint video frame processing
- ✅ Enhanced multimodal capabilities
- ✅ Better long video support

## Usage
```python
from transformers import AutoModel, AutoTokenizer

model = AutoModel.from_pretrained("{self.model_dir}")
tokenizer = AutoTokenizer.from_pretrained("{self.model_dir}")
```

## vLLM Integration
```bash
python -m vllm.entrypoints.api_server \\
  --model {self.model_dir} \\
  --trust-remote-code \\
  --host 0.0.0.0 \\
  --port 8000
```
"""
            
            info_file = self.model_dir / "MODEL_INFO.md"
            with open(info_file, 'w') as f:
                f.write(info_content)
            
            logger.info(f"📄 Model info saved to: {info_file}")
            
        except Exception as e:
            logger.error(f"❌ Error creating model info: {e}")
    
    def run(self):
        """Main download process"""
        logger.info("🎯 MiniCPM-V-4.5 Download Process")
        logger.info("=" * 60)
        
        # Check disk space
        if not self.check_disk_space():
            logger.error("❌ Insufficient disk space. Aborting download.")
            return False
        
        # Install dependencies
        self.install_huggingface_hub()
        
        # Download model
        if not self.download_model():
            logger.error("❌ Download failed. Aborting.")
            return False
        
        # Verify download
        if not self.verify_download():
            logger.error("❌ Verification failed. Download may be incomplete.")
            return False
        
        # Create model info
        self.create_model_info()
        
        logger.info("=" * 60)
        logger.info("🎉 MiniCPM-V-4.5 download process completed successfully!")
        logger.info(f"📁 Model location: {self.model_dir}")
        logger.info("🚀 Ready for deployment with enhanced video processing capabilities!")
        
        return True

def main():
    """Main function"""
    downloader = MiniCPMV45Downloader()
    success = downloader.run()
    
    if success:
        logger.info("✅ All tasks completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Download process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
