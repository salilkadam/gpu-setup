# Indian Language Audio Models Research

## 🎯 **Objective**
Research and implement the best STT (Speech-to-Text) and TTS (Text-to-Speech) models for Indian languages that are compatible with our vLLM-based inference system.

## 📊 **Research Findings**

### **🔍 STT (Speech-to-Text) Models**

#### **1. OpenAI Whisper Large v3** ⭐ **RECOMMENDED**
- **Model**: `openai/whisper-large-v3`
- **Size**: ~3GB
- **Languages**: 99 languages including Hindi, Tamil, Telugu, Bengali, Gujarati, Marathi, Punjabi, Urdu
- **Architecture**: `WhisperForConditionalGeneration`
- **vLLM Compatibility**: ❌ **NOT COMPATIBLE** (vLLM doesn't support WhisperForConditionalGeneration)
- **Alternative**: Use with Transformers backend or separate service

#### **2. Whisper Large v3 Turbo** ⭐ **ALTERNATIVE**
- **Model**: `openai/whisper-large-v3-turbo`
- **Size**: ~3GB
- **Languages**: Same as v3 but optimized for speed
- **Architecture**: `WhisperForConditionalGeneration`
- **vLLM Compatibility**: ❌ **NOT COMPATIBLE**

### **🔊 TTS (Text-to-Speech) Models**

#### **1. SYSPIN Coqui TTS Models** ⭐ **RECOMMENDED**
- **Hindi Female**: `SYSPIN/tts_vits_coquiai_HindiFemale`
- **Hindi Male**: `SYSPIN/tts_vits_coquiai_HindiMale`
- **Bengali Female**: `SYSPIN/tts_vits_coquiai_BengaliFemale`
- **Bengali Male**: `SYSPIN/tts_vits_coquiai_BengaliMale`
- **Chhattisgarhi Female**: `SYSPIN/tts_vits_coquiai_ChhattisgarhiFemale`
- **Chhattisgarhi Male**: `SYSPIN/tts_vits_coquiai_ChhattisgarhiMale`
- **Architecture**: VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech)
- **vLLM Compatibility**: ❌ **NOT COMPATIBLE** (TTS models not supported by vLLM)

#### **2. Other TTS Options**
- **Coqui TTS**: General-purpose TTS framework
- **Festival**: Traditional TTS system
- **eSpeak**: Open-source speech synthesizer

## 🚧 **Critical Challenge: vLLM Compatibility**

### **❌ Problem**
**vLLM does NOT support audio models!**

- **WhisperForConditionalGeneration**: Not supported by vLLM
- **TTS Models**: Not supported by vLLM
- **Audio Processing**: vLLM is designed for text-only LLM inference

### **✅ Solution Strategy**

#### **Option 1: Hybrid Architecture** ⭐ **RECOMMENDED**
- **vLLM**: Handle text-only use cases (Agent, Avatar, Multimodal, Video)
- **Separate Audio Services**: Handle STT and TTS
- **API Gateway**: Route requests to appropriate services

#### **Option 2: Transformers Backend**
- Use Hugging Face Transformers for audio models
- Integrate with our existing routing system
- Lower performance but full compatibility

## 🏗️ **Implementation Plan**

### **Phase 1: Audio Service Setup**
1. **STT Service**: Deploy Whisper Large v3 with Transformers
2. **TTS Service**: Deploy Coqui TTS models
3. **API Integration**: Add audio endpoints to routing system

### **Phase 2: Model Selection**
1. **STT**: `openai/whisper-large-v3` (3GB)
2. **TTS Hindi**: `SYSPIN/tts_vits_coquiai_HindiFemale` + `SYSPIN/tts_vits_coquiai_HindiMale`
3. **TTS Bengali**: `SYSPIN/tts_vits_coquiai_BengaliFemale` + `SYSPIN/tts_vits_coquiai_BengaliMale`

### **Phase 3: Integration**
1. **Docker Services**: Separate containers for audio processing
2. **API Gateway**: Route audio requests to appropriate services
3. **Monitoring**: Add audio service monitoring

## 📋 **Indian Languages Coverage**

### **STT Support (Whisper Large v3)**
- ✅ **Hindi** (hi)
- ✅ **Tamil** (ta)
- ✅ **Telugu** (te)
- ✅ **Bengali** (bn)
- ✅ **Gujarati** (gu)
- ✅ **Marathi** (mr)
- ✅ **Punjabi** (pa)
- ✅ **Urdu** (ur)
- ✅ **Kannada** (kn)
- ✅ **Malayalam** (ml)
- ✅ **Odia** (or)
- ✅ **Assamese** (as)

### **TTS Support (SYSPIN Models)**
- ✅ **Hindi** (Male + Female voices)
- ✅ **Bengali** (Male + Female voices)
- ✅ **Chhattisgarhi** (Male + Female voices)

## 🎯 **Recommended Implementation**

### **Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   vLLM Service  │    │  Audio Services │
│                 │    │                 │    │                 │
│  Route Requests │───▶│  Text Models    │    │  STT + TTS      │
│                 │    │  (MiniCPM-V-4)  │    │  (Whisper+TTS)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Services**
1. **vLLM Service**: MiniCPM-V-4 (Agent, Avatar, Multimodal, Video)
2. **STT Service**: Whisper Large v3 (Speech-to-Text)
3. **TTS Service**: Coqui TTS models (Text-to-Speech)

### **Use Case Coverage**
- **Agent**: ✅ vLLM (MiniCPM-V-4)
- **Avatar**: ✅ vLLM (MiniCPM-V-4)
- **STT**: ✅ Audio Service (Whisper)
- **TTS**: ✅ Audio Service (Coqui TTS)
- **Multimodal**: ✅ vLLM (MiniCPM-V-4)
- **Video**: ✅ vLLM (MiniCPM-V-4)

**Total Coverage: 6/6 (100%)**

## 🚀 **Next Steps**
1. Download and test Whisper Large v3
2. Download and test Coqui TTS models
3. Create separate Docker services for audio processing
4. Integrate with existing routing system
5. Test end-to-end audio functionality
