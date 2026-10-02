from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

class ArticleStateLog(Base):
    """Audit trail logging every transition an article makes in the Finite State Machine."""
    __tablename__ = "article_state_logs"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state = Column(String(50), nullable=True)
    to_state = Column(String(50), nullable=False, index=True)
    reason = Column(Text, nullable=True)  # Explainable AI: why did this transition happen?
    transitioned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    article = relationship("Article", back_populates="state_logs")

    def __repr__(self):
        return f"<StateLog(article_id={self.article_id}, {self.previous_state} -> {self.to_state})>"

