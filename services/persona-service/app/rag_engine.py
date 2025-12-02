import os
import weaviate
from typing import List, Dict, Any
import logging
import sys

# Add libs to path
sys.path.append('/app')
from libs.common.gemini_embeddings import GeminiEmbeddings

logger = logging.getLogger(__name__)

class RAGEngine:
    """Retrieval-Augmented Generation engine"""
    
    def __init__(self):
        self.weaviate_client = weaviate.Client(url=os.getenv("WEAVIATE_URL", "http://localhost:8080"))
        
        # Initialize Gemini embeddings
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.embeddings_client = GeminiEmbeddings(api_key=gemini_api_key)
    
    def retrieve_context(
        self,
        query: str,
        persona_id: str,
        org_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        
        try:
            # Create query embedding
            query_embedding = self._create_query_embedding(query)
            
            # Search in Weaviate
            results = self._search_weaviate(
                query_embedding=query_embedding,
                persona_id=persona_id,
                org_id=org_id,
                top_k=top_k
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []
    
    def _create_query_embedding(self, query: str) -> List[float]:
        """Create embedding for search query using Gemini"""
        try:
            # Use Gemini's query-optimized embedding
            return self.embeddings_client.embed_query(query)
        except Exception as e:
            logger.error(f"Failed to create query embedding: {e}")
            raise
    
    def _search_weaviate(
        self,
        query_embedding: List[float],
        persona_id: str,
        org_id: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Search Weaviate for relevant chunks"""
        
        try:
            # Build where filter for tenant isolation
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["org_id"],
                        "operator": "Equal",
                        "valueString": org_id
                    },
                    {
                        "path": ["persona_id"],
                        "operator": "Equal",
                        "valueString": persona_id
                    }
                ]
            }
            
            # Perform vector search
            result = (
                self.weaviate_client.query
                .get("KnowledgeChunk", [
                    "text",
                    "source_id",
                    "chunk_id",
                    "chunk_index"
                ])
                .with_near_vector({
                    "vector": query_embedding
                })
                .with_where(where_filter)
                .with_limit(top_k)
                .with_additional(["distance"])
                .do()
            )
            
            # Process results
            chunks = []
            if result.get("data") and result["data"].get("Get") and result["data"]["Get"].get("KnowledgeChunk"):
                for item in result["data"]["Get"]["KnowledgeChunk"]:
                    chunks.append({
                        "text": item["text"],
                        "source_id": item["source_id"],
                        "chunk_id": item["chunk_id"],
                        "chunk_index": item["chunk_index"],
                        "score": 1.0 - item["_additional"]["distance"]  # Convert distance to similarity
                    })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Weaviate search failed: {e}")
            return []
    
    def search_by_keywords(
        self,
        keywords: List[str],
        persona_id: str,
        org_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search by keywords using BM25"""
        
        try:
            # Build where filter
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["org_id"],
                        "operator": "Equal",
                        "valueString": org_id
                    },
                    {
                        "path": ["persona_id"],
                        "operator": "Equal",
                        "valueString": persona_id
                    }
                ]
            }
            
            # Build BM25 query
            query_text = " ".join(keywords)
            
            result = (
                self.weaviate_client.query
                .get("KnowledgeChunk", [
                    "text",
                    "source_id",
                    "chunk_id",
                    "chunk_index"
                ])
                .with_bm25(query=query_text)
                .with_where(where_filter)
                .with_limit(top_k)
                .with_additional(["score"])
                .do()
            )
            
            # Process results
            chunks = []
            if result.get("data") and result["data"].get("Get") and result["data"]["Get"].get("KnowledgeChunk"):
                for item in result["data"]["Get"]["KnowledgeChunk"]:
                    chunks.append({
                        "text": item["text"],
                        "source_id": item["source_id"],
                        "chunk_id": item["chunk_id"],
                        "chunk_index": item["chunk_index"],
                        "score": item["_additional"]["score"]
                    })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        persona_id: str,
        org_id: str,
        top_k: int = 5,
        alpha: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining vector and keyword search"""
        
        try:
            # Get vector search results
            vector_results = self.retrieve_context(query, persona_id, org_id, top_k)
            
            # Get keyword search results
            keywords = query.split()  # Simple keyword extraction
            keyword_results = self.search_by_keywords(keywords, persona_id, org_id, top_k)
            
            # Combine and re-rank results
            combined_results = self._combine_search_results(
                vector_results, keyword_results, alpha
            )
            
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return self.retrieve_context(query, persona_id, org_id, top_k)
    
    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        alpha: float
    ) -> List[Dict[str, Any]]:
        """Combine vector and keyword search results"""
        
        # Create a map of chunk_id to results
        result_map = {}
        
        # Add vector results
        for result in vector_results:
            chunk_id = result["chunk_id"]
            result_map[chunk_id] = result.copy()
            result_map[chunk_id]["vector_score"] = result["score"]
            result_map[chunk_id]["keyword_score"] = 0.0
        
        # Add keyword results
        for result in keyword_results:
            chunk_id = result["chunk_id"]
            if chunk_id in result_map:
                result_map[chunk_id]["keyword_score"] = result["score"]
            else:
                result_map[chunk_id] = result.copy()
                result_map[chunk_id]["vector_score"] = 0.0
                result_map[chunk_id]["keyword_score"] = result["score"]
        
        # Calculate combined scores
        for chunk_id, result in result_map.items():
            vector_score = result.get("vector_score", 0.0)
            keyword_score = result.get("keyword_score", 0.0)
            
            # Normalize scores (simple min-max normalization)
            combined_score = alpha * vector_score + (1 - alpha) * keyword_score
            result["score"] = combined_score
        
        # Sort by combined score
        sorted_results = sorted(
            result_map.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        return sorted_results