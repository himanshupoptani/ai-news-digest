import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import Source, Topic, Article, ArticleStateLog, ArticleTopic

# Use an in-memory SQLite database for fast, isolated automated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_source_creation(db_session):
    source = Source(name="Test Publisher", domain="testnews.com", credibility_score=0.90)
    db_session.add(source)
    db_session.commit()
    
    saved = db_session.query(Source).filter_by(name="Test Publisher").first()
    assert saved is not None
    assert saved.domain == "testnews.com"
    assert saved.credibility_score == 0.90

def test_article_fsm_state_logging(db_session):
    # 1. Create source
    source = Source(name="Reuters", domain="reuters.com")
    db_session.add(source)
    db_session.commit()

    # 2. Create article
    article = Article(
        title="Breaking News Event",
        url="https://reuters.com/news-1",
        source_id=source.id,
        current_state="DISCOVERED"
    )
    db_session.add(article)
    db_session.commit()

    # 3. Transition state to COLLECTED and log it
    article.current_state = "COLLECTED"
    log = ArticleStateLog(
        article_id=article.id,
        previous_state="DISCOVERED",
        to_state="COLLECTED",
        reason="Metadata and raw content ingested."
    )
    db_session.add(log)
    db_session.commit()

    # 4. Verify relations
    saved_article = db_session.query(Article).filter_by(url="https://reuters.com/news-1").first()
    assert saved_article.current_state == "COLLECTED"
    assert len(saved_article.state_logs) == 1
    assert saved_article.state_logs[0].to_state == "COLLECTED"

