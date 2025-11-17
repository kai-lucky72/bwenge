import os
import openai
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    """Orchestrates calls to various LLM providers"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        self.default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-3.5-turbo")
    
    async def generate_response(
        self,
        persona: Any,
        user_message: str,
        context: List[Dict[str, Any]],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response using LLM with persona and context"""
        
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(persona, context)
            
            # Build conversation history
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Add session context if available
            if session_context and session_context.get("conversation_history"):
                # Insert conversation history before the current message
                history = session_context["conversation_history"][-5:]  # Last 5 messages
                messages = [messages[0]] + history + [messages[1]]
            
            # Call OpenAI
            response = await self._call_openai(messages)
            
            # Parse response and extract actions/animations
            parsed_response = self._parse_response(response, context)
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback response
            return {
                "text": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "actions": [],
                "citations": [],
                "animation_hint": "neutral"
            }
    
    def _build_system_prompt(self, persona: Any, context: List[Dict[str, Any]]) -> str:
        """Build system prompt with persona and context"""
        
        # Base persona prompt
        prompt_parts = [
            f"You are {persona.name}, an AI assistant with the following characteristics:",
            f"Description: {persona.description or 'A helpful AI assistant'}",
        ]
        
        # Add tone instructions
        if persona.tone:
            tone_str = ", ".join([f"{k}: {v}" for k, v in persona.tone.items()])
            prompt_parts.append(f"Tone and style: {tone_str}")
        
        # Add rules
        if persona.rules:
            rules_str = "\n".join([f"- {rule}" for rule in persona.rules.get("guidelines", [])])
            if rules_str:
                prompt_parts.append(f"Guidelines:\n{rules_str}")
        
        # Add safety rules
        if persona.safety_rules:
            safety_str = "\n".join([f"- {rule}" for rule in persona.safety_rules])
            prompt_parts.append(f"Safety rules:\n{safety_str}")
        
        # Add context from knowledge base
        if context:
            context_str = "\n\n".join([
                f"Source {i+1}: {item['text']}"
                for i, item in enumerate(context[:3])  # Top 3 most relevant
            ])
            prompt_parts.append(f"Relevant knowledge:\n{context_str}")
        
        # Add response format instructions
        prompt_parts.extend([
            "",
            "Response format:",
            "- Provide helpful, accurate responses based on the knowledge provided",
            "- If you reference specific information, cite the source",
            "- Suggest appropriate animations/gestures when relevant",
            "- Keep responses conversational and engaging"
        ])
        
        return "\n\n".join(prompt_parts)
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            # Try fallback model
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as fallback_e:
                logger.error(f"Fallback model also failed: {fallback_e}")
                raise e
    
    def _parse_response(self, response_text: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse LLM response and extract structured information"""
        
        # For now, simple parsing. In production, you might use function calling
        # or structured output formats
        
        # Extract animation hints based on content
        animation_hint = self._extract_animation_hint(response_text)
        
        # Create citations for referenced context
        citations = []
        for i, ctx in enumerate(context[:3]):
            if self._is_context_referenced(response_text, ctx["text"]):
                citations.append({
                    "source_id": ctx["source_id"],
                    "chunk_id": ctx["chunk_id"],
                    "text": ctx["text"][:100] + "...",
                    "relevance_score": ctx.get("score", 0.0)
                })
        
        # Extract actions (placeholder for future functionality)
        actions = []
        
        return {
            "text": response_text,
            "actions": actions,
            "citations": citations,
            "animation_hint": animation_hint
        }
    
    def _extract_animation_hint(self, text: str) -> str:
        """Extract animation hint from response text"""
        text_lower = text.lower()
        
        # Simple keyword-based animation detection
        if any(word in text_lower for word in ["excited", "happy", "great", "wonderful"]):
            return "happy"
        elif any(word in text_lower for word in ["thinking", "consider", "analyze"]):
            return "thinking"
        elif any(word in text_lower for word in ["explain", "show", "demonstrate"]):
            return "explaining"
        elif any(word in text_lower for word in ["welcome", "hello", "hi"]):
            return "greeting"
        else:
            return "neutral"
    
    def _is_context_referenced(self, response: str, context_text: str) -> bool:
        """Check if context is referenced in response"""
        # Simple check - look for overlapping keywords
        response_words = set(response.lower().split())
        context_words = set(context_text.lower().split())
        
        # If more than 2 words overlap, consider it referenced
        overlap = len(response_words.intersection(context_words))
        return overlap > 2