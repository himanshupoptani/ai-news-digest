from pydantic import BaseModel
from typing import List, Optional

class TimelineEntry(BaseModel):
    """Represents a single milestone event on the chronological timeline."""
    id: str
    headline: str
    summary: str
    source_name: str
    url: str
    published_at: str  # Formatted ISO timestamp
    display_time: str  # Human-readable format, e.g. "Sep 09, 2026 - 14:30 UTC"

class TimelineResponse(BaseModel):
    """Complete chronological timeline sequence for a news event or search query."""
    event_topic: str
    total_milestones: int
    timeline: List[TimelineEntry]

