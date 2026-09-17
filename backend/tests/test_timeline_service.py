import pytest
from datetime import datetime, timezone
from backend.app.schemas.news import RawArticle
from backend.app.schemas.timeline import TimelineResponse, TimelineEntry
from backend.app.services.timeline_service import TimelineService

def test_generate_timeline_chronological_ordering():
    art_late = RawArticle(
        title="US Government Inks AI Safety Pact",
        url="https://bloomberg.com/ai-2",
        source_name="Bloomberg",
        published_at="2026-09-09T18:00:00Z",
        content="Late afternoon statement on AI frontier model red-teaming."
    )
    art_early = RawArticle(
        title="OpenAI and Anthropic Sign Safety Agreements",
        url="https://reuters.com/ai-1",
        source_name="Reuters",
        published_at="2026-09-09T10:00:00Z",
        content="Early morning announcement regarding formal safety testing pact."
    )
    art_middle = RawArticle(
        title="Tech Industry Reacts to AI Safety Pact",
        url="https://techcrunch.com/ai-3",
        source_name="TechCrunch",
        published_at="2026-09-09T14:30:00Z",
        content="Midday reaction from AI laboratory researchers."
    )

    # Pass articles in shuffled order
    res = TimelineService.generate_timeline([art_late, art_early, art_middle], event_topic="AI Safety Pact Timeline")

    assert isinstance(res, TimelineResponse)
    assert res.total_milestones == 3
    assert len(res.timeline) == 3

    # Check that entries are strictly ascending (10:00 -> 14:30 -> 18:00)
    assert res.timeline[0].source_name == "Reuters"
    assert res.timeline[1].source_name == "TechCrunch"
    assert res.timeline[2].source_name == "Bloomberg"

    # Verify human-readable time format
    assert "Sep 09, 2026 - 10:00 UTC" in res.timeline[0].display_time

def test_generate_timeline_empty():
    res = TimelineService.generate_timeline([], event_topic="Empty Event")
    assert res.total_milestones == 0
    assert len(res.timeline) == 0
