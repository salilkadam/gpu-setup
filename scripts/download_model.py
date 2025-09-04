#!/usr/bin/env python3
"""
Model Download Script for Docker-based Model Management
Downloads AI models from Hugging Face Hub
"""

import os
import sys
import time
import signal
from pathlib import Path

def download_model(repo_id, target_dir, model_name):
    """Download a model from Hugging Face Hub"""
    
    # Set timeout for download (2 hours)
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Download timed out after 2 hours for {model_name}")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(7200)  # 2 hours timeout
    
    try:
        print(f"🚀 Starting download of {model_name} from {repo_id}")
        print(f"📁 Target directory: {target_dir}")
        print(f"⏰ Download timeout set to 2 hours")
        
        # Install huggingface_hub if not available
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            print("📦 Installing huggingface_hub...")
            os.system("pip install huggingface_hub")
            from huggingface_hub import snapshot_download
        
        # Create target directory
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"⬇️  Downloading {model_name}...")
        start_time = time.time()
        
        # Get Hugging Face token from environment
        hf_token = os.environ.get('HF_TOKEN')
        
        # Download the model with progress tracking
        download_kwargs = {
            'repo_id': repo_id,
            'local_dir': target_dir,
            'local_dir_use_symlinks': False,
            'resume_download': True,
            'max_workers': 4,  # Parallel downloads
            'tqdm_class': None  # Disable tqdm to avoid Docker issues
        }
        
        # Add token if available
        if hf_token:
            download_kwargs['token'] = hf_token
            print(f"🔑 Using Hugging Face token for authentication")
        
        print(f"🚀 Starting download... This may take a while for large models.")
        print(f"📊 Download will resume if interrupted.")
        
        snapshot_download(**download_kwargs)
        
        download_time = time.time() - start_time
        
        # Calculate size
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except OSError:
                    pass
        
        # Convert to human readable format
        def human_readable_size(size_bytes):
            if size_bytes == 0:
                return "0B"
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            return f"{size_bytes:.1f}{size_names[i]}"
        
        print(f"✅ {model_name} downloaded successfully!")
        print(f"📊 Download statistics:")
        print(f"   - Time: {download_time:.1f} seconds")
        print(f"   - Size: {human_readable_size(total_size)}")
        print(f"   - Files: {file_count}")
        print(f"   - Location: {target_dir}")
        
        signal.alarm(0)  # Cancel timeout
        return True
        
    except TimeoutError as e:
        print(f"⏰ {e}")
        print(f"💡 You can resume the download by running the command again")
        return False
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        return False
    finally:
        signal.alarm(0)  # Cancel timeout

def main():
    """Main function"""
    if len(sys.argv) != 4:
        print("Usage: python download_model.py <repo_id> <target_dir> <model_name>")
        print("Example: python download_model.py mistralai/Mistral-7B-Instruct-v0.2 /app/model mistral-7b")
        sys.exit(1)
    
    repo_id = sys.argv[1]
    target_dir = sys.argv[2]
    model_name = sys.argv[3]
    
    print(f"🐳 Docker-based Model Download")
    print(f"==============================")
    
    success = download_model(repo_id, target_dir, model_name)
    
    if success:
        print(f"\n🎉 {model_name} is ready for use!")
        sys.exit(0)
    else:
        print(f"\n💥 Failed to download {model_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()
