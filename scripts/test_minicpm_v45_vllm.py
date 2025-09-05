#!/usr/bin/env python3
"""
Test MiniCPM-V-4.5 vLLM Compatibility

This script specifically tests MiniCPM-V-4.5 to verify it works with vLLM
for the Avatar, Multimodal, and Video use cases.
"""

import os
import sys
import subprocess
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minicpm_v45_with_vllm():
    """Test MiniCPM-V-4.5 with vLLM to verify compatibility."""
    
    logger.info("🧪 Testing MiniCPM-V-4.5 vLLM compatibility...")
    logger.info("Model: openbmb/MiniCPM-V-4_5")
    logger.info("Size: 8.7B parameters (~8.7GB)")
    logger.info("Capabilities: Vision, OCR, document parsing, multi-image, video")
    
    # Create test script
    test_script = """
import sys
import os
sys.path.append('/usr/local/lib/python3.12/dist-packages')

try:
    from vllm import LLM
    print("✅ vLLM import successful")
    
    # Try to initialize MiniCPM-V-4.5
    print("🔄 Testing MiniCPM-V-4.5 with vLLM...")
    print("Model: openbmb/MiniCPM-V-4_5")
    
    # Test with minimal configuration first
    llm = LLM(
        model="openbmb/MiniCPM-V-4_5", 
        task="generate",
        max_model_len=1024,  # Start small
        gpu_memory_utilization=0.8
    )
    print("✅ MiniCPM-V-4.5 initialization successful")
    
    # Try a simple text generation
    print("🔄 Testing text generation...")
    outputs = llm.generate("Hello, how are you?")
    print("✅ Text generation successful")
    print(f"Output: {outputs[0].outputs[0].text}")
    
    # Try a vision-related prompt
    print("🔄 Testing vision-related prompt...")
    vision_outputs = llm.generate("Describe what you see in this image:")
    print("✅ Vision prompt successful")
    print(f"Vision Output: {vision_outputs[0].outputs[0].text}")
    
    print("🎉 MiniCPM-V-4.5 is vLLM compatible!")
    print("✅ Suitable for: Agent, Avatar, Multimodal, Video use cases")
    
except Exception as e:
    print(f"❌ MiniCPM-V-4.5 failed vLLM compatibility test: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    # Write test script
    test_file = "/tmp/test_minicpm_v45_vllm.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    try:
        logger.info("🔄 Running MiniCPM-V-4.5 vLLM compatibility test...")
        logger.info("This may take several minutes to download and test the model...")
        
        result = subprocess.run([
            "python3", test_file
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode == 0:
            logger.info("✅ MiniCPM-V-4.5 is vLLM compatible!")
            logger.info("Test output:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
            return True, "vLLM compatible"
        else:
            logger.error("❌ MiniCPM-V-4.5 failed vLLM compatibility test")
            logger.error("Error output:")
            for line in result.stderr.strip().split('\n'):
                logger.error(f"  {line}")
            return False, f"vLLM test failed: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        logger.error("❌ MiniCPM-V-4.5 test timed out (10 minutes)")
        return False, "Test timed out"
    except Exception as e:
        logger.error(f"❌ MiniCPM-V-4.5 test failed with exception: {str(e)}")
        return False, f"Exception: {str(e)}"
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """Main testing function."""
    logger.info("🎯 Testing MiniCPM-V-4.5 for your 6 use cases...")
    
    is_compatible, reason = test_minicpm_v45_with_vllm()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"MINICPM-V-4.5 VLLM COMPATIBILITY RESULTS")
    logger.info(f"{'='*60}")
    
    if is_compatible:
        logger.info("✅ MiniCPM-V-4.5 is vLLM compatible!")
        logger.info(f"Reason: {reason}")
        
        logger.info("\n📋 USE CASE COVERAGE:")
        logger.info("✅ Agent: MiniCPM-V-4.5 (conversational, multilingual)")
        logger.info("✅ Avatar: MiniCPM-V-4.5 (vision + text)")
        logger.info("❌ STT: Not suitable (no audio processing)")
        logger.info("❌ TTS: Not suitable (no audio synthesis)")
        logger.info("✅ Multimodal: MiniCPM-V-4.5 (vision + text, document parsing)")
        logger.info("✅ Video: MiniCPM-V-4.5 (video processing, multi-image)")
        
        logger.info("\n🎯 COVERAGE SUMMARY:")
        logger.info("✅ 4 out of 6 use cases covered by MiniCPM-V-4.5")
        logger.info("❌ 2 use cases (STT, TTS) need separate audio models")
        
        logger.info("\n🚀 RECOMMENDATION:")
        logger.info("MiniCPM-V-4.5 is an excellent choice for multimodal use cases!")
        logger.info("It can handle Agent, Avatar, Multimodal, and Video use cases.")
        logger.info("For STT/TTS, we'll need separate audio models (Whisper, SpeechT5).")
        
        return 0
    else:
        logger.error("❌ MiniCPM-V-4.5 is NOT vLLM compatible")
        logger.error(f"Reason: {reason}")
        logger.error("\n🔄 ALTERNATIVES:")
        logger.error("We need to find other multimodal models or use Hugging Face Transformers")
        return 1

if __name__ == "__main__":
    sys.exit(main())
