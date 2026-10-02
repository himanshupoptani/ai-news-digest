"""
event_clustering.py — Event Clustering & Deduplication Engine

Groups related articles about the same event together using
TF-IDF cosine similarity (no external ML dependencies needed).
"""

from __future__ import annotations
import re
import math
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from backend.app.schemas.news import RawArticle

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "will", "would", "could", "should", "may", "might",
    "its", "it", "this", "that", "as", "not", "no", "up", "out", "if",
    "about", "after", "before", "into", "over", "than", "then", "so",
    "news", "latest", "breaking", "update", "report", "says", "said",
    "new", "day", "today", "week", "month", "year", "time", "now",
}


@dataclass
class NewsEvent:
    """A cluster of related articles describing the same event."""
    event_id: str
    headline: str                    # Most representative title
    articles: List[RawArticle]
    source_count: int = 0
    sources: List[str] = field(default_factory=list)
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    is_developing: bool = False      # Multiple independent sources = developing
    primary_article: Optional[RawArticle] = None
    coverage_score: float = 0.0      # Higher = more corroborated


def _tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS]


def _tfidf_vectors(docs: List[List[str]]) -> List[Dict[str, float]]:
    """Compute TF-IDF vectors for a list of token lists."""
    N = len(docs)
    if N == 0:
        return []

    # Document frequency
    df: Dict[str, int] = defaultdict(int)
    for tokens in docs:
        for word in set(tokens):
            df[word] += 1

    vectors = []
    for tokens in docs:
        tf: Dict[str, float] = defaultdict(float)
        for word in tokens:
            tf[word] += 1.0
        total = max(len(tokens), 1)
        vec: Dict[str, float] = {}
        for word, count in tf.items():
            tfidf = (count / total) * math.log((N + 1) / (df[word] + 1))
            vec[word] = tfidf
        vectors.append(vec)
    return vectors


def _cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    """Cosine similarity between two TF-IDF vectors."""
    common = set(v1.keys()) & set(v2.keys())
    if not common:
        return 0.0
    dot = sum(v1[w] * v2[w] for w in common)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


class EventClusteringEngine:
    """
    Clusters news articles into events using TF-IDF cosine similarity.
    Threshold 0.35 = articles must share ~35% semantic content to be grouped.
    """

    def __init__(self, similarity_threshold: float = 0.35):
        self.threshold = similarity_threshold

    def cluster(self, articles: List[RawArticle]) -> List[NewsEvent]:
        """
        Group articles into events. Returns list of events sorted by
        coverage_score (most corroborated first).
        """
        if not articles:
            return []

        # Tokenize titles + first 200 chars of content
        docs = [_tokenize(f"{a.title} {(a.content or '')[:200]}") for a in articles]
        vectors = _tfidf_vectors(docs)

        n = len(articles)
        # Union-Find for clustering
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            parent[find(x)] = find(y)

        # Compare all pairs
        for i in range(n):
            for j in range(i + 1, n):
                if vectors[i] and vectors[j]:
                    sim = _cosine_similarity(vectors[i], vectors[j])
                    if sim >= self.threshold:
                        union(i, j)

        # Build clusters
        clusters: Dict[int, List[int]] = defaultdict(list)
        for i in range(n):
            clusters[find(i)].append(i)

        events = []
        for root, indices in clusters.items():
            cluster_articles = [articles[i] for i in indices]
            event = self._build_event(root, cluster_articles)
            events.append(event)

        # Sort: most corroborated first, then by date
        events.sort(key=lambda e: (e.coverage_score, e.latest_date or ""), reverse=True)
        return events

    def _build_event(self, event_id: int, articles: List[RawArticle]) -> NewsEvent:
        """Build a NewsEvent from a cluster of articles."""
        # Sort by date newest first
        def date_key(a):
            return a.published_at or ""
        articles_sorted = sorted(articles, key=date_key, reverse=True)

        # Headline = shortest/most concise title (usually most informative)
        headline = min(articles, key=lambda a: len(a.title)).title

        unique_sources = list({a.source_name for a in articles})
        source_count = len(unique_sources)

        dates = [a.published_at for a in articles if a.published_at]
        earliest = min(dates) if dates else None
        latest = max(dates) if dates else None

        # Developing story = 3+ independent sources
        is_developing = source_count >= 3

        # Coverage score: log(sources) * article_count
        import math
        coverage = math.log(source_count + 1) * len(articles)

        return NewsEvent(
            event_id=f"evt_{event_id}",
            headline=headline,
            articles=articles_sorted,
            source_count=source_count,
            sources=unique_sources[:8],
            earliest_date=earliest,
            latest_date=latest,
            is_developing=is_developing,
            primary_article=articles_sorted[0],
            coverage_score=round(coverage, 3),
        )

    def deduplicate(self, articles: List[RawArticle]) -> List[RawArticle]:
        """
        Fast deduplication using title similarity.
        Returns one representative article per event cluster.
        """
        events = self.cluster(articles)
        return [e.primary_article for e in events if e.primary_article]


# Singleton
event_clusterer = EventClusteringEngine(similarity_threshold=0.35)
