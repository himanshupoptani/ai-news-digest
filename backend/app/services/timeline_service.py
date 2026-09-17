import re
from datetime import datetime, timezone
from typing import List, Optional

from backend.app.schemas.news import RawArticle
from backend.app.schemas.timeline import TimelineEntry, TimelineResponse

class TimelineService:
    """
    Event Chronological Timeline Service.
    - Normalizes multi-source publication timestamps
    - Orders reporting milestones from earliest to latest
    - Extracts concise milestone narratives for each timestamp
    """

    @staticmethod
    def parse_datetime(dt_str: Optional[str]) -> datetime:
        """Parses various date/time formats into UTC datetime, with fallback."""
        if not dt_str:
            return datetime.now(timezone.utc)

        # Clean string
        clean_str = dt_str.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(clean_str)
        except Exception:
            pass

        # Try common RSS formats like: "Wed, 09 Sep 2026 14:30:00 GMT"
        try:
            return datetime.strptime(clean_str[:25], "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    @classmethod
    def generate_timeline(
        cls, 
        articles: List[RawArticle], 
        event_topic: str = "News Event Timeline"
    ) -> TimelineResponse:
        """
        Builds an ordered chronological timeline of events from a set of articles.
        """
        if not articles:
            return TimelineResponse(
                event_topic=event_topic,
                total_milestones=0,
                timeline=[]
            )

        # Parse timestamps and sort ascending (earliest -> latest)
        article_tuples = []
        for art in articles:
            dt = cls.parse_datetime(art.published_at)
            article_tuples.append((dt, art))

        article_tuples.sort(key=lambda x: x[0])

        entries: List[TimelineEntry] = []
        for idx, (dt, art) in enumerate(article_tuples):
            # Extract first clean sentence as milestone summary
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", art.content) if len(s.strip()) > 20]
            summary = sentences[0] if sentences else art.content[:140]

            display_time = dt.strftime("%b %d, %Y - %H:%M UTC")

            entries.append(
                TimelineEntry(
                    id=f"milestone_{idx + 1}",
                    headline=art.title,
                    summary=summary,
                    source_name=art.source_name,
                    url=art.url,
                    published_at=dt.isoformat(),
                    display_time=display_time
                )
            )

        return TimelineResponse(
            event_topic=event_topic,
            total_milestones=len(entries),
            timeline=entries
        )

# Singleton instance
timeline_service = TimelineService()
