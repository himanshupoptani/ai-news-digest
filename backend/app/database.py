import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings

# Ensure data directory exists for the SQLite database file
db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# SQLite engine with thread safety for FastAPI async endpoints
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Database session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()

def get_db():
    """Dependency that yields a database session and closes it when the request is complete."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

