"""
global_news_engine.py — Global News Intelligence Orchestrator

The master search pipeline that coordinates:
  1. Geo Intelligence (detect country/language from query)
  2. Query Expansion (multilingual + topic variants)
  3. Multi-Provider Fetching (Google News, GDELT, NewsAPI, RSS)
  4. Event Clustering (group related articles)
  5. Coverage Tracking (no geographic blind spots)
  6. Relevance + Freshness Ranking
"""

from __future__ import annotations
import logging
import urllib.parse
import feedparser
import requests
import socket
socket.setdefaulttimeout(5.0)
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from email.utils import parsedate_to_datetime

from backend.app.schemas.news import RawArticle
from backend.app.services.geo_intelligence import geo_engine, GeoContext
from backend.app.services.event_clustering import event_clusterer, NewsEvent
from backend.app.config import settings

logger = logging.getLogger(__name__)


def _parse_date(date_str) -> Optional[datetime]:
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str if date_str.tzinfo else date_str.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(str(date_str))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return None


@dataclass
class GlobalSearchResult:
    """Full result of the global news search pipeline."""
    query: str
    geo_context: Optional[GeoContext]
    articles: List[RawArticle]
    events: List[NewsEvent]
    coverage: Dict[str, object]   # Coverage report
    mode_used: str
    total_found: int
    search_time_ms: int = 0


class GlobalNewsEngine:
    """
    The master orchestrator for worldwide news retrieval.
    Searches across Google News (geo-targeted), GDELT, NewsAPI,
    and curated RSS feeds with automatic fallback.
    """

    # ── Regional RSS feeds organized by geography ──────────────────────────
    REGIONAL_RSS: Dict[str, List[Dict]] = {
        "South Asia": [
            {"name": "NDTV",         "url": "https://feeds.feedburner.com/ndtvnews-top-stories",           "category": "India"},
            {"name": "Times of India","url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "category": "India"},
            {"name": "The Hindu",    "url": "https://www.thehindu.com/feeder/default.rss",                 "category": "India"},
            {"name": "Dawn (PK)",    "url": "https://www.dawn.com/feeds/home",                             "category": "Pakistan"},
            {"name": "Daily Star BD","url": "https://www.thedailystar.net/feed/rss.xml",                   "category": "Bangladesh"},
        ],
        "East Asia": [
            {"name": "Japan Times",  "url": "https://www.japantimes.co.jp/feed/",                         "category": "Japan"},
            {"name": "Korea Herald", "url": "https://www.koreaherald.com/rss/020000000000.xml",            "category": "South Korea"},
            {"name": "South China Morning Post", "url": "https://www.scmp.com/rss/91/feed",               "category": "East Asia"},
            {"name": "Channel NewsAsia","url": "https://www.channelnewsasia.com/rss",                      "category": "Southeast Asia"},
        ],
        "Middle East": [
            {"name": "Al Jazeera",   "url": "https://www.aljazeera.com/xml/rss/all.xml",                  "category": "Middle East"},
            {"name": "Arab News",    "url": "https://www.arabnews.com/rss.xml",                            "category": "Middle East"},
            {"name": "Gulf News",    "url": "https://gulfnews.com/rss",                                    "category": "Gulf"},
            {"name": "Jerusalem Post","url": "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx",          "category": "Israel"},
        ],
        "Europe": [
            {"name": "Euronews",     "url": "https://feeds.feedburner.com/euronews/en/home/",              "category": "Europe"},
            {"name": "The Local",    "url": "https://www.thelocal.com/feeds/",                             "category": "Europe"},
            {"name": "DW English",   "url": "https://rss.dw.com/rdf/rss-en-all",                          "category": "Europe"},
            {"name": "France 24",    "url": "https://www.france24.com/en/rss",                             "category": "France"},
            {"name": "EUobserver",   "url": "https://euobserver.com/news/rss.xml",                        "category": "Europe"},
        ],
        "Africa": [
            {"name": "AllAfrica",    "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "category": "Africa"},
            {"name": "The East African","url": "https://www.theeastafrican.co.ke/rss",                    "category": "East Africa"},
            {"name": "Business Day (ZA)","url": "https://businessday.ng/feed/",                           "category": "Nigeria"},
            {"name": "News24 Africa","url": "https://feeds.news24.com/articles/News24/TopStories/rss",    "category": "South Africa"},
        ],
        "South America": [
            {"name": "MercoPress",   "url": "https://en.mercopress.com/rss",                              "category": "South America"},
            {"name": "Buenos Aires Times","url": "https://batimes.com.ar/rss.xml",                        "category": "Argentina"},
        ],
        "Oceania": [
            {"name": "ABC Australia","url": "https://www.abc.net.au/news/feed/45910/rss.xml",             "category": "Australia"},
            {"name": "NZ Herald",    "url": "https://www.nzherald.co.nz/arc/outboundfeeds/rss/",          "category": "New Zealand"},
            {"name": "RNZ Pacific",  "url": "https://www.rnz.co.nz/rss/pacific.xml",                     "category": "Pacific"},
        ],
        "Global": [
            {"name": "Reuters World","url": "https://feeds.reuters.com/Reuters/worldNews",                 "category": "World"},
            {"name": "BBC World",    "url": "http://feeds.bbci.co.uk/news/world/rss.xml",                  "category": "World"},
            {"name": "AP News",      "url": "https://feeds.apnews.com/rss/apf-topnews",                   "category": "World"},
            {"name": "AFP",          "url": "https://www.afp.com/en/rss",                                  "category": "World"},
        ],
    }

    def search(self, query: str, limit: int = 20) -> GlobalSearchResult:
        """
        Main global search pipeline.
        Returns richly structured results with event clustering.
        """
        import time
        start = time.time()

        # ── Step 1: Geo Intelligence ──────────────────────────────────────────
        ctx = geo_engine.analyze(query)
        logger.info(f"Geo: {ctx.coverage_note or 'No geo detected'} | Queries: {ctx.expanded_queries}")

        articles: List[RawArticle] = []
        providers_used = []
        providers_failed = []

        # ── Step 2: Google News RSS (geo-targeted) ────────────────────────────
        gnews_urls = geo_engine.get_google_news_urls(ctx, query)
        for url in gnews_urls:
            try:
                arts = self._fetch_google_rss(url, limit=limit)
                if arts:
                    articles.extend(arts)
                    providers_used.append("Google News RSS")
                    break  # One successful URL is enough
            except Exception as e:
                logger.warning(f"Google News RSS failed ({url[:50]}...): {e}")
                providers_failed.append("Google News RSS")

        # ── Step 3: GDELT API (free, global, no key needed) ───────────────────
        if len(articles) < 3:
            try:
                gdelt_arts = self._fetch_gdelt(query, limit=limit)
                if gdelt_arts:
                    articles.extend(gdelt_arts)
                    providers_used.append("GDELT")
            except Exception as e:
                logger.warning(f"GDELT failed: {e}")
                providers_failed.append("GDELT")

        # ── Step 4: NewsAPI (fresh, sortBy=publishedAt) ───────────────────────
        if settings.NEWS_API_KEY and len(articles) < 4:
            for q in ctx.expanded_queries[:2]:
                try:
                    na_arts = self._fetch_newsapi_fresh(q, limit=limit // 2)
                    if na_arts:
                        articles.extend(na_arts)
                        providers_used.append("NewsAPI")
                        break
                except Exception as e:
                    logger.warning(f"NewsAPI failed: {e}")
                    providers_failed.append("NewsAPI")

        # ── Step 5: Regional RSS (based on detected region) ───────────────────
        if len(articles) < 8:
            region_feeds = self._get_regional_feeds(ctx)
            rss_arts = self._fetch_feeds(region_feeds, query, limit=12)
            if rss_arts:
                articles.extend(rss_arts)
                providers_used.append("Regional RSS")

        # ── Step 6: Expanded query variants (Google News) ─────────────────────
        if len(articles) < 6 and len(ctx.expanded_queries) > 1:
            for eq in ctx.expanded_queries[1:3]:
                try:
                    q_enc = urllib.parse.quote(eq)
                    gl, hl = ctx.gl, ctx.hl
                    url = f"https://news.google.com/rss/search?q={q_enc}&hl={hl}&gl={gl}&ceid={gl}:{hl[:2]}"
                    extra = self._fetch_google_rss(url, limit=8)
                    articles.extend(extra)
                    if extra:
                        providers_used.append(f"Google News (expanded: {eq[:30]})")
                except Exception as e:
                    logger.warning(f"Expanded query RSS failed: {e}")

        # ── Step 7: Deduplicate + Sort by date ────────────────────────────────
        unique = self._deduplicate(articles)
        unique = self._sort_by_date(unique)

        # ── Step 8: Event Clustering ──────────────────────────────────────────
        events = []
        try:
            events = event_clusterer.cluster(unique[:limit * 2])
        except Exception as e:
            logger.warning(f"Event clustering failed: {e}")

        # ── Step 9: Enrich articles ────────────────────────────────────────────
        try:
            from backend.app.services.text_processor import text_processor
            for art in unique[:limit]:
                if not art.intelligence:
                    art.intelligence = text_processor.extract_intelligence(art.title, art.content)
        except Exception as e:
            logger.warning(f"Enrichment failed: {e}")

        # ── Step 10: Build Coverage Report ────────────────────────────────────
        elapsed = int((time.time() - start) * 1000)
        coverage = self._build_coverage_report(ctx, unique, providers_used, providers_failed)

        mode = "+".join(list(dict.fromkeys(providers_used))) if providers_used else "offline"

        return GlobalSearchResult(
            query=query,
            geo_context=ctx,
            articles=unique[:limit],
            events=events[:limit],
            coverage=coverage,
            mode_used=mode,
            total_found=len(unique),
            search_time_ms=elapsed,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PROVIDER IMPLEMENTATIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _fetch_google_rss(self, url: str, limit: int = 20) -> List[RawArticle]:
        """Parse a Google News RSS feed URL."""
        results = []
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:limit * 2]:
            title = entry.get("title", "").strip()
            if not title:
                continue
            source_name = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                source_name = parts[1].strip()
            pub_date = entry.get("published", "")
            dt = _parse_date(pub_date)
            pub_iso = dt.isoformat() if dt else datetime.now(timezone.utc).isoformat()
            summary = entry.get("summary", "") or entry.get("description", "")
            results.append(RawArticle(
                title=title,
                url=entry.get("link", ""),
                source_name=source_name,
                author="Wire",
                published_at=pub_iso,
                content=summary,
                category="General",
                image_url=None,
            ))
            if len(results) >= limit:
                break
        return results

    def _fetch_gdelt(self, query: str, limit: int = 15) -> List[RawArticle]:
        """
        GDELT 2.0 Doc API — completely free, global coverage, no API key.
        Covers 65+ languages from 100+ countries.
        """
        q_enc = urllib.parse.quote(query)
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={q_enc}&mode=artlist&maxrecords={min(limit, 25)}"
            f"&format=json&sort=DateDesc&timespan=24h"
        )
        try:
            resp = requests.get(url, timeout=3.5, headers={"User-Agent": "NexusIntelligence/1.0"})
            if resp.status_code != 200:
                return []
            data = resp.json()
        except Exception:
            return []
        articles = []
        for item in (data.get("articles") or []):
            title = item.get("title", "").strip()
            if not title:
                continue
            # GDELT seendate format: YYYYMMDDTHHMMSSZ
            raw_date = item.get("seendate", "")
            try:
                dt = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                pub_iso = dt.isoformat()
            except Exception:
                pub_iso = datetime.now(timezone.utc).isoformat()

            articles.append(RawArticle(
                title=title,
                url=item.get("url", ""),
                source_name=item.get("domain", "GDELT Source"),
                author=item.get("author", "Wire"),
                published_at=pub_iso,
                content=item.get("seendate", "") + " " + title,
                category=item.get("language", "General"),
                image_url=None,
            ))
        return articles

    def _fetch_newsapi_fresh(self, query: str, limit: int = 10) -> List[RawArticle]:
        """NewsAPI /everything sorted by publishedAt, last 48 hours."""
        if not settings.NEWS_API_KEY:
            return []
        from_dt = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "sortBy": "publishedAt",
                "language": "en",
                "from": from_dt,
                "pageSize": min(30, max(limit * 2, 10)),
                "apiKey": settings.NEWS_API_KEY,
            },
            timeout=8,
        )
        if resp.status_code != 200:
            return []
        articles = []
        for item in resp.json().get("articles", []):
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
                category="General",
            ))
        return articles

    def _fetch_feeds(self, feeds: List[Dict], query: str, limit: int = 12) -> List[RawArticle]:
        """Fetch from a list of RSS feed dicts, filtering by query tokens."""
        stop = {"or","and","the","for","with","from","news","latest","in","at","of"}
        raw_tokens = [q.lower() for q in query.replace(" OR "," ").split()]
        tokens = [t for t in raw_tokens if len(t) >= 3 and t not in stop]

        results = []
        for feed in feeds:
            try:
                parsed = feedparser.parse(feed["url"])
                for entry in parsed.entries[:15]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or ""
                    text = f"{title} {summary}".lower()
                    if not tokens or any(t in text for t in tokens):
                        pub = entry.get("published", "")
                        dt = _parse_date(pub)
                        results.append(RawArticle(
                            title=title,
                            url=entry.get("link", ""),
                            source_name=feed["name"],
                            author=entry.get("author", feed["name"]),
                            published_at=dt.isoformat() if dt else datetime.now(timezone.utc).isoformat(),
                            content=summary,
                            category=feed.get("category", "General"),
                        ))
                        if len(results) >= limit:
                            return results
            except Exception as e:
                logger.warning(f"RSS {feed['name']} failed: {e}")
        return results

    def _get_regional_feeds(self, ctx: GeoContext) -> List[Dict]:
        """Return RSS feeds relevant to the detected region."""
        feeds = list(self.REGIONAL_RSS.get("Global", []))
        if ctx.detected_region:
            region = ctx.detected_region
            # Match broad regions
            for key, region_feeds in self.REGIONAL_RSS.items():
                if key.lower() in region.lower() or region.lower() in key.lower():
                    feeds.extend(region_feeds)
        return feeds[:10]  # Max 10 feeds to keep it fast

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _deduplicate(self, articles: List[RawArticle]) -> List[RawArticle]:
        seen = set()
        out = []
        for a in articles:
            key = a.title.strip().lower()[:90]
            if key and key not in seen:
                seen.add(key)
                out.append(a)
        return out

    def _sort_by_date(self, articles: List[RawArticle]) -> List[RawArticle]:
        def key(a):
            dt = _parse_date(a.published_at)
            return dt or datetime.min.replace(tzinfo=timezone.utc)
        return sorted(articles, key=key, reverse=True)

    def _build_coverage_report(
        self,
        ctx: GeoContext,
        articles: List[RawArticle],
        providers_used: List[str],
        providers_failed: List[str],
    ) -> Dict:
        unique_sources = list({a.source_name for a in articles})
        return {
            "query": ctx.query,
            "detected_country": ctx.detected_country,
            "detected_region": ctx.detected_region,
            "languages_searched": ctx.languages,
            "google_locale": f"{ctx.gl}/{ctx.hl}",
            "expanded_queries": ctx.expanded_queries,
            "providers_used": list(dict.fromkeys(providers_used)),
            "providers_failed": list(dict.fromkeys(providers_failed)),
            "sources_retrieved": unique_sources[:20],
            "articles_count": len(articles),
            "is_geographic": ctx.is_geographic,
        }


# Singleton
global_news_engine = GlobalNewsEngine()
