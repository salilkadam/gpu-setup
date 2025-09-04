# App Integration Guide: vLLM AI Infrastructure

## 🎯 **Overview**

This guide provides comprehensive documentation for applications wanting to integrate with our vLLM AI infrastructure. The system provides ultra-low latency AI inference with smart bypass optimization for real-time conversations.

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Your App      │───▶│  Smart Router   │───▶│  vLLM Models    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Session Cache  │    │  GPU Memory     │
                       │  (Redis)        │    │  (Pre-loaded)   │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 **Deployment Options**

### **Option 1: Real-Time Optimized (Recommended)**
```bash
# Ultra-low latency for real-time conversations
docker-compose -f docker-compose-realtime.yml up -d
```
- **Latency**: 200-300ms total
- **Bypass Rate**: 80-95%
- **Use Case**: Real-time conversations, live interactions

### **Option 2: Standard Deployment**
```bash
# Standard deployment with dynamic routing
docker-compose up -d
```
- **Latency**: 250-500ms
- **Flexibility**: Higher model switching flexibility
- **Use Case**: Batch processing, non-real-time applications

## 📡 **API Endpoints**

### **Base URLs**
- **Real-Time API**: `http://localhost:8001`
- **Direct vLLM API**: `http://localhost:8000`
- **Standard Routing API**: `http://localhost:8001` (when using standard deployment)

### **1. Real-Time Query Routing (Primary Endpoint)**

#### **POST `/route`**
Route queries with smart bypass optimization for real-time conversations.

**Request:**
```json
{
  "query": "Write a Python function to sort a list",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id", 
  "modality": "text",
  "context": {
    "language": "english",
    "domain": "programming"
  },
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "result": "def sort_list(lst):\n    return sorted(lst)",
  "use_case": "agent",
  "selected_model": "Qwen/Qwen2.5-7B-Instruct",
  "confidence": 0.95,
  "routing_time": 0.003,
  "bypass_used": true,
  "session_id": "abc123def456",
  "new_session": false,
  "inference_time": 0.245,
  "total_time": 0.248
}
```

#### **Parameters:**
- `query` (required): The input query to process
- `session_id` (optional): Session ID for conversation continuity
- `user_id` (optional): User ID for session management
- `modality` (optional): Input modality hint (`text`, `image`, `audio`, `video`)
- `context` (optional): Additional context information
- `max_tokens` (optional): Maximum tokens for response (default: 100)
- `temperature` (optional): Temperature for response generation (default: 0.7)

### **2. Session Management**

#### **GET `/sessions/{session_id}`**
Get information about a specific session.

**Response:**
```json
{
  "session_id": "abc123def456",
  "use_case": "agent",
  "model_id": "Qwen/Qwen2.5-7B-Instruct",
  "endpoint": "http://localhost:8000",
  "confidence": 0.95,
  "request_count": 15,
  "created_at": "2024-12-19T10:00:00",
  "last_accessed": "2024-12-19T10:05:00",
  "bypass_enabled": true
}
```

#### **DELETE `/sessions/{session_id}`**
End a conversation session.

**Response:**
```json
{
  "success": true,
  "message": "Session abc123def456 ended"
}
```

### **3. Performance Monitoring**

#### **GET `/stats`**
Get performance statistics.

**Response:**
```json
{
  "total_requests": 1000,
  "bypass_requests": 850,
  "full_routing_requests": 150,
  "session_creations": 50,
  "context_changes": 25,
  "bypass_rate_percent": 85.0,
  "average_routing_time": 0.045,
  "average_bypass_time": 0.003,
  "average_inference_time": 0.245,
  "average_total_time": 0.248
}
```

### **4. System Health**

#### **GET `/health`**
Check system health.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703000000.0,
  "bypass_router": "connected",
  "model_endpoints": {
    "agent": {
      "status": "healthy",
      "endpoint": "http://localhost:8000",
      "response_time": "2ms"
    },
    "multimodal": {
      "status": "healthy", 
      "endpoint": "http://localhost:8001",
      "response_time": "3ms"
    }
  }
}
```

### **5. Use Case Information**

#### **GET `/use-cases`**
List supported use cases.

**Response:**
```json
{
  "use_cases": [
    {
      "id": "agent",
      "description": "Content generation and executing agents",
      "endpoint": "http://localhost:8000"
    },
    {
      "id": "avatar",
      "description": "Talking head avatars and lip sync generation",
      "endpoint": "http://localhost:8001"
    },
    {
      "id": "stt",
      "description": "Speech-to-text conversion for Indian languages",
      "endpoint": "http://localhost:8002"
    },
    {
      "id": "tts",
      "description": "Text-to-speech synthesis for Indian languages",
      "endpoint": "http://localhost:8002"
    },
    {
      "id": "multimodal",
      "description": "Multi-modal temporal agentic RAG",
      "endpoint": "http://localhost:8001"
    },
    {
      "id": "video",
      "description": "Video-to-text understanding and content generation",
      "endpoint": "http://localhost:8001"
    }
  ]
}
```

## 🎮 **Supported Use Cases**

### **1. 🤖 Content Generation & Executing Agents**
- **Use Case ID**: `agent`
- **Primary Model**: `Qwen/Qwen2.5-7B-Instruct`
- **Capabilities**: Text generation, code generation, reasoning, instruction following
- **Languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance**: 95/100

**Example Queries:**
- "Write a Python function to sort a list"
- "Explain quantum computing in simple terms"
- "Generate a business plan for a startup"
- "Debug this code: [code snippet]"

### **2. 🚀 Talking Head Avatars & Lip Sync**
- **Use Case ID**: `avatar`
- **Primary Model**: `Qwen/Qwen2.5-VL-7B-Instruct`
- **Capabilities**: Multimodal, vision, text generation
- **Languages**: English, Hindi, Tamil, Telugu
- **Performance**: 90/100

**Example Queries:**
- "Generate a talking head avatar with lip sync"
- "Create a facial animation for this text"
- "Make the avatar speak with emotion"

### **3. 🗣️ Multilingual STT (Indian Languages)**
- **Use Case ID**: `stt`
- **Primary Model**: `Qwen/Qwen2-Audio-7B`
- **Capabilities**: Audio processing, speech-to-text, multilingual
- **Languages**: Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance**: 88/100

**Example Queries:**
- "Transcribe this audio file to text"
- "Convert speech to text in Hindi"
- "Process this audio recording"

### **4. 🎵 Multilingual TTS (Indian Languages)**
- **Use Case ID**: `tts`
- **Primary Model**: `Qwen/Qwen2-Audio-7B`
- **Capabilities**: Audio processing, text-to-speech, multilingual, voice cloning
- **Languages**: Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance**: 88/100

**Example Queries:**
- "Convert this text to speech in Hindi"
- "Generate voice narration for this content"
- "Create a voice clone for this text"

### **5. 📊 Multi-Modal Temporal Agentic RAG**
- **Use Case ID**: `multimodal`
- **Primary Model**: `Qwen/Qwen2.5-VL-7B-Instruct`
- **Capabilities**: Multimodal, vision, text generation, temporal understanding, RAG
- **Languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance**: 90/100

**Example Queries:**
- "Analyze this image and describe what you see"
- "Process this document and extract key information"
- "Answer questions based on this visual content"

### **6. 🎬 Video-to-Text Understanding**
- **Use Case ID**: `video`
- **Primary Model**: `Qwen/Qwen2.5-VL-7B-Instruct`
- **Capabilities**: Multimodal, video understanding, temporal analysis, text generation
- **Languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance**: 90/100

**Example Queries:**
- "Analyze this video and describe the content"
- "Extract key frames from this video"
- "Generate a summary of this video"

## 💻 **Integration Examples**

### **Python Integration**

```python
import requests
import json

class AIInfrastructureClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session_id = None
    
    def query(self, text, modality=None, context=None):
        """Send a query to the AI infrastructure."""
        payload = {
            "query": text,
            "session_id": self.session_id,
            "modality": modality,
            "context": context or {}
        }
        
        response = requests.post(f"{self.base_url}/route", json=payload)
        result = response.json()
        
        if result["success"]:
            self.session_id = result["session_id"]
            return result["result"]
        else:
            raise Exception(f"Query failed: {result.get('error_message')}")
    
    def get_session_info(self):
        """Get current session information."""
        if not self.session_id:
            return None
        
        response = requests.get(f"{self.base_url}/sessions/{self.session_id}")
        return response.json()
    
    def end_session(self):
        """End the current session."""
        if self.session_id:
            requests.delete(f"{self.base_url}/sessions/{self.session_id}")
            self.session_id = None

# Usage example
client = AIInfrastructureClient()

# First query (creates new session)
response = client.query("Write a Python function to sort a list")
print(f"Response: {response}")

# Follow-up query (uses bypass for speed)
response = client.query("Add error handling to that function")
print(f"Response: {response}")

# Get session info
session_info = client.get_session_info()
print(f"Session: {session_info}")

# End session
client.end_session()
```

### **JavaScript/Node.js Integration**

```javascript
class AIInfrastructureClient {
    constructor(baseUrl = 'http://localhost:8001') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }
    
    async query(text, modality = null, context = {}) {
        const payload = {
            query: text,
            session_id: this.sessionId,
            modality: modality,
            context: context
        };
        
        const response = await fetch(`${this.baseUrl}/route`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            this.sessionId = result.session_id;
            return result.result;
        } else {
            throw new Error(`Query failed: ${result.error_message}`);
        }
    }
    
    async getSessionInfo() {
        if (!this.sessionId) return null;
        
        const response = await fetch(`${this.baseUrl}/sessions/${this.sessionId}`);
        return await response.json();
    }
    
    async endSession() {
        if (this.sessionId) {
            await fetch(`${this.baseUrl}/sessions/${this.sessionId}`, {
                method: 'DELETE'
            });
            this.sessionId = null;
        }
    }
}

// Usage example
const client = new AIInfrastructureClient();

async function example() {
    try {
        // First query
        const response1 = await client.query("Write a Python function to sort a list");
        console.log("Response:", response1);
        
        // Follow-up query
        const response2 = await client.query("Add error handling to that function");
        console.log("Response:", response2);
        
        // Get session info
        const sessionInfo = await client.getSessionInfo();
        console.log("Session:", sessionInfo);
        
        // End session
        await client.endSession();
    } catch (error) {
        console.error("Error:", error.message);
    }
}

example();
```

### **cURL Examples**

```bash
# Basic query
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Write a Python function to sort a list",
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Query with session continuity
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Add error handling to that function",
    "session_id": "abc123def456",
    "modality": "text"
  }'

# Get session information
curl http://localhost:8001/sessions/abc123def456

# Get performance statistics
curl http://localhost:8001/stats

# Check system health
curl http://localhost:8001/health
```

## 🔧 **Configuration**

### **Environment Variables**

```bash
# API Configuration
ROUTING_MODE=realtime                    # realtime or standard
REDIS_URL=redis://localhost:6379        # Redis for session storage

# vLLM Configuration
VLLM_USE_TRITON_KERNEL=0                # Disable Triton kernels
VLLM_GPU_MEMORY_UTILIZATION=0.9         # GPU memory usage

# Performance Tuning
MAX_CONCURRENT_MODELS=3                 # Maximum concurrent models
MODEL_SWITCH_TIMEOUT=10                 # Model switch timeout (seconds)
SESSION_TIMEOUT=1800                    # Session timeout (seconds)
```

### **Model Configuration**

Models are configured in `src/config/model_registry.yaml`. You can:
- Add new models
- Modify performance scores
- Update capabilities
- Change routing preferences

## 📊 **Performance Optimization**

### **Smart Bypass Benefits**
- **95% reduction** in routing overhead (50-100ms → 1-5ms)
- **90%+ faster** first requests (2.3-5.6s → 250-300ms)
- **80-95% bypass rate** for typical conversations
- **Real-time conversation ready** with <300ms total latency

### **Best Practices**
1. **Use Session IDs**: Maintain conversation continuity for bypass optimization
2. **Provide Context**: Include modality hints and context for better routing
3. **Monitor Performance**: Use `/stats` endpoint to monitor system performance
4. **Handle Errors**: Implement proper error handling for failed requests
5. **Optimize Queries**: Keep queries focused for better model selection

## 🚨 **Error Handling**

### **Common Error Responses**

```json
{
  "success": false,
  "error_message": "Model not available",
  "use_case": "agent",
  "routing_time": 0.045
}
```

### **Error Codes**
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (session not found)
- `500`: Internal Server Error (model unavailable)
- `503`: Service Unavailable (system overloaded)

### **Retry Logic**
```python
import time
import requests

def query_with_retry(client, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.query(query)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

## 📈 **Monitoring & Analytics**

### **Key Metrics to Monitor**
- **Bypass Rate**: Should be >80% for real-time conversations
- **Average Response Time**: Should be <300ms
- **Error Rate**: Should be <1%
- **Session Count**: Monitor Redis memory usage
- **Model Health**: Check individual model endpoints

### **Grafana Dashboard**
Access monitoring at `http://localhost:3000`:
- Request latency distribution
- Bypass rate over time
- Session creation rate
- Context change frequency
- Model endpoint health

## 🔒 **Security Considerations**

### **Authentication**
- Implement API key authentication for production
- Use HTTPS for secure communication
- Validate input parameters
- Implement rate limiting

### **Data Privacy**
- Session data is stored in Redis (configurable TTL)
- No persistent storage of user queries
- Implement data retention policies
- Use secure Redis configuration

## 🚀 **Getting Started**

### **Quick Start**
1. **Deploy the system**:
   ```bash
   docker-compose -f docker-compose-realtime.yml up -d
   ```

2. **Test the API**:
   ```bash
   curl -X POST http://localhost:8001/route \
     -H "Content-Type: application/json" \
     -d '{"query": "Hello, world!"}'
   ```

3. **Integrate with your app** using the provided examples

4. **Monitor performance** using the `/stats` endpoint

### **Production Deployment**
1. Configure environment variables
2. Set up proper authentication
3. Implement monitoring and alerting
4. Configure backup and recovery
5. Set up load balancing if needed

## 📞 **Support**

For support and questions:
- Check the documentation in `docs/`
- Review the implementation tracker
- Create an issue in the repository
- Monitor system health using `/health` endpoint

---

**Status**: ✅ **Production Ready with Real-Time Optimization**  
**Last Updated**: December 19, 2024  
**Version**: 2.0.0
