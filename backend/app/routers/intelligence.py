from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database import get_db
from backend.app.schemas.graph import GraphDataResponse
from backend.app.schemas.timeline import TimelineResponse
from backend.app.schemas.analytics import AnalyticsDashboardResponse
from backend.app.services.news_fetcher import news_fetcher
from backend.app.services.graph_service import graph_service
from backend.app.services.timeline_service import timeline_service
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/intelligence", tags=["Knowledge Graph, Timeline & Analytics"])

@router.get("/graph", response_model=GraphDataResponse)
def get_knowledge_graph(
    topic: Optional[str] = Query(default=None, description="Topic filter for article graph"),
    db: Session = Depends(get_db)
):
    """
    Returns the Knowledge Graph payload:
    - If 'topic' query is provided: Returns multi-layer Article-Source-Topic graph.
    - If no topic: Returns the hierarchical Topic Taxonomy graph from SQLite.
    """
    if topic:
        res = news_fetcher.search(query=topic, limit=6)
        return graph_service.build_article_intelligence_graph(res.articles, query_topic=topic)
    return graph_service.build_topic_taxonomy_graph(db)

@router.get("/timeline", response_model=TimelineResponse)
def get_event_timeline(
    query: str = Query(default="Artificial Intelligence", description="News event topic")
):
    """Returns chronologically sorted milestone events for the requested topic."""
    res = news_fetcher.search(query=query, limit=6)
    return timeline_service.generate_timeline(res.articles, event_topic=query)

@router.get("/analytics", response_model=AnalyticsDashboardResponse)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Returns macro dashboard metrics, trend scores, and category distributions."""
    res = news_fetcher.search(query="news", limit=20)
    articles = list(res.articles)
    # Ensure offline sample dataset is also represented for complete analytics coverage
    offline_samples = news_fetcher.fetch_offline_sample("news", limit=15)
    seen_urls = {a.url for a in articles}
    for off in offline_samples:
        if off.url not in seen_urls:
            articles.append(off)
            seen_urls.add(off.url)
    return analytics_service.generate_dashboard_analytics(articles, db)

