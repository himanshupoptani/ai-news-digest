from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.schemas.news import NewsSearchRequest, NewsSearchResponse, RawArticle
from backend.app.services.news_fetcher import news_fetcher
from backend.app.services.text_processor import text_processor
from backend.app.services.rational_agent import rational_agent

router = APIRouter(prefix="/api/news", tags=["News Retrieval & Search"])

@router.post("/search", response_model=NewsSearchResponse)
def search_news(request: NewsSearchRequest):
    """
    Search news articles across live APIs, RSS feeds, or offline sample data.
    Automatically applies text cleaning, deduplication, and rational agent ranking.
    """
    # 1. Ingest candidate articles
    raw_response = news_fetcher.search(query=request.query, limit=request.limit * 2, mode=request.mode)
    
    # 2. Text cleaning & deduplication
    unique_articles, duplicate_clusters = text_processor.deduplicate_articles(raw_response.articles)

    # 3. Rational agent evaluation & ranking
    ranked_tuples = rational_agent.rank_and_select(unique_articles, query=request.query, top_k=request.limit)
    final_selected = [art for art, breakdown in ranked_tuples]

    return NewsSearchResponse(
        query=request.query,
        mode_used=raw_response.mode_used,
        total_found=len(final_selected),
        articles=final_selected,
        coverage=raw_response.coverage,
        events=raw_response.events
    )

@router.get("/headlines")
def get_top_headlines(
    category: str = Query(default="all", description="Category: all, tech, business, science, ai"),
    limit: int = Query(default=12, ge=1, le=30)
):
    """Returns breaking news headlines enriched with sentiment, entities, and impact level."""
    from backend.app.config import settings as app_settings
    articles = news_fetcher.fetch_top_headlines(category=category, limit=limit)
    mode = "live-api" if app_settings.NEWS_API_KEY and app_settings.APP_MODE == "live" else "live-rss"
    return {
        "category": category,
        "mode_used": mode,
        "total_count": len(articles),
        "articles": [a.model_dump() for a in articles]
    }


