import re
from collections import Counter
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.article import Article
from backend.app.models.source import Source
from backend.app.models.topic import Topic
from backend.app.schemas.news import RawArticle
from backend.app.schemas.analytics import TrendingTopic, AnalyticsDashboardResponse

class AnalyticsService:
    """
    Analytics & Trending Topics Service:
    - Calculates trending tags and trend scores
    - Computes macro category and publisher distributions
    - Aggregates article Finite State Machine metrics
    """

    # Predefined high-interest news entity anchors
    TRACKED_ENTITIES = [
        {"tag": "#AI", "name": "Artificial Intelligence", "keywords": ["ai", "artificial intelligence", "llm", "frontier", "models"], "category": "AI"},
        {"tag": "#Nvidia", "name": "Nvidia & Hardware", "keywords": ["nvidia", "blackwell", "gpu", "chips", "hardware"], "category": "Tech"},
        {"tag": "#Semiconductors", "name": "Global Chip Fabrication", "keywords": ["semiconductor", "tsmc", "foundry", "2nm", "rapidus"], "category": "Tech"},
        {"tag": "#Economy", "name": "Federal Reserve & Inflation", "keywords": ["fed", "federal reserve", "rates", "interest", "inflation"], "category": "Economy"},
        {"tag": "#Space", "name": "NASA Artemis Mission", "keywords": ["nasa", "artemis", "sls", "rocket", "moon"], "category": "Science"},
    ]

    @classmethod
    def calculate_trending_topics(cls, articles: List[RawArticle]) -> List[TrendingTopic]:
        """
        Scans articles to count entity mentions, unique publishers, and computes trend score:
        Trend Score = (Count * 10) + (Unique Publishers * 15)
        """
        if not articles:
            return []

        trending: List[TrendingTopic] = []

        for entity in cls.TRACKED_ENTITIES:
            matching_articles = []
            distinct_sources = set()

            for art in articles:
                text_corpus = f"{art.title} {art.content}".lower()
                if any(kw in text_corpus for kw in entity["keywords"]):
                    matching_articles.append(art)
                    distinct_sources.add(art.source_name)

            count = len(matching_articles)
            if count > 0:
                score = round((count * 10.0) + (len(distinct_sources) * 15.0), 1)
                trending.append(
                    TrendingTopic(
                        tag=entity["tag"],
                        name=entity["name"],
                        article_count=count,
                        source_count=len(distinct_sources),
                        trend_score=score,
                        category=entity["category"]
                    )
                )

        # Sort descending by trend score
        trending.sort(key=lambda x: x.trend_score, reverse=True)
        return trending

    @classmethod
    def generate_dashboard_analytics(
        cls, 
        articles: List[RawArticle], 
        db: Session
    ) -> AnalyticsDashboardResponse:
        """
        Compiles high-level macro statistics for dashboard charts and visual analytics.
        """
        # Topic / Category distribution
        categories = [a.category or "General" for a in articles]
        category_counts = dict(Counter(categories))

        # Source distribution
        sources = [a.source_name or "Unknown" for a in articles]
        source_counts = dict(Counter(sources))

        # Trending topics
        trending = cls.calculate_trending_topics(articles)

        # Database statistics
        db_articles_count = db.query(Article).count()
        db_sources_count = db.query(Source).count()
        db_topics_count = db.query(Topic).count()

        # FSM state breakdown from database
        db_articles = db.query(Article).all()
        fsm_states = [a.current_state for a in db_articles]
        fsm_summary = dict(Counter(fsm_states))

        return AnalyticsDashboardResponse(
            total_articles=len(articles) if articles else db_articles_count,
            total_sources=len(source_counts) if source_counts else db_sources_count,
            total_topics=len(category_counts) if category_counts else db_topics_count,
            topic_distribution=category_counts,
            source_distribution=source_counts,
            trending_topics=trending,
            fsm_state_summary=fsm_summary
        )

# Singleton instance
analytics_service = AnalyticsService()
