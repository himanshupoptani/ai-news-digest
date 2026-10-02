from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

class Event(Base):
    """Represents an overarching news event covered by multiple articles and publishers."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    first_reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    articles = relationship("Article", back_populates="event")

    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title[:30]}...')>"


class ArticleTopic(Base):
    """Association table linking Articles to Topics with classification confidence."""
    __tablename__ = "article_topics"

    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    is_primary = Column(Boolean, default=False)

    article = relationship("Article", back_populates="topic_associations")
    topic = relationship("Topic", back_populates="article_associations")


class Article(Base):
    """Core Article entity representing a collected, analyzed, and synthesized news piece."""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    url = Column(String(500), nullable=False, unique=True, index=True)
    author = Column(String(150), nullable=True)
    raw_content = Column(Text, nullable=True)
    clean_content = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    
    published_at = Column(DateTime, nullable=True, index=True)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Foreign Keys
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    
    # State Machine: Tracks where the article is in the 12-state FSM
    current_state = Column(String(50), default="DISCOVERED", index=True)

    # Deduplication
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_id = Column(Integer, ForeignKey("articles.id"), nullable=True)

    # Rational Agent Multi-Objective Scores
    relevance_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    diversity_score = Column(Float, default=0.0)
    credibility_score = Column(Float, default=0.0)
    final_agent_score = Column(Float, default=0.0, index=True)

    # Relationships
    source = relationship("Source", back_populates="articles")
    event = relationship("Event", back_populates="articles")
    topic_associations = relationship("ArticleTopic", back_populates="article", cascade="all, delete-orphan")
    state_logs = relationship("ArticleStateLog", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:30]}...', state='{self.current_state}')>"

