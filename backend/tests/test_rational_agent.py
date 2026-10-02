import pytest
from datetime import datetime, timezone, timedelta
from backend.app.schemas.news import RawArticle
from backend.app.services.rational_agent import RationalNewsAgent, ScoreBreakdown

def test_relevance_calculation():
    query = "Nvidia Blackwell GPU"
    
    art_relevant = RawArticle(
        title="Nvidia Blackwell GPU Architecture Enters Full Production",
        url="https://reuters.com/nvidia-1",
        source_name="Reuters",
        content="Nvidia CEO announced Blackwell chip shipments commence next month."
    )
    
    art_irrelevant = RawArticle(
        title="Local Zoo Celebrates Birth of Rare Giant Panda Twins",
        url="https://news.com/zoo-1",
        source_name="Local News",
        content="Two giant panda cubs were born this morning in a conservation enclosure."
    )

    score_rel = RationalNewsAgent.calculate_relevance(art_relevant, query)
    score_irrel = RationalNewsAgent.calculate_relevance(art_irrelevant, query)

    assert score_rel > 0.60
    assert score_irrel == 0.0

def test_freshness_exponential_decay():
    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    five_days_ago = (now - timedelta(days=5)).isoformat()

    fresh_score = RationalNewsAgent.calculate_freshness(one_hour_ago)
    old_score = RationalNewsAgent.calculate_freshness(five_days_ago)

    assert fresh_score > 0.90
    assert old_score < 0.30
    assert fresh_score > old_score

def test_source_diversity_penalty():
    # First Reuters article gets full diversity score
    div1 = RationalNewsAgent.calculate_diversity("Reuters", [])
    assert div1 == 1.0

    # Second Reuters article gets moderate score
    div2 = RationalNewsAgent.calculate_diversity("Reuters", ["Reuters"])
    assert div2 == 0.6

    # A different publisher (Bloomberg) gets full diversity bonus
    div_bloomberg = RationalNewsAgent.calculate_diversity("Bloomberg", ["Reuters", "Reuters"])
    assert div_bloomberg == 1.0

def test_rank_and_select_multi_objective():
    query = "Artificial Intelligence Governance"
    now = datetime.now(timezone.utc).isoformat()
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()

    art1 = RawArticle(
        title="AI Governance and Safety Standards Approved by US and UK",
        url="https://reuters.com/ai-gov",
        source_name="Reuters",
        published_at=now,
        content="Global regulators finalized frontier model safety standards."
    )
    art2 = RawArticle(
        title="Tech Giants Form Consortium on Frontier AI Safety",
        url="https://bloomberg.com/ai-gov-2",
        source_name="Bloomberg",
        published_at=now,
        content="Leading AI labs agreed to third-party red teaming."
    )
    art3 = RawArticle(
        title="Historical Retrospective on Computing Governance from 1990",
        url="https://history.com/old-gov",
        source_name="History Magazine",
        published_at=three_days_ago,
        content="A review of early software regulations 30 years ago."
    )

    ranked = RationalNewsAgent.rank_and_select([art1, art2, art3], query, top_k=2)

    assert len(ranked) == 2
    top_article, top_breakdown = ranked[0]
    assert isinstance(top_breakdown, ScoreBreakdown)
    assert top_breakdown.final_score > 0.70
    # Both top articles should be the fresh, relevant news stories
    selected_urls = [a.url for a, b in ranked]
    assert "https://history.com/old-gov" not in selected_urls

