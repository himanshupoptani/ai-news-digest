import pytest
from backend.app.services.text_processor import TextProcessor
from backend.app.schemas.news import RawArticle

def test_clean_text_strips_html_and_scripts():
    raw_html = "<div><h1>Breaking News</h1><script>alert('hack');</script><p>Major announcement.&nbsp;&nbsp;Full report.</p></div>"
    cleaned = TextProcessor.clean_text(raw_html)
    assert "<script>" not in cleaned
    assert "alert" not in cleaned
    assert "<div>" not in cleaned
    assert cleaned == "Breaking News Major announcement. Full report."

def test_jaccard_similarity_calculation():
    text1 = "OpenAI releases new reasoning model"
    text2 = "OpenAI announces new reasoning model"
    score = TextProcessor.compute_jaccard_similarity(text1, text2)
    assert score >= 0.50

    unrelated = "Delicious chocolate cake recipe"
    score_unrelated = TextProcessor.compute_jaccard_similarity(text1, unrelated)
    assert score_unrelated == 0.0

def test_tfidf_cosine_similarity():
    text1 = "The Federal Reserve maintained interest rates at current benchmarks citing employment stability."
    text2 = "Federal Reserve officials voted to keep interest rates steady as employment remains resilient."
    score = TextProcessor.compute_tfidf_cosine_similarity(text1, text2)
    assert score > 0.20  # Significant similarity in concise two-sentence TF-IDF space

    unrelated = "Astronomers discover water vapor on a distant exoplanet."
    score_unrelated = TextProcessor.compute_tfidf_cosine_similarity(text1, unrelated)
    assert score_unrelated < 0.05

def test_deduplicate_articles_clustering():
    art1 = RawArticle(
        title="OpenAI and Anthropic Sign Safety Agreements with US Government",
        url="https://reuters.com/safety-agreement-1",
        source_name="Reuters",
        content="OpenAI and Anthropic signed testing pacts with the US AI Safety Institute."
    )
    art2 = RawArticle(
        title="US Government Inks AI Safety Pact with OpenAI and Anthropic",
        url="https://bloomberg.com/safety-agreement-2",
        source_name="Bloomberg",
        content="The US AI Safety Institute secured pre-release testing agreements with OpenAI and Anthropic."
    )
    art3 = RawArticle(
        title="NASA Artemis Moon Mission Completes Liquid Fuel Tests",
        url="https://apnews.com/artemis-fuel-test",
        source_name="AP News",
        content="Engineers finished cryogenic propellant loading for the SLS rocket without interface leaks."
    )

    unique, duplicates = TextProcessor.deduplicate_articles([art1, art2, art3])
    
    # art1 and art2 report the same event -> clustered together, leaving 2 unique stories
    assert len(unique) == 2
    assert len(duplicates) == 1
    assert duplicates[0]["primary_source"] == "Reuters"
    assert duplicates[0]["duplicate_source"] == "Bloomberg"
