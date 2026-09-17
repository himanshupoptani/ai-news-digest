import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.article import Article
from backend.app.models.source import Source
from backend.app.models.topic import Topic
from backend.app.schemas.news import RawArticle
from backend.app.schemas.analytics import AnalyticsDashboardResponse, TrendingTopic
from backend.app.services.analytics_service import AnalyticsService

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()

    source = Source(name="Reuters", domain="reuters.com")
    session.add(source)
    session.commit()

    topic = Topic(name="AI", slug="ai")
    session.add(topic)
    session.commit()

    art = Article(
        title="Test Article",
        url="https://test.com/1",
        source_id=source.id,
        current_state="PUBLISHED"
    )
    session.add(art)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_calculate_trending_topics():
    art1 = RawArticle(
        title="OpenAI releases new reasoning model",
        url="u1",
        source_name="Reuters",
        content="Artificial intelligence frontier models demonstrated new reasoning capabilities.",
        category="AI"
    )
    art2 = RawArticle(
        title="AI safety standards agreed upon",
        url="u2",
        source_name="Bloomberg",
        content="US institutes evaluate AI models with frontier labs.",
        category="AI"
    )
    art3 = RawArticle(
        title="Nvidia Blackwell chips enter mass shipment",
        url="u3",
        source_name="Reuters",
        content="Nvidia hardware GPUs ramp up production.",
        category="Tech"
    )

    trending = AnalyticsService.calculate_trending_topics([art1, art2, art3])

    assert len(trending) > 0
    top_tag = trending[0]
    assert isinstance(top_tag, TrendingTopic)
    # #AI has 2 matching articles across 2 distinct sources: (2 * 10) + (2 * 15) = 50.0
    assert top_tag.tag == "#AI"
    assert top_tag.article_count == 2
    assert top_tag.source_count == 2
    assert top_tag.trend_score == 50.0

def test_generate_dashboard_analytics(db):
    art1 = RawArticle(
        title="Story 1", url="u1", source_name="Reuters", content="Fed cuts rates.", category="Economy"
    )
    art2 = RawArticle(
        title="Story 2", url="u2", source_name="Bloomberg", content="Nvidia GPU beat.", category="Tech"
    )

    analytics = AnalyticsService.generate_dashboard_analytics([art1, art2], db)

    assert isinstance(analytics, AnalyticsDashboardResponse)
    assert analytics.total_articles == 2
    assert "Economy" in analytics.topic_distribution
    assert "Tech" in analytics.topic_distribution
    assert "Reuters" in analytics.source_distribution
    assert "Bloomberg" in analytics.source_distribution
    assert "PUBLISHED" in analytics.fsm_state_summary
