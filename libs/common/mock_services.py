"""
Mock services for local development without external dependencies
"""
import random
import hashlib
from typing import List, Dict, Any
from datetime import datetime


class MockLLM:
    """Mock LLM for local development - no OpenAI API needed"""
    
    def __init__(self):
        self.responses = {
            "greeting": [
                "Hello! I'm your AI tutor. How can I help you learn today?",
                "Hi there! I'm excited to help you with your studies. What would you like to learn?",
                "Welcome! I'm here to make learning fun and easy. What topic interests you?"
            ],
            "math": [
                "Great math question! Let me break this down step by step for you.",
                "I love helping with math! Here's how we can solve this problem together.",
                "Math can be fun! Let's work through this problem systematically."
            ],
            "explain": [
                "I'll explain this concept clearly. The key thing to understand is...",
                "Let me break this down into simpler parts so it's easier to understand.",
                "That's a great question! Here's a clear explanation..."
            ],
            "default": [
                "That's an interesting question! Let me help you understand this better.",
                "I understand what you're asking. Here's my answer based on what I know.",
                "Let me provide you with a helpful response to your question.",
                "Based on the context, I can explain this to you clearly."
            ]
        }
    
    def chat_completion(self, messages: List[Dict], **kwargs):
        """Mock chat completion"""
        user_message = messages[-1]["content"] if messages else ""
        response = self._generate_response(user_message)
        
        return {
            "choices": [{
                "message": {
                    "content": response,
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message.split()) * 2,
                "completion_tokens": len(response.split()),
                "total_tokens": len(user_message.split()) * 2 + len(response.split())
            },
            "model": "mock-gpt-3.5-turbo"
        }
    
    def _generate_response(self, user_message: str) -> str:
        """Generate contextual response based on keywords"""
        msg_lower = user_message.lower()
        
        # Detect intent
        if any(word in msg_lower for word in ["hello", "hi", "hey", "greetings"]):
            response_type = "greeting"
        elif any(word in msg_lower for word in ["math", "calculate", "solve", "equation"]):
            response_type = "math"
        elif any(word in msg_lower for word in ["explain", "what is", "how does", "why"]):
            response_type = "explain"
        else:
            response_type = "default"
        
        # Get random response from category
        base_response = random.choice(self.responses[response_type])
        
        # Add context from user message
        if len(user_message) > 50:
            context = f" Regarding your question about '{user_message[:50]}...', "
        else:
            context = f" Regarding '{user_message}', "
        
        return base_response + context + "this is a mock response for local development. In production, this would be a real AI-generated answer with proper context and citations."


class MockEmbeddings:
    """Mock embeddings for local development - no OpenAI API needed"""
    
    def create(self, input: str or List[str], **kwargs):
        """Generate fake but consistent embeddings"""
        if isinstance(input, str):
            input = [input]
        
        embeddings = []
        for text in input:
            embedding = self._generate_embedding(text)
            embeddings.append(embedding)
        
        return {
            "data": [
                {
                    "embedding": emb,
                    "index": i,
                    "object": "embedding"
                }
                for i, emb in enumerate(embeddings)
            ],
            "model": "mock-text-embedding-ada-002",
            "usage": {
                "prompt_tokens": sum(len(t.split()) for t in input),
                "total_tokens": sum(len(t.split()) for t in input)
            }
        }
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate consistent fake 1536-dimensional embedding"""
        # Use hash for consistency - same text = same embedding
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Generate 1536-dimensional vector (OpenAI ada-002 size)
        embedding = []
        for i in range(1536):
            # Use hash to generate consistent values between -1 and 1
            hash_val = int(text_hash[(i * 2) % len(text_hash):(i * 2 + 2) % len(text_hash) or None], 16)
            normalized = (hash_val / 255.0) * 2 - 1  # Scale to [-1, 1]
            embedding.append(normalized)
        
        return embedding


class MockWhisper:
    """Mock transcription for local development"""
    
    def __init__(self):
        self.sample_transcriptions = [
            "This is a sample transcription of an audio file. In production, this would contain the actual transcribed speech from the audio.",
            "Welcome to this educational content. Today we'll be discussing important concepts that will help you learn effectively.",
            "Let's explore this topic together. I'll explain the key points clearly so you can understand them well.",
        ]
    
    def transcribe(self, audio_file: str, **kwargs) -> Dict[str, Any]:
        """Return mock transcription"""
        # Use filename hash to get consistent transcription
        file_hash = hashlib.md5(audio_file.encode()).hexdigest()
        index = int(file_hash[:8], 16) % len(self.sample_transcriptions)
        
        return {
            "text": self.sample_transcriptions[index] + f" [Mock transcription for: {audio_file}]",
            "language": "en",
            "duration": 120.0,
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": self.sample_transcriptions[index]
                }
            ]
        }


class MockEmailService:
    """Mock email service for local development"""
    
    def send_email(self, to: str, subject: str, body: str, **kwargs):
        """Print email to console instead of sending"""
        print("\n" + "="*60)
        print("📧 EMAIL (Mock - Local Development)")
        print("="*60)
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        print(body)
        print("="*60 + "\n")
        
        return {
            "status": "sent",
            "mode": "mock",
            "message_id": f"mock-{hashlib.md5(to.encode()).hexdigest()[:16]}"
        }


class MockPaymentProvider:
    """Mock payment provider for local development"""
    
    def __init__(self):
        self.transactions = {}
    
    def create_payment(self, amount: float, currency: str, method: str, **kwargs):
        """Create mock payment"""
        transaction_id = f"mock-txn-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]}"
        
        self.transactions[transaction_id] = {
            "id": transaction_id,
            "amount": amount,
            "currency": currency,
            "method": method,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        print(f"\n💳 MOCK PAYMENT CREATED")
        print(f"   Transaction ID: {transaction_id}")
        print(f"   Amount: {amount} {currency}")
        print(f"   Method: {method}")
        print(f"   Status: pending")
        print(f"   To complete: POST /payments/simulate-completion/{transaction_id}\n")
        
        return {
            "transaction_id": transaction_id,
            "status": "pending",
            "payment_url": f"http://localhost:8007/mock-payment/{transaction_id}"
        }
    
    def verify_payment(self, transaction_id: str):
        """Verify mock payment"""
        if transaction_id in self.transactions:
            return self.transactions[transaction_id]
        return None
    
    def complete_payment(self, transaction_id: str, success: bool = True):
        """Complete mock payment"""
        if transaction_id in self.transactions:
            self.transactions[transaction_id]["status"] = "completed" if success else "failed"
            return self.transactions[transaction_id]
        return None


# Factory functions to get the right service based on environment
def get_llm_client():
    """Get LLM client (mock or real based on environment)"""
    import os
    
    if os.getenv("USE_MOCK_LLM", "false").lower() == "true":
        return MockLLM()
    else:
        import openai
        return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embeddings_client():
    """Get embeddings client (mock or real based on environment)"""
    import os
    
    if os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true":
        return MockEmbeddings()
    else:
        import openai
        return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_whisper_client():
    """Get Whisper client (mock or real based on environment)"""
    import os
    
    if os.getenv("USE_MOCK_WHISPER", "false").lower() == "true":
        return MockWhisper()
    else:
        import whisper
        model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        return whisper.load_model(model_size)


def get_email_service():
    """Get email service (mock or real based on environment)"""
    import os
    
    if os.getenv("EMAIL_CONSOLE_MODE", "true").lower() == "true":
        return MockEmailService()
    else:
        # Import real email service
        from libs.common.email_service import RealEmailService
        return RealEmailService()


def get_payment_provider():
    """Get payment provider (mock or real based on environment)"""
    import os
    
    if os.getenv("PAYMENT_SIMULATION_MODE", "true").lower() == "true":
        return MockPaymentProvider()
    else:
        # Import real payment provider
        from libs.common.payment_provider import RealPaymentProvider
        return RealPaymentProvider()
