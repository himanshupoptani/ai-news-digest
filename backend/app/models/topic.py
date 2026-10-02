from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    
    # Self-referential relationship for Topic Hierarchy (e.g., Tech -> AI -> LLMs)
    parent_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    parent = relationship("Topic", remote_side=[id], backref="subtopics")

    # Many-to-many relationship with Articles via ArticleTopic
    article_associations = relationship("ArticleTopic", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"

