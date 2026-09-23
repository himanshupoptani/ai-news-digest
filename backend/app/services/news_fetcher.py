import os
import json
import logging
import requests
import feedparser
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.schemas.news import RawArticle, NewsSearchResponse

logger = logging.getLogger(__name__)

class NewsFetcher:
    """
    Hybrid News Aggregation Service:
    1. NewsAPI (REST API when key available)
    2. Curated Open RSS Feeds (Free live news without rate limits)
    3. Offline Sample Snapshot (Zero-failure demo mode)
    """

    # High-quality open RSS feeds covering Tech, AI, and World News
    RSS_FEEDS = [
        {"name": "BBC Tech", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "category": "Technology"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Technology"},
        {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "category": "Technology"},
    ]

    def __init__(self):
        self.sample_data_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../data/sample_news.json")
        )

    def search(self, query: str, limit: int = 10, mode: Optional[str] = None) -> NewsSearchResponse:
        """
        Main entrypoint: Retrieves news articles based on configured mode and query.
        Guarantees results via graceful fallback.
        """
        target_mode = mode or settings.APP_MODE

        # 1. If explicitly in demo mode, use offline curated fixtures
        if target_mode == "demo":
            articles = self.fetch_offline_sample(query, limit=limit)
            return NewsSearchResponse(
                query=query,
                mode_used="offline-demo",
                total_found=len(articles),
                articles=articles
            )

        # 2. If in live mode, try Live APIs or Live RSS
        articles = []
        mode_used = "live-rss"

        if settings.NEWS_API_KEY:
            try:
                articles = self.fetch_from_news_api(query, limit=limit)
                if articles:
                    mode_used = "live-api"
            except Exception as e:
                logger.warning(f"NewsAPI request failed: {e}. Falling back to RSS.")

        # If NewsAPI didn't yield results, use live RSS feeds
        if not articles:
            try:
                articles = self.fetch_from_rss(query, limit=limit)
            except Exception as e:
                logger.warning(f"Live RSS fetch failed: {e}. Falling back to offline snapshot.")

        # 3. Graceful Fallback: If live yielded nothing (e.g. no internet/offline), use offline dataset
        if not articles:
            articles = self.fetch_offline_sample(query, limit=limit)
            mode_used = "offline-demo (fallback)"

        return NewsSearchResponse(
            query=query,
            mode_used=mode_used,
            total_found=len(articles),
            articles=articles
        )

    def fetch_offline_sample(self, query: str, limit: int = 10) -> List[RawArticle]:
        """Loads and filters articles from the local sample dataset."""
        if not os.path.exists(self.sample_data_path):
            return []

        try:
            with open(self.sample_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            query_tokens = [q.lower().strip() for q in query.split() if len(q) > 2]
            results = []

            for item in data:
                text_to_search = f"{item.get('title', '')} {item.get('content', '')} {item.get('category', '')}".lower()
                
                # If query is general (e.g., "news", "latest") or matches query tokens
                if not query_tokens or any(token in text_to_search for token in query_tokens):
                    results.append(
                        RawArticle(
                            title=item["title"],
                            url=item["url"],
                            source_name=item.get("source_name", "Unknown Source"),
                            author=item.get("author", "Staff Writer"),
                            published_at=item.get("published_at"),
                            content=item["content"],
                            category=item.get("category", "General")
                        )
                    )

            # If specific query produced no matches, return top sample articles rather than empty list
            if not results and data:
                results = [
                    RawArticle(
                        title=item["title"],
                        url=item["url"],
                        source_name=item.get("source_name", "Unknown Source"),
                        author=item.get("author", "Staff Writer"),
                        published_at=item.get("published_at"),
                        content=item["content"],
                        category=item.get("category", "General")
                    )
                    for item in data[:limit]
                ]

            return results[:limit]

        except Exception as e:
            logger.error(f"Error loading offline sample news: {e}")
            return []

    def fetch_from_rss(self, query: str, limit: int = 10) -> List[RawArticle]:
        """Fetches live items from curated RSS feeds and filters by search query."""
        results = []
        query_tokens = [q.lower().strip() for q in query.split() if len(q) > 2]

        for feed in self.RSS_FEEDS:
            try:
                parsed = feedparser.parse(feed["url"])
                for entry in parsed.entries[:15]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description", "")
                    content_text = f"{title} {summary}".lower()

                    # Match relevance
                    if not query_tokens or any(token in content_text for token in query_tokens):
                        results.append(
                            RawArticle(
                                title=title,
                                url=entry.get("link", ""),
                                source_name=feed["name"],
                                author=entry.get("author", feed["name"]),
                                published_at=entry.get("published", datetime.now(timezone.utc).isoformat()),
                                content=summary,
                                category=feed["category"]
                            )
                        )
                        if len(results) >= limit:
                            break
            except Exception as e:
                logger.warning(f"Failed parsing RSS feed {feed['name']}: {e}")
                continue

            if len(results) >= limit:
                break

        return results[:limit]

    def fetch_from_news_api(self, query: str, limit: int = 10) -> List[RawArticle]:
        """Calls the live NewsAPI endpoint if configured."""
        if not settings.NEWS_API_KEY:
            return []

        url = "https://newsapi.org/v2/everything"
        # Using 'relevancy' ensures specific queries like 'apple earnings' return relevant stories instead of random fruit exports
        params = {
            "q": query,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": min(20, max(limit * 2, 10)),
            "apiKey": settings.NEWS_API_KEY
        }

        try:
            response = requests.get(url, params=params, timeout=8)
            if response.status_code != 200:
                logger.error(f"NewsAPI returned error: {response.status_code}")
                return []
            data = response.json()
        except Exception as e:
            logger.error(f"NewsAPI request failed: {e}")
            return []
        articles = []
        for item in data.get("articles", []):
            articles.append(
                RawArticle(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    source_name=item.get("source", {}).get("name", "NewsAPI Source"),
                    author=item.get("author", "Staff Writer"),
                    published_at=item.get("publishedAt"),
                    content=item.get("description", "") or item.get("content", ""),
                    image_url=item.get("urlToImage")
                )
            )
        return articles

# Singleton instance for easy import across services
news_fetcher = NewsFetcher()

