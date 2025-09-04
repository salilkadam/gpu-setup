# API Reference: vLLM AI Infrastructure

## 🎯 **Overview**

Complete API reference for the vLLM AI Infrastructure with smart bypass optimization. This document provides detailed information about all available endpoints, request/response formats, and integration patterns.

## 📡 **Base URLs**

| Environment | Real-Time API | Direct vLLM API | Standard Routing |
|-------------|---------------|-----------------|------------------|
| **Local** | `http://localhost:8001` | `http://localhost:8000` | `http://localhost:8001` |
| **Production** | `https://your-domain.com:8001` | `https://your-domain.com:8000` | `https://your-domain.com:8001` |

## 🔗 **Authentication**

Currently, the API does not require authentication. For production deployments, implement API key authentication:

```bash
# Add to request headers
Authorization: Bearer your-api-key
```

## 📋 **API Endpoints**

### **1. Real-Time Query Routing**

#### **POST `/route`**
Route queries with smart bypass optimization for real-time conversations.

**Endpoint**: `POST /route`

**Request Headers**:
```
Content-Type: application/json
X-Session-ID: optional-session-id (alternative to body parameter)
```

**Request Body**:
```json
{
  "query": "string (required)",
  "session_id": "string (optional)",
  "user_id": "string (optional)",
  "modality": "string (optional)",
  "context": "object (optional)",
  "max_tokens": "integer (optional, default: 100)",
  "temperature": "float (optional, default: 0.7)"
}
```

**Request Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | The input query to process |
| `session_id` | string | ❌ | null | Session ID for conversation continuity |
| `user_id` | string | ❌ | null | User ID for session management |
| `modality` | string | ❌ | null | Input modality hint (`text`, `image`, `audio`, `video`) |
| `context` | object | ❌ | {} | Additional context information |
| `max_tokens` | integer | ❌ | 100 | Maximum tokens for response |
| `temperature` | float | ❌ | 0.7 | Temperature for response generation (0.0-2.0) |

**Response**:
```json
{
  "success": true,
  "result": "string",
  "use_case": "string",
  "selected_model": "string",
  "confidence": "float",
  "routing_time": "float",
  "bypass_used": "boolean",
  "session_id": "string",
  "new_session": "boolean",
  "inference_time": "float",
  "total_time": "float",
  "error_message": "string (only on error)"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request was successful |
| `result` | string | The generated response text |
| `use_case` | string | Detected use case (`agent`, `avatar`, `stt`, `tts`, `multimodal`, `video`) |
| `selected_model` | string | Model ID that processed the request |
| `confidence` | float | Confidence score for the routing decision (0.0-1.0) |
| `routing_time` | float | Time taken for routing decision (seconds) |
| `bypass_used` | boolean | Whether smart bypass was used |
| `session_id` | string | Session ID for conversation continuity |
| `new_session` | boolean | Whether a new session was created |
| `inference_time` | float | Time taken for model inference (seconds) |
| `total_time` | float | Total request processing time (seconds) |
| `error_message` | string | Error message (only present on failure) |

**Example Request**:
```bash
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Write a Python function to sort a list",
    "modality": "text",
    "context": {
      "language": "english",
      "domain": "programming"
    },
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

**Example Response**:
```json
{
  "success": true,
  "result": "def sort_list(lst):\n    \"\"\"Sort a list in ascending order.\"\"\"\n    return sorted(lst)\n\n# Example usage:\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6]\nsorted_numbers = sort_list(numbers)\nprint(sorted_numbers)  # [1, 1, 2, 3, 4, 5, 6, 9]",
  "use_case": "agent",
  "selected_model": "Qwen/Qwen2.5-7B-Instruct",
  "confidence": 0.95,
  "routing_time": 0.003,
  "bypass_used": false,
  "session_id": "abc123def456",
  "new_session": true,
  "inference_time": 0.245,
  "total_time": 0.248
}
```

**Error Response**:
```json
{
  "success": false,
  "error_message": "Model not available",
  "use_case": "agent",
  "routing_time": 0.045
}
```

### **2. Session Management**

#### **GET `/sessions/{session_id}`**
Get information about a specific session.

**Endpoint**: `GET /sessions/{session_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | ✅ | The session ID to retrieve |

**Response**:
```json
{
  "session_id": "string",
  "use_case": "string",
  "model_id": "string",
  "endpoint": "string",
  "confidence": "float",
  "request_count": "integer",
  "created_at": "string",
  "last_accessed": "string",
  "bypass_enabled": "boolean"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | The session ID |
| `use_case` | string | Current use case for the session |
| `model_id` | string | Model ID being used |
| `endpoint` | string | Model endpoint URL |
| `confidence` | float | Confidence score for the session |
| `request_count` | integer | Number of requests in this session |
| `created_at` | string | Session creation timestamp (ISO 8601) |
| `last_accessed` | string | Last access timestamp (ISO 8601) |
| `bypass_enabled` | boolean | Whether bypass is enabled for this session |

**Example Request**:
```bash
curl http://localhost:8001/sessions/abc123def456
```

**Example Response**:
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

**Endpoint**: `DELETE /sessions/{session_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | ✅ | The session ID to end |

**Response**:
```json
{
  "success": true,
  "message": "string"
}
```

**Example Request**:
```bash
curl -X DELETE http://localhost:8001/sessions/abc123def456
```

**Example Response**:
```json
{
  "success": true,
  "message": "Session abc123def456 ended"
}
```

### **3. Performance Monitoring**

#### **GET `/stats`**
Get performance statistics.

**Endpoint**: `GET /stats`

**Response**:
```json
{
  "total_requests": "integer",
  "bypass_requests": "integer",
  "full_routing_requests": "integer",
  "session_creations": "integer",
  "context_changes": "integer",
  "bypass_rate_percent": "float",
  "average_routing_time": "float",
  "average_bypass_time": "float",
  "average_inference_time": "float",
  "average_total_time": "float"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `total_requests` | integer | Total number of requests processed |
| `bypass_requests` | integer | Number of requests using bypass |
| `full_routing_requests` | integer | Number of requests using full routing |
| `session_creations` | integer | Number of new sessions created |
| `context_changes` | integer | Number of context changes detected |
| `bypass_rate_percent` | float | Percentage of requests using bypass |
| `average_routing_time` | float | Average routing time (seconds) |
| `average_bypass_time` | float | Average bypass time (seconds) |
| `average_inference_time` | float | Average inference time (seconds) |
| `average_total_time` | float | Average total request time (seconds) |

**Example Request**:
```bash
curl http://localhost:8001/stats
```

**Example Response**:
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

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "string",
  "timestamp": "float",
  "bypass_router": "string",
  "model_endpoints": "object"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Overall system status (`healthy`, `degraded`, `unhealthy`) |
| `timestamp` | float | Unix timestamp of health check |
| `bypass_router` | string | Bypass router status |
| `model_endpoints` | object | Status of individual model endpoints |

**Example Request**:
```bash
curl http://localhost:8001/health
```

**Example Response**:
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
    },
    "audio": {
      "status": "healthy",
      "endpoint": "http://localhost:8002",
      "response_time": "4ms"
    }
  }
}
```

### **5. Use Case Information**

#### **GET `/use-cases`**
List supported use cases.

**Endpoint**: `GET /use-cases`

**Response**:
```json
{
  "use_cases": [
    {
      "id": "string",
      "description": "string",
      "endpoint": "string"
    }
  ]
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `use_cases` | array | List of supported use cases |
| `use_cases[].id` | string | Use case identifier |
| `use_cases[].description` | string | Human-readable description |
| `use_cases[].endpoint` | string | Direct endpoint URL |

**Example Request**:
```bash
curl http://localhost:8001/use-cases
```

**Example Response**:
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

### **6. System Cleanup**

#### **POST `/cleanup`**
Manually cleanup expired sessions.

**Endpoint**: `POST /cleanup`

**Response**:
```json
{
  "success": true,
  "message": "string"
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8001/cleanup
```

**Example Response**:
```json
{
  "success": true,
  "message": "Session cleanup completed"
}
```

## 🎮 **Use Case Details**

### **Use Case: `agent`**
- **Description**: Content generation and executing agents
- **Primary Model**: `Qwen/Qwen2.5-7B-Instruct`
- **Capabilities**: Text generation, code generation, reasoning, instruction following
- **Languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance Score**: 95/100

**Example Queries**:
- "Write a Python function to sort a list"
- "Explain quantum computing in simple terms"
- "Generate a business plan for a startup"
- "Debug this code: [code snippet]"

### **Use Case: `avatar`**
- **Description**: Talking head avatars and lip sync generation
- **Primary Model**: `Qwen/Qwen2.5-VL-7B-Instruct`
- **Capabilities**: Multimodal, vision, text generation
- **Languages**: English, Hindi, Tamil, Telugu
- **Performance Score**: 90/100

**Example Queries**:
- "Generate a talking head avatar with lip sync"
- "Create a facial animation for this text"
- "Make the avatar speak with emotion"

### **Use Case: `stt`**
- **Description**: Speech-to-text conversion for Indian languages
- **Primary Model**: `Qwen/Qwen2-Audio-7B`
- **Capabilities**: Audio processing, speech-to-text, multilingual
- **Languages**: Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance Score**: 88/100

**Example Queries**:
- "Transcribe this audio file to text"
- "Convert speech to text in Hindi"
- "Process this audio recording"

### **Use Case: `tts`**
- **Description**: Text-to-speech synthesis for Indian languages
- **Primary Model**: `Qwen/Qwen2-Audio-7B`
- **Capabilities**: Audio processing, text-to-speech, multilingual, voice cloning
- **Languages**: Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance Score**: 88/100

**Example Queries**:
- "Convert this text to speech in Hindi"
- "Generate voice narration for this content"
- "Create a voice clone for this text"

### **Use Case: `multimodal`**
- **Description**: Multi-modal temporal agentic RAG
- **Primary Model**: `Qwen/Qwen2.5-VL-7B-Instruct`
- **Capabilities**: Multimodal, vision, text generation, temporal understanding, RAG
- **Languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance Score**: 90/100

**Example Queries**:
- "Analyze this image and describe what you see"
- "Process this document and extract key information"
- "Answer questions based on this visual content"

### **Use Case: `video`**
- **Description**: Video-to-text understanding and content generation
- **Primary Model**: `Qwen/Qwen2.5-VL-7B-Instruct`
- **Capabilities**: Multimodal, video understanding, temporal analysis, text generation
- **Languages**: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Performance Score**: 90/100

**Example Queries**:
- "Analyze this video and describe the content"
- "Extract key frames from this video"
- "Generate a summary of this video"

## 🚨 **Error Handling**

### **HTTP Status Codes**

| Code | Description | Common Causes |
|------|-------------|---------------|
| `200` | Success | Request processed successfully |
| `400` | Bad Request | Invalid request parameters |
| `404` | Not Found | Session not found, endpoint not found |
| `422` | Unprocessable Entity | Validation error |
| `500` | Internal Server Error | Model unavailable, system error |
| `503` | Service Unavailable | System overloaded, maintenance mode |

### **Error Response Format**

```json
{
  "success": false,
  "error_message": "string",
  "use_case": "string (optional)",
  "routing_time": "float (optional)"
}
```

### **Common Error Messages**

| Error Message | Description | Solution |
|---------------|-------------|----------|
| `"Model not available"` | Requested model is not loaded | Wait for model to load or use fallback |
| `"Session not found"` | Session ID does not exist | Create new session or check session ID |
| `"Invalid parameters"` | Request parameters are invalid | Check parameter format and values |
| `"System overloaded"` | System is under heavy load | Retry with exponential backoff |
| `"Timeout"` | Request timed out | Increase timeout or simplify query |

### **Retry Logic Example**

```python
import time
import requests
from requests.exceptions import RequestException

def query_with_retry(url, payload, max_retries=3, base_delay=1):
    """Query with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
            print(f"Retry {attempt + 1}/{max_retries} after {delay}s delay")
```

## 📊 **Rate Limiting**

Currently, no rate limiting is implemented. For production deployments, consider implementing:

- **Per-user rate limiting**: 100 requests/minute per user
- **Per-session rate limiting**: 1000 requests/minute per session
- **Global rate limiting**: 10000 requests/minute total

## 🔒 **Security**

### **Input Validation**
- All input parameters are validated
- Query length is limited to 10,000 characters
- Modality values are restricted to valid options
- Temperature values are clamped to 0.0-2.0 range

### **Data Privacy**
- Session data is stored in Redis with TTL
- No persistent storage of user queries
- Implement data retention policies
- Use secure Redis configuration

### **Production Security Checklist**
- [ ] Implement API key authentication
- [ ] Use HTTPS for all communications
- [ ] Configure proper CORS policies
- [ ] Implement rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure secure Redis
- [ ] Implement input sanitization
- [ ] Set up log aggregation

## 📈 **Performance Metrics**

### **Target Performance**
- **Total Latency**: <300ms (real-time optimized)
- **Routing Time**: <50ms
- **Bypass Time**: <5ms
- **Inference Time**: <200ms
- **Bypass Rate**: >80% for typical conversations

### **Monitoring Endpoints**
- `/stats` - Performance statistics
- `/health` - System health status
- Grafana Dashboard - `http://localhost:3000`

## 🚀 **SDK Examples**

### **Python SDK**
```python
from ai_infrastructure import AIClient

client = AIClient(base_url="http://localhost:8001")

# Simple query
response = client.query("Hello, world!")
print(response.result)

# Query with session
response = client.query("Follow up question", session_id="abc123")
print(response.result)
```

### **JavaScript SDK**
```javascript
import { AIClient } from 'ai-infrastructure-sdk';

const client = new AIClient('http://localhost:8001');

// Simple query
const response = await client.query('Hello, world!');
console.log(response.result);

// Query with session
const response2 = await client.query('Follow up question', { sessionId: 'abc123' });
console.log(response2.result);
```

---

**Status**: ✅ **Production Ready**  
**Last Updated**: December 19, 2024  
**Version**: 2.0.0
