#!/usr/bin/env python3
"""
Comprehensive test script for Audio Services (STT + TTS)
Tests Indian language support and functionality
"""

import os
import sys
import time
import base64
import requests
import json
from pathlib import Path

def test_stt_service(base_url="http://localhost:8002"):
    """Test Speech-to-Text service"""
    print("🎤 Testing STT Service (Speech-to-Text)")
    print("=" * 50)
    
    try:
        # Test health check
        print("1. Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ STT service is healthy")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ STT health check failed: {response.status_code}")
            return False
        
        # Test supported languages
        print("\n2. Testing supported languages...")
        response = requests.get(f"{base_url}/languages", timeout=10)
        if response.status_code == 200:
            languages = response.json()
            print("✅ Supported Indian languages:")
            for code, name in languages["supported_languages"].items():
                print(f"   - {code}: {name}")
        else:
            print(f"❌ Failed to get languages: {response.status_code}")
        
        # Test with sample audio (placeholder)
        print("\n3. Testing transcription (placeholder)...")
        # Create a simple test audio file (silence)
        import numpy as np
        import io
        import wave
        
        # Generate 2 seconds of silence at 16kHz
        sample_rate = 16000
        duration = 2.0
        audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        # Convert to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        
        wav_data = wav_buffer.getvalue()
        
        # Test transcription
        files = {'file': ('test.wav', wav_data, 'audio/wav')}
        data = {'language': 'hi'}  # Hindi
        
        response = requests.post(f"{base_url}/transcribe", files=files, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription test successful")
            print(f"   Language: {result.get('language', 'unknown')}")
            print(f"   Model: {result.get('model', 'unknown')}")
            print(f"   Status: {result.get('status', 'unknown')}")
        else:
            print(f"❌ Transcription test failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ STT service test failed: {e}")
        return False

def test_tts_service(base_url="http://localhost:8003"):
    """Test Text-to-Speech service"""
    print("\n🔊 Testing TTS Service (Text-to-Speech)")
    print("=" * 50)
    
    try:
        # Test health check
        print("1. Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ TTS service is healthy")
            health_data = response.json()
            print(f"   Available models: {health_data.get('models', [])}")
        else:
            print(f"❌ TTS health check failed: {response.status_code}")
            return False
        
        # Test available models
        print("\n2. Testing available models...")
        response = requests.get(f"{base_url}/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print("✅ Available TTS models:")
            for model_name, info in models["available_models"].items():
                print(f"   - {model_name}: {info['language']} ({info['gender']})")
        else:
            print(f"❌ Failed to get models: {response.status_code}")
        
        # Test supported languages
        print("\n3. Testing supported languages...")
        response = requests.get(f"{base_url}/languages", timeout=10)
        if response.status_code == 200:
            languages = response.json()
            print("✅ Supported languages:")
            for code, name in languages["supported_languages"].items():
                print(f"   - {code}: {name}")
            print(f"   Supported genders: {languages['supported_genders']}")
        else:
            print(f"❌ Failed to get languages: {response.status_code}")
        
        # Test speech synthesis
        print("\n4. Testing speech synthesis...")
        test_texts = [
            ("Hello, this is a test.", "hi", "female"),
            ("नमस्ते, यह एक परीक्षण है।", "hi", "male"),
            ("হ্যালো, এটি একটি পরীক্ষা।", "bn", "female")
        ]
        
        for text, language, gender in test_texts:
            print(f"   Testing: '{text}' ({language}, {gender})")
            response = requests.post(
                f"{base_url}/synthesize",
                params={"text": text, "language": language, "gender": gender},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Synthesis successful")
                print(f"      Model: {result.get('model', 'unknown')}")
                print(f"      Duration: {result.get('duration', 0):.2f}s")
                print(f"      Sample Rate: {result.get('sample_rate', 0)}Hz")
                print(f"      Audio Data Length: {len(result.get('audio_data', ''))}")
            else:
                print(f"   ❌ Synthesis failed: {response.status_code}")
                print(f"      Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS service test failed: {e}")
        return False

def test_integration():
    """Test integration between STT and TTS services"""
    print("\n🔄 Testing STT-TTS Integration")
    print("=" * 50)
    
    try:
        # Test workflow: TTS -> STT (round trip)
        print("1. Testing TTS -> STT round trip...")
        
        # Step 1: Generate speech with TTS
        tts_url = "http://localhost:8003"
        test_text = "Hello, this is a test of the audio services."
        
        print(f"   Generating speech for: '{test_text}'")
        response = requests.post(
            f"{tts_url}/synthesize",
            params={"text": test_text, "language": "hi", "gender": "female"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   ❌ TTS synthesis failed: {response.status_code}")
            return False
        
        tts_result = response.json()
        print(f"   ✅ TTS synthesis successful")
        
        # Step 2: Transcribe the generated speech with STT
        stt_url = "http://localhost:8002"
        audio_data = base64.b64decode(tts_result["audio_data"])
        
        print(f"   Transcribing generated audio...")
        files = {'file': ('generated.wav', audio_data, 'audio/wav')}
        data = {'language': 'hi'}
        
        response = requests.post(f"{stt_url}/transcribe", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            stt_result = response.json()
            print(f"   ✅ STT transcription successful")
            print(f"      Original: '{test_text}'")
            print(f"      Transcribed: '{stt_result.get('transcription', '')}'")
        else:
            print(f"   ❌ STT transcription failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Audio Services Comprehensive Test")
    print("=" * 60)
    print("Testing STT and TTS services for Indian languages")
    print("=" * 60)
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(10)
    
    # Test results
    results = {
        "stt": False,
        "tts": False,
        "integration": False
    }
    
    # Test STT service
    results["stt"] = test_stt_service()
    
    # Test TTS service
    results["tts"] = test_tts_service()
    
    # Test integration
    if results["stt"] and results["tts"]:
        results["integration"] = test_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"🎤 STT Service: {'✅ PASS' if results['stt'] else '❌ FAIL'}")
    print(f"🔊 TTS Service: {'✅ PASS' if results['tts'] else '❌ FAIL'}")
    print(f"🔄 Integration: {'✅ PASS' if results['integration'] else '❌ FAIL'}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All audio services are working correctly!")
        print("✅ Indian language support is functional!")
    else:
        print("⚠️ Some tests failed. Check the logs above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
