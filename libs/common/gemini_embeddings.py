"""
Google Gemini Embeddings Integration for Bwenge OS
Provides embeddings using Google's Gemini API
"""
import os
from typing import List, Dict, Any
from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)


class GeminiEmbeddings:
    """Google Gemini embeddings service"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini embeddings client
        
        Args:
            api_key: Google Gemini API key (optional, reads from env if not provided)
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in environment variables or pass it to constructor."
            )
        
        # Set environment variable for the client
        os.environ["GEMINI_API_KEY"] = self.api_key
        
        try:
            # Initialize the Gemini client
            self.client = genai.Client()
            self.model = "gemini-embedding-001"
            logger.info(f"✅ Gemini embeddings client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def create(self, input: str or List[str], **kwargs) -> Dict[str, Any]:
        """
        Create embeddings for text input (OpenAI-compatible interface)
        
        Args:
            input: Single string or list of strings to embed
            **kwargs: Additional parameters (ignored for compatibility)
        
        Returns:
            Dict with OpenAI-compatible format:
            {
                "data": [
                    {"embedding": [...], "index": 0},
                    ...
                ],
                "model": "gemini-embedding-001",
                "usage": {"prompt_tokens": ..., "total_tokens": ...}
            }
        """
        # Convert single string to list
        if isinstance(input, str):
            input = [input]
        
        try:
            # Call Gemini API for embeddings
            response = self.client.models.embed_content(
                model=self.model,
                contents=input,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"  # Optimized for RAG
                )
            )
            
            # Convert to OpenAI-compatible format
            embeddings_data = []
            for i, emb in enumerate(response.embeddings):
                embeddings_data.append({
                    "embedding": emb.values,
                    "index": i,
                    "object": "embedding"
                })
            
            # Calculate token usage (approximate)
            total_tokens = sum(len(text.split()) for text in input)
            
            result = {
                "data": embeddings_data,
                "model": self.model,
                "object": "list",
                "usage": {
                    "prompt_tokens": total_tokens,
                    "total_tokens": total_tokens
                }
            }
            
            logger.info(f"✅ Generated {len(embeddings_data)} embeddings, dimension: {len(embeddings_data[0]['embedding'])}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text (for RAG retrieval)
        
        Args:
            text: Query text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=[text],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY"  # Optimized for queries
                )
            )
            
            embedding = response.embeddings[0].values
            logger.info(f"✅ Generated query embedding, dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents (for RAG indexing)
        
        Args:
            texts: List of document texts to embed
        
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"  # Optimized for documents
                )
            )
            
            embeddings = [emb.values for emb in response.embeddings]
            logger.info(f"✅ Generated {len(embeddings)} document embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate document embeddings: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model
        
        Returns:
            Integer dimension (768 for gemini-embedding-001)
        """
        # Gemini embedding-001 produces 768-dimensional vectors
        return 768


# Factory function for easy integration
def get_gemini_embeddings(api_key: str = None) -> GeminiEmbeddings:
    """
    Factory function to create Gemini embeddings client
    
    Args:
        api_key: Optional API key (reads from env if not provided)
    
    Returns:
        GeminiEmbeddings instance
    """
    return GeminiEmbeddings(api_key=api_key)


# Example usage and testing
if __name__ == "__main__":
    # Test the embeddings
    print("Testing Gemini Embeddings...")
    
    try:
        # Initialize
        embeddings = GeminiEmbeddings()
        
        # Test single embedding
        print("\n1. Single text embedding:")
        text = "The quick brown fox jumps over the lazy dog."
        result = embeddings.create(text)
        print(f"   Dimension: {len(result['data'][0]['embedding'])}")
        print(f"   First 5 values: {result['data'][0]['embedding'][:5]}")
        
        # Test batch embeddings
        print("\n2. Batch embeddings:")
        texts = [
            "A dog wearing a red collar runs through a green field.",
            "The process for generating a numerical vector from text is called embedding.",
            "Using a vector database helps with efficient semantic search."
        ]
        result = embeddings.create(texts)
        print(f"   Generated {len(result['data'])} embeddings")
        print(f"   Dimension: {len(result['data'][0]['embedding'])}")
        
        # Test query embedding
        print("\n3. Query embedding:")
        query = "What is semantic search?"
        query_emb = embeddings.embed_query(query)
        print(f"   Dimension: {len(query_emb)}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure GEMINI_API_KEY is set in your environment")
