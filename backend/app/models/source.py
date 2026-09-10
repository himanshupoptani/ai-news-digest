from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    domain = Column(String(150), nullable=True, index=True)
    credibility_score = Column(Float, default=0.85)  # 0.0 to 1.0
    reliability_tier = Column(String(50), default="TIER_1")  # TIER_1, TIER_2, INDEPENDENT
    bias_rating = Column(String(50), default="CENTER")  # CENTER, LEFT, RIGHT, TECH_SPECIFIC
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to Articles published by this source
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', tier='{self.reliability_tier}')>"
