import re
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.schemas.news import RawArticle
from backend.app.services.text_processor import TextProcessor

class DocumentChunk(BaseModel):
    """Represents an atomic text passage indexed in the vector store with metadata."""
    chunk_id: str
    article_title: str
    source_name: str
    url: str
    text: str
    chunk_index: int

class SearchResult(BaseModel):
    """Represents a retrieved chunk with its similarity score."""
    chunk: DocumentChunk
    similarity_score: float

class InMemoryVectorStore:
    """
    High-performance In-Memory Semantic Vector Store.
    Features:
    - Sliding window chunking with configurable overlap
    - TF-IDF vector embeddings with sublinear term-frequency scaling
    - Cosine similarity ranking with relevance threshold filtering
    - Zero external database dependencies (viva & demo safe)
    """

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 120, overlap: int = 25) -> List[str]:
        """
        Splits text into chunks of `chunk_size` words with `overlap` words of shared context.
        """
        words = text.split()
        if not words:
            return []

        if len(words) <= chunk_size:
            return [text]

        chunks = []
        step = max(1, chunk_size - overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size]
            chunks.append(" ".join(chunk_words))
            if i + chunk_size >= len(words):
                break

        return chunks

    def add_articles(self, articles: List[RawArticle], chunk_size: int = 120, overlap: int = 25) -> int:
        """
        Chunks and indexes an entire batch of articles into the vector store.
        Returns the total count of chunks indexed.
        """
        self.clear()
        all_chunks: List[DocumentChunk] = []

        for art_idx, art in enumerate(articles):
            clean_body = TextProcessor.clean_text(art.content)
            # Prepend title to the first chunk to ensure title context is searchable
            full_text = f"{art.title}. {clean_body}"
            passages = self.chunk_text(full_text, chunk_size=chunk_size, overlap=overlap)

            for c_idx, passage in enumerate(passages):
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=f"art_{art_idx}_chk_{c_idx}",
                        article_title=art.title,
                        source_name=art.source_name,
                        url=art.url,
                        text=passage,
                        chunk_index=c_idx
                    )
                )

        if not all_chunks:
            return 0

        self.chunks = all_chunks

        # Build TF-IDF vector space model across all chunk texts
        corpus = [c.text for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            sublinear_tf=True,
            ngram_range=(1, 2)  # Unigrams + Bigrams for rich semantic phrases
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        return len(self.chunks)

    def similarity_search(
        self, 
        query: str, 
        top_k: int = 4, 
        min_score: float = 0.10
    ) -> List[SearchResult]:
        """
        Finds the top-K most semantically relevant chunks for a user query.
        Filters out any chunks below the min_score threshold.
        """
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        clean_query = TextProcessor.clean_text(query)
        if not clean_query.strip():
            return []

        try:
            query_vec = self.vectorizer.transform([clean_query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

            # Pair each chunk with its cosine similarity score
            scored_results = []
            for idx, score in enumerate(similarities):
                if score >= min_score:
                    scored_results.append(
                        SearchResult(
                            chunk=self.chunks[idx],
                            similarity_score=round(float(score), 4)
                        )
                    )

            # Sort descending by similarity score
            scored_results.sort(key=lambda x: x.similarity_score, reverse=True)
            return scored_results[:top_k]

        except Exception:
            return []

    def clear(self):
        """Resets the vector store."""
        self.chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None

# Singleton instance
vector_store = InMemoryVectorStore()

