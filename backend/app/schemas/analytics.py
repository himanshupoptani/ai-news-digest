from pydantic import BaseModel
from typing import List, Dict, Any

class TrendingTopic(BaseModel):
    """Represents a trending topic/hashtag with dynamic scoring."""
    tag: str
    name: str
    article_count: int
    source_count: int
    trend_score: float
    category: str

class AnalyticsDashboardResponse(BaseModel):
    """Macro analytics payload for charts and dashboard visualization."""
    total_articles: int
    total_sources: int
    total_topics: int
    topic_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    trending_topics: List[TrendingTopic]
    fsm_state_summary: Dict[str, int]

