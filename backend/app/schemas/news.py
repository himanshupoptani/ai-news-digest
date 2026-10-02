from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class ArticleIntelligence(BaseModel):
    """Deep analytical metadata extracted from an article."""
    sentiment: str = "Neutral"  # Bullish, Bearish, Neutral
    sentiment_score: float = 0.0  # -1.0 to +1.0
    entities: List[str] = []  # Companies, leaders, tech terms
    impact_level: str = "Medium"  # High, Medium, Low
    reading_time_min: int = 2

class RawArticle(BaseModel):
    """Unified Data Transfer Object for articles ingested from any source (API, RSS, Demo)."""
    title: str
    url: str
    source_name: str
    author: Optional[str] = "Editorial Staff"
    published_at: Optional[str] = None
    content: str
    category: Optional[str] = "General"
    image_url: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    intelligence: Optional[ArticleIntelligence] = None

class NewsSearchRequest(BaseModel):
    """Schema for incoming news search queries."""
    query: str = Field(..., min_length=2, description="Search terms, e.g., 'artificial intelligence', 'Nvidia'")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum articles to retrieve")
    mode: Optional[str] = Field(default=None, description="Force 'live' or 'demo' mode. Defaults to app config.")

class EventClusterDTO(BaseModel):
    event_id: str
    headline: str
    source_count: int
    sources: List[str] = []
    is_developing: bool = False
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    coverage_score: float = 0.0

class NewsSearchResponse(BaseModel):
    """Schema for returning search results with metadata."""
    query: str
    mode_used: str
    total_found: int
    articles: List[RawArticle]
    coverage: Optional[Dict[str, Any]] = None
    events: Optional[List[EventClusterDTO]] = None

class HeadlinesResponse(BaseModel):
    """Real-time breaking headlines feed grouped by category."""
    category: str
    mode_used: str
    total_count: int
    articles: List[RawArticle]

