import os
import json
import logging
import requests
import feedparser
import urllib.parse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from backend.app.config import settings
from backend.app.schemas.news import RawArticle, NewsSearchResponse, EventClusterDTO

logger = logging.getLogger(__name__)


def _parse_date(date_str) -> Optional[datetime]:
    """Parse various date formats into timezone-aware datetime."""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str if date_str.tzinfo else date_str.replace(tzinfo=timezone.utc)
    try:
        # ISO 8601 (NewsAPI format)
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        # RFC 2822 (RSS format)
        dt = parsedate_to_datetime(str(date_str))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return None


class NewsFetcher:
    """
    Ultra-fresh Hybrid News Aggregation Engine.
    Priority order:
      1. Google News RSS (topic/query-specific, always < 6 hours old)
      2. NewsAPI /everything (sortBy=publishedAt, from=last 24h)
      3. NewsAPI /top-headlines (standard categories)
      4. Curated RSS feeds (BBC, TechCrunch, Reuters, etc.)
      5. Offline sample snapshot (fallback, never empty)
    """

    # ── Standard curated RSS feeds (for category homepages) ──────────────────
    RSS_FEEDS = [
        {"name": "BBC Tech",         "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",              "category": "Technology"},
        {"name": "TechCrunch",       "url": "https://techcrunch.com/feed/",                                 "category": "Technology"},
        {"name": "Ars Technica",     "url": "https://feeds.arstechnica.com/arstechnica/index",              "category": "Technology"},
        {"name": "MIT Tech Review",  "url": "https://www.technologyreview.com/feed/",                       "category": "AI"},
        {"name": "VentureBeat AI",   "url": "https://venturebeat.com/category/ai/feed/",                    "category": "AI"},
        {"name": "Reuters Tech",     "url": "https://feeds.reuters.com/reuters/technologyNews",             "category": "Technology"},
        {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews",               "category": "Business"},
        {"name": "Reuters World",    "url": "https://feeds.reuters.com/Reuters/worldNews",                  "category": "World"},
        {"name": "BBC Science",      "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "category": "Science"},
        {"name": "Wired",            "url": "https://www.wired.com/feed/rss",                               "category": "Technology"},
        {"name": "The Verge",        "url": "https://www.theverge.com/rss/index.xml",                       "category": "Technology"},
        {"name": "NDTV India",       "url": "https://feeds.feedburner.com/ndtvnews-top-stories",            "category": "India"},
        {"name": "Times of India",   "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",   "category": "India"},
        {"name": "India Today",      "url": "https://www.indiatoday.in/rss/1206578",                        "category": "India"},
        {"name": "Economic Times",   "url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",     "category": "Business"},
        {"name": "BBC World",        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",                   "category": "World"},
        {"name": "Al Jazeera",       "url": "https://www.aljazeera.com/xml/rss/all.xml",                    "category": "World"},
        {"name": "Space.com",        "url": "https://www.space.com/feeds/all",                              "category": "Science"},
    ]

    # ── Category routing map ─────────────────────────────────────────────────
    CATEGORY_MAP = {
        "all":        (None,         "world news technology business"),
        "tech":       ("technology", "technology innovation software hardware"),
        "technology": ("technology", "technology innovation software hardware"),
        "business":   ("business",   "business economy markets finance"),
        "finance":    ("business",   "business economy markets finance"),
        "ai":         (None,         "artificial intelligence machine learning LLM OpenAI Gemini"),
        "science":    ("science",    "science space research discovery"),
        "india":      (None,         "India news politics economy"),
        "world":      (None,         "world news international politics"),
    }

    def __init__(self):
        self.sample_data_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../data/sample_news.json")
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def enrich_articles(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Run intelligence extractor on all raw articles."""
        from backend.app.services.text_processor import text_processor
        for art in articles:
            if not art.intelligence:
                art.intelligence = text_processor.extract_intelligence(art.title, art.content)
        return articles

    def search(self, query: str, limit: int = 10, mode: Optional[str] = None) -> NewsSearchResponse:
        """
        Global Multi-Source Search:
        Coordinates Geo-Intelligence, Multi-Provider Fetching (Google News geo-targeted,
        GDELT worldwide, NewsAPI fresh, Regional RSS), and Event Clustering.
        """
        target_mode = mode or settings.APP_MODE

        if target_mode == "demo":
            articles = self.fetch_offline_sample(query, limit=limit)
            enriched = self.enrich_articles(articles)
            return NewsSearchResponse(
                query=query, mode_used="offline-demo",
                total_found=len(enriched), articles=enriched
            )

        # ── Primary Engine: GlobalNewsEngine ──────────────────────────────
        try:
            from backend.app.services.global_news_engine import global_news_engine
            global_res = global_news_engine.search(query=query, limit=limit)
            if global_res.articles:
                events_dto = []
                for ev in global_res.events:
                    events_dto.append(EventClusterDTO(
                        event_id=ev.event_id,
                        headline=ev.headline,
                        source_count=ev.source_count,
                        sources=ev.sources,
                        is_developing=ev.is_developing,
                        earliest_date=ev.earliest_date,
                        latest_date=ev.latest_date,
                        coverage_score=ev.coverage_score
                    ))
                enriched = self.enrich_articles(global_res.articles)
                return NewsSearchResponse(
                    query=query,
                    mode_used=global_res.mode_used,
                    total_found=len(enriched),
                    articles=enriched,
                    coverage=global_res.coverage,
                    events=events_dto
                )
        except Exception as e:
            logger.warning(f"GlobalNewsEngine failed: {e}. Falling back to standard pipeline.")

        articles: List[RawArticle] = []
        mode_used = "live-google-rss"

        # ── Tier 1: Google News RSS (freshest — usually < 6 hrs) ────────────
        try:
            gnews = self._fetch_google_news_rss(query, limit=limit * 2)
            articles.extend(gnews)
            logger.info(f"Google News RSS: {len(gnews)} articles for '{query}'")
        except Exception as e:
            logger.warning(f"Google News RSS failed: {e}")

        # ── Tier 2: NewsAPI /everything sortBy=publishedAt (last 24h) ────────
        if len(articles) < limit and settings.NEWS_API_KEY:
            try:
                na = self._newsapi_everything_fresh(query, limit=limit)
                articles.extend(na)
                if na:
                    mode_used = "live-newsapi+google"
                logger.info(f"NewsAPI fresh: {len(na)} articles for '{query}'")
            except Exception as e:
                logger.warning(f"NewsAPI everything failed: {e}")

        # ── Tier 3: Curated RSS as fallback ──────────────────────────────────
        if len(articles) < 4:
            try:
                rss = self.fetch_from_rss(query, limit=limit)
                articles.extend(rss)
                mode_used = "live-rss"
            except Exception as e:
                logger.warning(f"RSS fallback failed: {e}")

        # ── Tier 4: Offline snapshot (never empty) ───────────────────────────
        if not articles:
            articles = self.fetch_offline_sample(query, limit=limit)
            mode_used = "offline-demo (fallback)"

        # Deduplicate + sort by date (newest first)
        unique = self._deduplicate(articles)
        unique = self._sort_by_date(unique)

        enriched = self.enrich_articles(unique[:limit])
        return NewsSearchResponse(
            query=query, mode_used=mode_used,
            total_found=len(enriched), articles=enriched
        )


    def fetch_top_headlines(self, category: str = "all", limit: int = 12) -> List[RawArticle]:
        """
        Fetch breaking headlines for category. Uses Google News topic RSS,
        NewsAPI top-headlines, curated RSS — always sorted newest first.
        """
        category_lower = category.lower().strip()
        cat_info = self.CATEGORY_MAP.get(category_lower, (None, "world news technology"))
        headlines_category, everything_query = cat_info
        articles: List[RawArticle] = []

        # ── Google News topic RSS ─────────────────────────────────────────────
        try:
            gnews = self._fetch_google_news_topic(category_lower, limit=limit)
            articles.extend(gnews)
            logger.info(f"Google News topic RSS ({category}): {len(gnews)} articles")
        except Exception as e:
            logger.warning(f"Google News topic RSS failed: {e}")

        # ── NewsAPI top-headlines ─────────────────────────────────────────────
        if settings.NEWS_API_KEY and settings.APP_MODE == "live" and len(articles) < limit:
            try:
                if headlines_category:
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {
                        "country": "us",
                        "category": headlines_category,
                        "pageSize": min(limit, 20),
                        "apiKey": settings.NEWS_API_KEY
                    }
                    resp = requests.get(url, params=params, timeout=8)
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
                logger.warning(f"Top-headlines fetch failed: {e}")

        # ── NewsAPI /everything sortBy=publishedAt to fill gaps ──────────────
        if settings.NEWS_API_KEY and settings.APP_MODE == "live" and len(articles) < limit:
            try:
                fresh = self._newsapi_everything_fresh(everything_query, limit=limit - len(articles))
                articles.extend(fresh)
            except Exception as e:
                logger.warning(f"NewsAPI everything (headlines fill) failed: {e}")

        # ── Curated RSS as fallback ───────────────────────────────────────────
        if len(articles) < 8:
            try:
                rss = self.fetch_from_rss(everything_query, limit=limit)
                articles.extend(rss)
            except Exception as e:
                logger.warning(f"RSS supplement failed: {e}")

        # ── Offline fallback ─────────────────────────────────────────────────
        if len(articles) < 4:
            offline = self.fetch_offline_sample(everything_query, limit=limit)
            articles.extend(offline)

        unique = self._deduplicate(articles)
        unique = self._sort_by_date(unique)
        return self.enrich_articles(unique[:limit])

    # ─────────────────────────────────────────────────────────────────────────
    # GOOGLE NEWS RSS  (key innovation — always ultra-fresh)
    # ─────────────────────────────────────────────────────────────────────────

    def _fetch_google_news_rss(self, query: str, limit: int = 20) -> List[RawArticle]:
        """
        Fetch from Google News search RSS — articles are typically < 6 hours old.
        URL: https://news.google.com/rss/search?q=<query>&hl=en&gl=US&ceid=US:en
        """
        encoded_q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en&gl=US&ceid=US:en"
        return self._parse_google_rss(url, limit=limit, category="General")

    def _fetch_google_news_topic(self, category: str, limit: int = 12) -> List[RawArticle]:
        """
        Fetch Google News topic/section RSS for category homepages.
        These are updated every few minutes.
        """
        # Google News topic IDs
        topic_urls = {
            "all":        "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
            "tech":       "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en",
            "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en",
            "business":   "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en",
            "science":    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREdxTlhZU0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en",
            "ai":         None,  # Use search RSS for AI
            "india":      "https://news.google.com/rss/search?q=India+news&hl=en-IN&gl=IN&ceid=IN:en",
            "world":      "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en",
        }

        # For AI category, use search RSS
        if category == "ai":
            return self._fetch_google_news_rss("artificial intelligence machine learning LLM", limit=limit)

        url = topic_urls.get(category)
        if not url:
            # Fallback to search RSS
            query = self.CATEGORY_MAP.get(category, (None, "latest news"))[1]
            return self._fetch_google_news_rss(query, limit=limit)

        cat_name = category.title()
        return self._parse_google_rss(url, limit=limit, category=cat_name)

    def _parse_google_rss(self, url: str, limit: int = 20, category: str = "General") -> List[RawArticle]:
        """Parse a Google News RSS feed URL into RawArticle list."""
        results = []
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:limit * 2]:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                # Google News RSS titles sometimes include " - Source Name" at end
                source_name = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()

                link = entry.get("link", "")
                summary = entry.get("summary", "") or entry.get("description", "")

                # Parse publish date
                pub_date = entry.get("published", "")
                dt = _parse_date(pub_date)
                pub_iso = dt.isoformat() if dt else datetime.now(timezone.utc).isoformat()

                results.append(RawArticle(
                    title=title,
                    url=link,
                    source_name=source_name,
                    author="Wire",
                    published_at=pub_iso,
                    content=summary,
                    category=category,
                    image_url=None
                ))

                if len(results) >= limit:
                    break

        except Exception as e:
            logger.warning(f"Google RSS parse error ({url[:60]}): {e}")

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # NEWSAPI — sortBy=publishedAt, from=last 48h
    # ─────────────────────────────────────────────────────────────────────────

    def _newsapi_everything_fresh(self, query: str, limit: int = 10) -> List[RawArticle]:
        """
        NewsAPI /everything with sortBy=publishedAt and from=48h ago.
        This ensures results are always recent, not relevancy-ranked old articles.
        """
        if not settings.NEWS_API_KEY:
            return []

        from_dt = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "language": "en",
            "from": from_dt,
            "pageSize": min(30, max(limit * 2, 10)),
            "apiKey": settings.NEWS_API_KEY,
        }

        try:
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code != 200:
                logger.error(f"NewsAPI /everything returned {resp.status_code}")
                return []
            data = resp.json()
        except Exception as e:
            logger.error(f"NewsAPI /everything request failed: {e}")
            return []

        articles = []
        for item in data.get("articles", []):
            if not item.get("title") or item.get("title") == "[Removed]":
                continue
            articles.append(RawArticle(
                title=item["title"],
                url=item.get("url", ""),
                source_name=item.get("source", {}).get("name", "NewsAPI"),
                author=item.get("author") or "Staff",
                published_at=item.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                content=item.get("description") or item.get("content") or "",
                image_url=item.get("urlToImage"),
                category="General"
            ))
        return articles

    # ─────────────────────────────────────────────────────────────────────────
    # LEGACY: curated RSS fetch (used as fallback)
    # ─────────────────────────────────────────────────────────────────────────

    def fetch_from_rss(self, query: str, limit: int = 10) -> List[RawArticle]:
        """Fetch from curated RSS feeds, filter by query tokens."""
        results = []
        stop_words = {"or", "and", "the", "for", "with", "from", "news", "latest"}
        raw_tokens = [q.lower().strip() for q in query.replace(" OR ", " ").replace(" AND ", " ").split()]
        query_tokens = [t for t in raw_tokens if len(t) >= 4 and t not in stop_words]

        per_feed_limit = max(3, limit // len(self.RSS_FEEDS) + 2)

        for feed in self.RSS_FEEDS:
            feed_results = []
            try:
                parsed = feedparser.parse(feed["url"])
                for entry in parsed.entries[:20]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description", "")
                    content_text = f"{title} {summary}".lower()

                    if not query_tokens or any(token in content_text for token in query_tokens):
                        pub_date = entry.get("published", "")
                        dt = _parse_date(pub_date)
                        pub_iso = dt.isoformat() if dt else datetime.now(timezone.utc).isoformat()

                        feed_results.append(RawArticle(
                            title=title,
                            url=entry.get("link", ""),
                            source_name=feed["name"],
                            author=entry.get("author", feed["name"]),
                            published_at=pub_iso,
                            content=summary,
                            category=feed["category"]
                        ))
                        if len(feed_results) >= per_feed_limit:
                            break
                results.extend(feed_results)
            except Exception as e:
                logger.warning(f"RSS feed {feed['name']} failed: {e}")
                continue

            if len(results) >= limit:
                break

        return results[:limit]

    # ─────────────────────────────────────────────────────────────────────────
    # OFFLINE SAMPLE FALLBACK
    # ─────────────────────────────────────────────────────────────────────────

    def fetch_offline_sample(self, query: str, limit: int = 10) -> List[RawArticle]:
        """Load from local sample JSON as last resort."""
        if not os.path.exists(self.sample_data_path):
            return []
        try:
            with open(self.sample_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            query_tokens = [q.lower().strip() for q in query.split() if len(q) > 2]
            results = []
            for item in data:
                text = f"{item.get('title', '')} {item.get('content', '')} {item.get('category', '')}".lower()
                if not query_tokens or any(t in text for t in query_tokens):
                    results.append(RawArticle(
                        title=item["title"], url=item["url"],
                        source_name=item.get("source_name", "Archive"),
                        author=item.get("author", "Staff Writer"),
                        published_at=item.get("published_at"),
                        content=item["content"],
                        category=item.get("category", "General")
                    ))
            if not results and data:
                results = [
                    RawArticle(
                        title=item["title"], url=item["url"],
                        source_name=item.get("source_name", "Archive"),
                        author=item.get("author", "Staff Writer"),
                        published_at=item.get("published_at"),
                        content=item["content"],
                        category=item.get("category", "General")
                    )
                    for item in data[:limit]
                ]
            return results[:limit]
        except Exception as e:
            logger.error(f"Offline sample load failed: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _deduplicate(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Remove duplicates by normalized title prefix."""
        seen = set()
        unique = []
        for art in articles:
            key = art.title.strip().lower()[:80]
            if key not in seen and key:
                seen.add(key)
                unique.append(art)
        return unique

    def _sort_by_date(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Sort newest first. Articles with unparseable dates go to end."""
        def sort_key(a):
            dt = _parse_date(a.published_at)
            return dt if dt else datetime.min.replace(tzinfo=timezone.utc)
        return sorted(articles, key=sort_key, reverse=True)

    # Keep legacy method name for backward compatibility
    def fetch_from_news_api(self, query: str, limit: int = 10) -> List[RawArticle]:
        return self._newsapi_everything_fresh(query, limit=limit)


# Singleton
news_fetcher = NewsFetcher()
