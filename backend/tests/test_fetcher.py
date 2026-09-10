import pytest
from backend.app.services.news_fetcher import NewsFetcher
from backend.app.schemas.news import RawArticle, NewsSearchResponse

@pytest.fixture
def fetcher():
    return NewsFetcher()

def test_fetch_offline_sample_specific_query(fetcher):
    """Verifies that offline dataset correctly filters articles by query keywords."""
    response = fetcher.search(query="Nvidia", limit=5, mode="demo")
    
    assert isinstance(response, NewsSearchResponse)
    assert response.mode_used == "offline-demo"
    assert response.total_found > 0
    assert any("Nvidia" in article.title for article in response.articles)

def test_fetch_offline_sample_ai_query(fetcher):
    """Verifies retrieval of AI safety agreement articles."""
    response = fetcher.search(query="OpenAI Anthropic", limit=3, mode="demo")
    
    assert response.total_found > 0
    first_article = response.articles[0]
    assert isinstance(first_article, RawArticle)
    assert "OpenAI" in first_article.title or "AI" in first_article.title
    assert first_article.source_name in ["Reuters", "Bloomberg", "TechCrunch"]

def test_fetch_offline_fallback_for_unknown_query(fetcher):
    """Verifies that an unknown query falls back to returning top news instead of crashing."""
    response = fetcher.search(query="xyzunobtaniumquery99", limit=3, mode="demo")
    
    assert isinstance(response, NewsSearchResponse)
    assert len(response.articles) > 0  # Graceful fallback ensures non-empty articles for display
