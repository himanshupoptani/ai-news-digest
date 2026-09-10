from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

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

class NewsSearchRequest(BaseModel):
    """Schema for incoming news search queries."""
    query: str = Field(..., min_length=2, description="Search terms, e.g., 'artificial intelligence', 'Nvidia'")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum articles to retrieve")
    mode: Optional[str] = Field(default=None, description="Force 'live' or 'demo' mode. Defaults to app config.")

class NewsSearchResponse(BaseModel):
    """Schema for returning search results with metadata."""
    query: str
    mode_used: str  # 'live-api', 'live-rss', or 'offline-demo'
    total_found: int
    articles: List[RawArticle]
