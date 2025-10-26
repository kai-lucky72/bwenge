"""
Enhanced API Documentation Generator for Bwenge OS

This module provides comprehensive OpenAPI documentation generation
with examples, schemas, and detailed descriptions.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation."""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers
    )
    
    # Add custom schemas
    openapi_schema["components"]["schemas"].update({
        "UserRegister": {
            "type": "object",
            "required": ["name", "email", "password"],
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255,
                    "example": "John Doe"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "john@example.com"
                },
                "password": {
                    "type": "string",
                    "minLength": 8,
                    "example": "securepassword123"
                },
                "org_name": {
                    "type": "string",
                    "nullable": True,
                    "example": "Acme Education"
                }
            }
        },
        "UserLogin": {
            "type": "object",
            "required": ["email", "password"],
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "john@example.com"
                },
                "password": {
                    "type": "string",
                    "example": "securepassword123"
                }
            }
        },
        "TokenResponse": {
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                },
                "refresh_token": {
                    "type": "string",
                    "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                },
                "token_type": {
                    "type": "string",
                    "example": "bearer"
                }
            }
        },
        "PersonaCreate": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "type": "string",
                    "example": "Gabriel - Math Tutor"
                },
                "description": {
                    "type": "string",
                    "nullable": True,
                    "example": "A friendly AI tutor specialized in mathematics"
                },
                "tone": {
                    "type": "object",
                    "example": {
                        "style": "friendly",
                        "formality": "casual",
                        "enthusiasm": "high"
                    }
                },
                "rules": {
                    "type": "object",
                    "example": {
                        "guidelines": [
                            "Be encouraging and patient",
                            "Break down complex problems",
                            "Use examples and analogies"
                        ]
                    }
                },
                "sample_prompts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": [
                        "Hello! I'm Gabriel, your math tutor. What would you like to learn today?",
                        "Let's solve this step by step!",
                        "Great question! Let me explain that concept."
                    ]
                },
                "safety_rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": [
                        "Keep content appropriate for educational settings",
                        "No inappropriate or harmful content",
                        "Focus on mathematical concepts and learning"
                    ]
                }
            }
        },
        "AIRequest": {
            "type": "object",
            "required": ["persona_id", "session_id", "user_message"],
            "properties": {
                "persona_id": {
                    "type": "string",
                    "format": "uuid",
                    "example": "123e4567-e89b-12d3-a456-426614174000"
                },
                "session_id": {
                    "type": "string",
                    "example": "session_abc123"
                },
                "user_message": {
                    "type": "string",
                    "example": "Can you help me understand quadratic equations?"
                },
                "context": {
                    "type": "object",
                    "example": {
                        "conversation_history": [
                            {
                                "role": "user",
                                "content": "Hello"
                            },
                            {
                                "role": "assistant",
                                "content": "Hi! How can I help you today?"
                            }
                        ]
                    }
                }
            }
        },
        "AIResponse": {
            "type": "object",
            "properties": {
                "response_text": {
                    "type": "string",
                    "example": "A quadratic equation is a polynomial equation of degree 2..."
                },
                "actions": {
                    "type": "array",
                    "items": {"type": "object"},
                    "example": []
                },
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {"type": "string", "format": "uuid"},
                            "chunk_id": {"type": "string"},
                            "text": {"type": "string"},
                            "relevance_score": {"type": "number"}
                        }
                    },
                    "example": [
                        {
                            "source_id": "123e4567-e89b-12d3-a456-426614174000",
                            "chunk_id": "chunk_001",
                            "text": "Quadratic equations are polynomial equations of degree 2...",
                            "relevance_score": 0.95
                        }
                    ]
                },
                "animation_hint": {
                    "type": "string",
                    "nullable": True,
                    "example": "explaining"
                },
                "session_id": {
                    "type": "string",
                    "example": "session_abc123"
                }
            }
        },
        "KnowledgeUploadResponse": {
            "type": "object",
            "properties": {
                "upload_id": {
                    "type": "string",
                    "format": "uuid",
                    "example": "123e4567-e89b-12d3-a456-426614174000"
                },
                "status": {
                    "type": "string",
                    "example": "pending"
                },
                "message": {
                    "type": "string",
                    "example": "File uploaded successfully and queued for processing"
                }
            }
        },
        "Model3DResponse": {
            "type": "object",
            "properties": {
                "model_url": {
                    "type": "string",
                    "example": "https://api.bwenge.com/assets/models/avatar.gltf?signature=abc123&expires=1234567890"
                },
                "animations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["idle", "talking", "thinking", "happy", "greeting"]
                },
                "scale": {
                    "type": "number",
                    "example": 1.0
                },
                "bounding_box": {
                    "type": "object",
                    "example": {"width": 1.0, "height": 2.0, "depth": 1.0}
                },
                "version": {
                    "type": "string",
                    "example": "1.0"
                },
                "mime_type": {
                    "type": "string",
                    "example": "model/gltf+json"
                }
            }
        },
        "WeeklyReport": {
            "type": "object",
            "properties": {
                "org_id": {
                    "type": "string",
                    "format": "uuid"
                },
                "week_start": {
                    "type": "string",
                    "format": "date-time"
                },
                "week_end": {
                    "type": "string",
                    "format": "date-time"
                },
                "total_messages": {
                    "type": "integer",
                    "example": 1250
                },
                "active_users": {
                    "type": "integer",
                    "example": 45
                },
                "top_personas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "persona_id": {"type": "string"},
                            "name": {"type": "string"},
                            "interaction_count": {"type": "integer"}
                        }
                    },
                    "example": [
                        {
                            "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Gabriel - Math Tutor",
                            "interaction_count": 450
                        }
                    ]
                },
                "usage_stats": {
                    "type": "object",
                    "example": {
                        "total_conversations": 125,
                        "avg_messages_per_conversation": 8.5,
                        "peak_usage_day": "Monday"
                    }
                }
            }
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "example": "Authentication required"
                }
            }
        }
    })
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add additional info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://bwenge.com/logo.png",
        "altText": "Bwenge OS Logo"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def add_api_examples() -> Dict[str, Any]:
    """Add comprehensive API usage examples."""
    
    return {
        "authentication_flow": {
            "summary": "Complete Authentication Flow",
            "description": "Example of user registration, login, and accessing protected endpoints",
            "value": {
                "step_1_register": {
                    "method": "POST",
                    "url": "/auth/register",
                    "body": {
                        "name": "Jane Smith",
                        "email": "jane@school.edu",
                        "password": "securepass123",
                        "org_name": "Springfield Elementary"
                    },
                    "response": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                },
                "step_2_access_protected": {
                    "method": "GET",
                    "url": "/users/me",
                    "headers": {
                        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    },
                    "response": {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Jane Smith",
                        "email": "jane@school.edu",
                        "role": "admin"
                    }
                }
            }
        },
        "persona_creation_flow": {
            "summary": "Creating and Using an AI Persona",
            "description": "Complete workflow for creating a persona and getting AI responses",
            "value": {
                "step_1_create_persona": {
                    "method": "POST",
                    "url": "/personas",
                    "body": {
                        "name": "Emma - Science Teacher",
                        "description": "An enthusiastic science teacher AI",
                        "tone": {
                            "style": "enthusiastic",
                            "formality": "casual",
                            "expertise_level": "intermediate"
                        },
                        "rules": {
                            "guidelines": [
                                "Make science fun and accessible",
                                "Use real-world examples",
                                "Encourage curiosity and questions"
                            ]
                        },
                        "sample_prompts": [
                            "Welcome to science class! What would you like to explore today?",
                            "That's a fantastic question! Let me explain...",
                            "Science is all around us! Let's discover how..."
                        ],
                        "safety_rules": [
                            "Keep all content age-appropriate",
                            "No dangerous experiments",
                            "Focus on educational content only"
                        ]
                    }
                },
                "step_2_get_ai_response": {
                    "method": "POST",
                    "url": "/ai/respond",
                    "body": {
                        "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                        "session_id": "science_session_001",
                        "user_message": "Can you explain photosynthesis?",
                        "context": {}
                    }
                }
            }
        },
        "knowledge_upload_flow": {
            "summary": "Uploading and Processing Knowledge",
            "description": "How to upload educational content and track processing",
            "value": {
                "step_1_upload": {
                    "method": "POST",
                    "url": "/knowledge/upload",
                    "content_type": "multipart/form-data",
                    "form_data": {
                        "file": "biology_textbook_chapter1.pdf",
                        "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Biology Textbook - Chapter 1: Introduction to Life"
                    }
                },
                "step_2_check_status": {
                    "method": "GET",
                    "url": "/knowledge/{upload_id}/status",
                    "response_progression": [
                        {"status": "pending", "message": "Queued for processing"},
                        {"status": "processing", "message": "Extracting content"},
                        {"status": "ready", "chunk_count": 15, "message": "Available for RAG"}
                    ]
                }
            }
        }
    }

def generate_api_documentation() -> str:
    """Generate comprehensive API documentation in Markdown format."""
    
    return """
# Bwenge OS API Documentation

## Overview

Bwenge OS is an AI-powered educational platform that combines personalized AI tutors with 3D avatars to create engaging learning experiences. This API provides comprehensive functionality for managing users, content, AI personas, and educational analytics.

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://api.bwenge.com`

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting Started

1. **Register** a new account: `POST /auth/register`
2. **Login** to get tokens: `POST /auth/login`
3. **Use the access token** for subsequent API calls
4. **Refresh** when the token expires: `POST /auth/refresh`

## Rate Limits

API endpoints have different rate limits based on their resource intensity:

| Endpoint Type | Rate Limit | Description |
|---------------|------------|-------------|
| Authentication | 5-20/min | Login, register, refresh |
| File Upload | 10/min | Knowledge content uploads |
| AI Responses | 60/min | AI-generated responses |
| General API | 100/min | Most other endpoints |

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "detail": "Specific error message"
}
```

### Common Status Codes

- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

## Multi-tenancy

The system supports multiple organizations with complete data isolation. Users can only access resources within their organization.

## WebSocket Endpoints

Real-time chat functionality is available via WebSocket:

```
ws://localhost:8004/ws/chat?persona_id={id}&session_id={session}&token={jwt_token}
```

### WebSocket Message Types

- `session_info` - Session initialization
- `message` - Chat messages (user/assistant)
- `typing` - Typing indicators
- `animation` - 3D avatar animation hints
- `error` - Error messages

## SDKs and Libraries

### Python SDK Example

```python
import requests

class BwengeClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def login(self, email, password):
        response = self.session.post(f'{self.base_url}/auth/login', 
                                   json={'email': email, 'password': password})
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        return response.json()
    
    def create_persona(self, persona_data):
        return self.session.post(f'{self.base_url}/personas', json=persona_data).json()
    
    def get_ai_response(self, persona_id, message, session_id):
        data = {
            'persona_id': persona_id,
            'session_id': session_id,
            'user_message': message,
            'context': {}
        }
        return self.session.post(f'{self.base_url}/ai/respond', json=data).json()

# Usage
client = BwengeClient('http://localhost:8000')
client.login('user@example.com', 'password')
response = client.get_ai_response(persona_id, 'Hello!', 'session_1')
```

### JavaScript SDK Example

```javascript
class BwengeClient {
    constructor(baseUrl, token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
    }
    
    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        const data = await response.json();
        this.token = data.access_token;
        return data;
    }
    
    async createPersona(personaData) {
        return this.request('POST', '/personas', personaData);
    }
    
    async getAIResponse(personaId, message, sessionId) {
        return this.request('POST', '/ai/respond', {
            persona_id: personaId,
            session_id: sessionId,
            user_message: message,
            context: {}
        });
    }
    
    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            }
        };
        if (data) options.body = JSON.stringify(data);
        
        const response = await fetch(`${this.baseUrl}${endpoint}`, options);
        return response.json();
    }
}
```

## Best Practices

### 1. Token Management
- Store tokens securely (not in localStorage for production)
- Implement automatic token refresh
- Handle token expiration gracefully

### 2. Error Handling
- Always check response status codes
- Implement retry logic for transient errors
- Log errors for debugging

### 3. Rate Limiting
- Implement client-side rate limiting
- Use exponential backoff for retries
- Cache responses when appropriate

### 4. File Uploads
- Validate file types before upload
- Show upload progress to users
- Handle large files appropriately

### 5. WebSocket Connections
- Implement reconnection logic
- Handle connection drops gracefully
- Manage multiple concurrent sessions

## Support

For API support and questions:
- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Documentation: [Full Documentation](https://docs.bwenge.com)
- Email: support@bwenge.com
"""