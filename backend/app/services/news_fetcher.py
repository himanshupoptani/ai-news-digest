import os
import json
import logging
import requests
import feedparser
import urllib.parse
import html
import re
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.schemas.news import RawArticle, NewsSearchResponse

logger = logging.getLogger(__name__)

class NewsFetcher:
    """
    Hybrid News Aggregation Service:
    1. Google News RSS Search (Covers EVERY query, topic, company, person worldwide)
    2. NewsAPI (REST API when key available)
    3. Curated Open RSS Feeds (Free live news without rate limits)
    4. Offline Sample Snapshot (Zero-failure demo mode)
    """

    # High-quality open RSS feeds covering Tech, AI, Business, Science and World News
    RSS_FEEDS = [
        {"name": "BBC Tech",        "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",            "category": "Technology"},
        {"name": "TechCrunch",      "url": "https://techcrunch.com/feed/",                                "category": "Technology"},
        {"name": "Ars Technica",    "url": "https://feeds.arstechnica.com/arstechnica/index",             "category": "Technology"},
        {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/",                      "category": "AI"},
        {"name": "Reuters Tech",    "url": "https://feeds.reuters.com/reuters/technologyNews",            "category": "Technology"},
        {"name": "Reuters Business","url": "https://feeds.reuters.com/reuters/businessNews",              "category": "Business"},
        {"name": "BBC Science",     "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml","category": "Science"},
        {"name": "Wired",           "url": "https://www.wired.com/feed/rss",                              "category": "Technology"},
        {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml",                     "category": "Technology"},
    ]

    # Map UI category slug → (NewsAPI top-headlines category OR None, everything search query)
    CATEGORY_MAP = {
        "all":        (None,         "technology OR business OR artificial intelligence"),
        "tech":       ("technology", "technology innovation software hardware"),
        "technology": ("technology", "technology innovation software hardware"),
        "business":   ("business",   "business economy markets stock finance"),
        "finance":    ("business",   "business economy markets stock finance"),
        "ai":         (None,         "artificial intelligence machine learning LLM GPT OpenAI"),
        "science":    ("science",    "science space research discovery NASA"),
    }

    def __init__(self):
        self.sample_data_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../data/sample_news.json")
        )

    def enrich_articles(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Runs the intelligence extractor on all raw articles."""
        from backend.app.services.text_processor import text_processor
        for art in articles:
            if not art.intelligence:
                art.intelligence = text_processor.extract_intelligence(art.title, art.content)
        return articles

    def fetch_from_google_news(self, query: str, limit: int = 15) -> List[RawArticle]:
        """
        Retrieves real-time news articles for ANY query worldwide via Google News RSS.
        Covers all topics: breaking news, local events, specific people, companies, tech, sports, etc.
        """
        results = []
        try:
            encoded = urllib.parse.quote(query.strip())
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit * 2]:
                raw_title = getattr(entry, "title", "").strip()
                if not raw_title:
                    continue

                source_name = getattr(entry, "source", {}).get("title", "")
                if not source_name and " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()
                elif source_name and raw_title.endswith(f" - {source_name}"):
                    title = raw_title[:-len(f" - {source_name}")].strip()
                else:
                    title = raw_title
                    source_name = source_name or "Verified News Source"

                link = getattr(entry, "link", "")
                pub_date = getattr(entry, "published", datetime.now(timezone.utc).isoformat())

                raw_summary = getattr(entry, "summary", "") or title
                clean_text = re.sub(r"<[^>]+>", " ", raw_summary)
                clean_text = html.unescape(clean_text)
                clean_text = re.sub(r"\s+", " ", clean_text).strip()

                if len(clean_text) < 50:
                    clean_text = f"{title}. Reported by {source_name} regarding {query}."

                results.append(
                    RawArticle(
                        title=title,
                        url=link,
                        source_name=source_name,
                        author=source_name,
                        published_at=pub_date,
                        content=clean_text,
                        category="News"
                    )
                )
                if len(results) >= limit:
                    break
        except Exception as e:
            logger.warning(f"Google News search failed for '{query}': {e}")

        return results

    def fetch_google_news_topic(self, category: str, limit: int = 15) -> List[RawArticle]:
        """Fetches top curated news articles from Google News category section feeds."""
        category_lower = category.lower().strip()
        topic_urls = {
            "all": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "top": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "tech": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
            "technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
            "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
            "finance": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
            "science": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-US&gl=US&ceid=US:en",
            "ai": "https://news.google.com/rss/search?q=Artificial+Intelligence+OR+OpenAI+OR+LLM+OR+Nvidia&hl=en-US&gl=US&ceid=US:en",
        }
        url = topic_urls.get(category_lower, f"https://news.google.com/rss/search?q={urllib.parse.quote(category)}&hl=en-US&gl=US&ceid=US:en")
        results = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                raw_title = getattr(entry, "title", "").strip()
                if not raw_title:
                    continue

                source_name = getattr(entry, "source", {}).get("title", "")
                if not source_name and " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()
                elif source_name and raw_title.endswith(f" - {source_name}"):
                    title = raw_title[:-len(f" - {source_name}")].strip()
                else:
                    title = raw_title
                    source_name = source_name or "Verified News Source"

                link = getattr(entry, "link", "")
                pub_date = getattr(entry, "published", datetime.now(timezone.utc).isoformat())

                raw_summary = getattr(entry, "summary", "") or title
                clean_text = re.sub(r"<[^>]+>", " ", raw_summary)
                clean_text = html.unescape(clean_text)
                clean_text = re.sub(r"\s+", " ", clean_text).strip()

                if len(clean_text) < 50:
                    clean_text = f"{title}. Reported by {source_name}."

                results.append(
                    RawArticle(
                        title=title,
                        url=link,
                        source_name=source_name,
                        author=source_name,
                        published_at=pub_date,
                        content=clean_text,
                        category=category.title()
                    )
                )
        except Exception as e:
            logger.warning(f"Google News topic feed failed for '{category}': {e}")

        return results

    def search(self, query: str, limit: int = 10, mode: Optional[str] = None) -> NewsSearchResponse:
        """
        Main entrypoint: Retrieves news articles based on configured mode and query.
        Guarantees results via Google News, NewsAPI, and graceful fallback.
        """
        target_mode = mode or settings.APP_MODE

        # 1. If explicitly in demo mode, use offline curated fixtures
        if target_mode == "demo":
            articles = self.fetch_offline_sample(query, limit=limit)
            enriched = self.enrich_articles(articles)
            return NewsSearchResponse(
                query=query,
                mode_used="offline-demo",
                total_found=len(enriched),
                articles=enriched
            )

        # 2. Live mode: Multi-Source Engine (Google News RSS + NewsAPI + Curated RSS)
        articles = []
        mode_used = "live-stream"

        # Tier A: Google News Search (unlimited, covers EVERY query worldwide)
        try:
            google_articles = self.fetch_from_google_news(query, limit=max(limit, 10))
            if google_articles:
                articles.extend(google_articles)
                mode_used = "live-search"
        except Exception as e:
            logger.warning(f"Google News search failed: {e}")

        # Tier B: NewsAPI (if configured)
        if settings.NEWS_API_KEY:
            try:
                api_articles = self.fetch_from_news_api(query, limit=limit)
                if api_articles:
                    articles.extend(api_articles)
                    mode_used = "live-api"
            except Exception as e:
                logger.warning(f"NewsAPI search failed: {e}")

        # Tier C: Curated Open RSS Feeds (supplement if few articles)
        if len(articles) < limit:
            try:
                rss_articles = self.fetch_from_rss(query, limit=limit)
                if rss_articles:
                    articles.extend(rss_articles)
            except Exception as e:
                logger.warning(f"Live RSS fetch failed: {e}")

        # Deduplicate by title
        seen_titles = set()
        unique = []
        for art in articles:
            t = art.title.strip().lower()[:80]
            if t not in seen_titles:
                seen_titles.add(t)
                unique.append(art)

        # Tier D: Graceful Fallback to offline fixtures only if completely empty (e.g. no internet)
        if not unique:
            unique = self.fetch_offline_sample(query, limit=limit)
            mode_used = "offline-demo (fallback)"

        enriched = self.enrich_articles(unique[:limit])
        return NewsSearchResponse(
            query=query,
            mode_used=mode_used,
            total_found=len(enriched),
            articles=enriched
        )

    def fetch_top_headlines(self, category: str = "all", limit: int = 12) -> List[RawArticle]:
        """Fetches latest breaking news across categories (all, tech, business, ai, science).
        Uses Google News section feeds + NewsAPI top-headlines + Curated RSS.
        Always guarantees rich, real-time stories.
        """
        category_lower = category.lower().strip()
        articles = []

        if settings.APP_MODE == "live":
            # Strategy 1: Google News Section Topics (Instant, up to 70 real-time verified stories)
            try:
                g_articles = self.fetch_google_news_topic(category_lower, limit=limit)
                if g_articles:
                    articles.extend(g_articles)
            except Exception as e:
                logger.warning(f"Google News headlines failed: {e}")

            # Strategy 2: NewsAPI top-headlines (if key configured)
            if settings.NEWS_API_KEY and len(articles) < limit:
                cat_info = self.CATEGORY_MAP.get(category_lower, (None, "technology news"))
                headlines_category, everything_query = cat_info
                try:
                    if headlines_category:
                        url = "https://newsapi.org/v2/top-headlines"
                        params = {
                            "country": "us",
                            "category": headlines_category,
                            "pageSize": limit,
                            "apiKey": settings.NEWS_API_KEY
                        }
                        resp = requests.get(url, params=params, timeout=6)
                        if resp.status_code == 200:
                            for item in resp.json().get("articles", []):
                                if item.get("title") and item.get("title") != "[Removed]":
                                    articles.append(RawArticle(
                                        title=item["title"],
                                        url=item.get("url", ""),
                                        source_name=item.get("source", {}).get("name", "NewsAPI"),
                                        author=item.get("author") or "Staff",
                                        published_at=item.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                                        content=item.get("description") or item.get("content") or "",
                                        image_url=item.get("urlToImage"),
                                        category=category.title()
                                    ))
                except Exception as e:
                    logger.warning(f"Top-headlines NewsAPI fetch failed: {e}")

            # Strategy 3: Open Curated RSS Feeds
            if len(articles) < limit:
                try:
                    rss_articles = self.fetch_from_rss(category_lower, limit=limit)
                    articles.extend(rss_articles)
                except Exception as e:
                    logger.warning(f"RSS feed fallback failed: {e}")

        # Strategy 4: Offline sample fallback if still empty
        if len(articles) < 4:
            offline = self.fetch_offline_sample(category_lower, limit=limit)
            articles.extend(offline)

        # Deduplicate by title
        seen_titles = set()
        unique = []
        for art in articles:
            t = art.title.strip().lower()[:80]
            if t not in seen_titles:
                seen_titles.add(t)
                unique.append(art)

        return self.enrich_articles(unique[:limit])

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
        """Fetches live items from curated RSS feeds.
        Strips boolean operators and short words before matching.
        Falls back to returning all entries if no tokens match.
        """
        results = []
        # Remove boolean operators and short words; keep meaningful 4+ char keywords
        stop_words = {"or", "and", "the", "for", "with", "from", "news"}
        raw_tokens = [q.lower().strip() for q in query.replace(" OR ", " ").replace(" AND ", " ").split()]
        query_tokens = [t for t in raw_tokens if len(t) >= 4 and t not in stop_words]

        per_feed_limit = max(4, limit // len(self.RSS_FEEDS) + 2)

        for feed in self.RSS_FEEDS:
            feed_results = []
            try:
                parsed = feedparser.parse(feed["url"])
                for entry in parsed.entries[:20]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description", "")
                    content_text = f"{title} {summary}".lower()

                    # Include if any query token matches, OR if no meaningful tokens (general query)
                    if not query_tokens or any(token in content_text for token in query_tokens):
                        feed_results.append(
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
                        if len(feed_results) >= per_feed_limit:
                            break
                results.extend(feed_results)
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

