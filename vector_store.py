import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

class SimpleVectorStore:
    """A simple vector store implementation using TF-IDF and cosine similarity"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.vectors = None
        self.chunks = []
        
    def add_texts(self, text_chunks):
        """Add text chunks to the vector store."""
        self.chunks = text_chunks
        
        # Create TF-IDF vectors
        self.vectors = self.vectorizer.fit_transform(text_chunks)
        
        return len(text_chunks)
    
    def similarity_search(self, query, k=3):
        """Find chunks relevant to the query."""
        if self.vectors is None or not self.chunks:
            return []
        
        # Transform query to vector
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.vectors)[0]
        
        # Get top k indices
        top_indices = np.argsort(similarity_scores)[::-1][:k]
        
        # Return the relevant chunks with scores
        results = [
            {"content": self.chunks[idx], "score": float(similarity_scores[idx])}
            for idx in top_indices
        ]
        
        return results

def create_vector_store(text_chunks):
    """Create a vector store from text chunks for semantic search."""
    try:
        vector_store = SimpleVectorStore()
        vector_store.add_texts(text_chunks)
        return vector_store
    
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        return None

def find_relevant_chunks(vector_store, query, k=3):
    """Find chunks relevant to the query."""
    if not vector_store:
        return []
    
    results = vector_store.similarity_search(query, k=k)
    return [result["content"] for result in results]

def get_document_stats(vector_store):
    """Get statistics about the documents in the vector store"""
    if not vector_store or not vector_store.chunks:
        return {
            "chunk_count": 0,
            "total_tokens": 0,
            "avg_chunk_size": 0
        }
    
    # Calculate some basic stats
    chunk_count = len(vector_store.chunks)
    total_tokens = sum(len(chunk.split()) for chunk in vector_store.chunks)
    avg_chunk_size = total_tokens / chunk_count if chunk_count > 0 else 0
    
    return {
        "chunk_count": chunk_count,
        "total_tokens": total_tokens,
        "avg_chunk_size": avg_chunk_size
    }