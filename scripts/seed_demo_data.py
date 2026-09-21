"""
Demo Data Seeder — Phase 17: Offline Demo Mode
Seeds the SQLite database with realistic articles, FSM state transitions,
and enriched metadata so all dashboard tabs show meaningful data at viva time.
Run: python scripts/seed_demo_data.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.database import engine, Base, SessionLocal
from backend.app.models.source import Source
from backend.app.models.topic import Topic
from backend.app.models.article import Article, Event
from backend.app.models.state import ArticleStateLog

def seed_demo_data():
    """Seeds all tables with rich demo data for offline presentation."""
    print("=" * 60)
    print("AI NEWS INTELLIGENCE PLATFORM — DEMO DATA SEEDER")
    print("=" * 60)

    # Create tables
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # ── 1. SOURCES ──────────────────────────────────────────────
        print("\n[1/5] Seeding sources...")
        existing_sources = {s.name for s in db.query(Source).all()}
        source_data = [
            {"name": "Reuters", "domain": "reuters.com", "credibility_score": 0.95},
            {"name": "Bloomberg", "domain": "bloomberg.com", "credibility_score": 0.94},
            {"name": "TechCrunch", "domain": "techcrunch.com", "credibility_score": 0.85},
            {"name": "Wall Street Journal", "domain": "wsj.com", "credibility_score": 0.93},
            {"name": "Space.com", "domain": "space.com", "credibility_score": 0.88},
            {"name": "The Verge", "domain": "theverge.com", "credibility_score": 0.82},
            {"name": "Wired", "domain": "wired.com", "credibility_score": 0.87},
            {"name": "Financial Times", "domain": "ft.com", "credibility_score": 0.96},
            {"name": "The Guardian", "domain": "theguardian.com", "credibility_score": 0.86},
        ]
        sources = {}
        for s in source_data:
            if s["name"] not in existing_sources:
                obj = Source(**s)
                db.add(obj)
                db.commit()
                db.refresh(obj)
            else:
                obj = db.query(Source).filter_by(name=s["name"]).first()
            sources[s["name"]] = obj
        print(f"   ✓ {len(sources)} sources seeded")

        # ── 2. TOPIC TAXONOMY ────────────────────────────────────────
        print("\n[2/5] Seeding topic taxonomy...")
        existing_topics = {t.slug: t for t in db.query(Topic).all()}

        root_topics = [
            {"name": "Technology", "slug": "technology", "description": "Tech industry and innovation"},
            {"name": "Economy", "slug": "economy", "description": "Global financial markets and economics"},
            {"name": "Science", "slug": "science", "description": "Scientific research and exploration"},
        ]
        root_topic_objs = {}
        for rt in root_topics:
            if rt["slug"] not in existing_topics:
                obj = Topic(**rt)
                db.add(obj)
                db.commit()
                db.refresh(obj)
            else:
                obj = existing_topics[rt["slug"]]
            root_topic_objs[rt["slug"]] = obj

        subtopics = [
            {"name": "Artificial Intelligence", "slug": "ai", "description": "AI, ML and LLM research", "parent": "technology"},
            {"name": "Semiconductors", "slug": "semiconductors", "description": "Chips, foundries and hardware", "parent": "technology"},
            {"name": "Federal Reserve", "slug": "federal-reserve", "description": "Monetary policy and interest rates", "parent": "economy"},
            {"name": "Space Exploration", "slug": "space", "description": "NASA and SpaceX missions", "parent": "science"},
        ]
        # Re-read existing topics after root inserts
        existing_topics = {t.slug: t for t in db.query(Topic).all()}
        for st in subtopics:
            if st["slug"] not in existing_topics:
                parent_key = st.pop("parent")
                parent = root_topic_objs.get(parent_key)
                st["parent_id"] = parent.id if parent else None
                obj = Topic(**st)
                db.add(obj)
                try:
                    db.commit()
                except Exception:
                    db.rollback()
        print(f"   ✓ Topic taxonomy seeded")

        # ── 3. ARTICLES WITH FSM STATES ───────────────────────────────
        print("\n[3/5] Seeding articles with FSM state transitions...")
        sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_news.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_articles = json.load(f)

        existing_urls = {a.url for a in db.query(Article).all()}
        states_progression = [
            "DISCOVERED", "COLLECTED", "CLEANED", "CLASSIFIED",
            "FILTERED", "RELEVANT", "DUPLICATE_CHECKED", "SELECTED",
            "RETRIEVED", "SUMMARIZED", "VERIFIED", "PUBLISHED"
        ]

        articles_added = 0
        for art_data in sample_articles:
            if art_data["url"] in existing_urls:
                continue
            src = sources.get(art_data["source_name"])
            if not src:
                src = list(sources.values())[0]

            article = Article(
                title=art_data["title"],
                url=art_data["url"],
                source_id=src.id,
                raw_content=art_data["content"],
                published_at=datetime.fromisoformat(art_data["published_at"].replace("Z", "+00:00")),
                current_state="PUBLISHED"
            )
            db.add(article)
            db.commit()
            db.refresh(article)

            # Simulate full FSM audit trail
            for state in states_progression:
                log = ArticleStateLog(
                    article_id=article.id,
                    previous_state=None if state == "DISCOVERED" else states_progression[states_progression.index(state) - 1],
                    to_state=state,
                    transitioned_at=datetime.now(timezone.utc)
                )
                db.add(log)
            db.commit()
            articles_added += 1

        print(f"   ✓ {articles_added} new articles seeded with full FSM audit trails")

        # ── 4. SUMMARY STATS ─────────────────────────────────────────
        print("\n[4/5] Final database summary:")
        total_articles = db.query(Article).count()
        total_sources = db.query(Source).count()
        total_topics = db.query(Topic).count()
        total_logs = db.query(ArticleStateLog).count()
        print(f"   • Articles    : {total_articles}")
        print(f"   • Sources     : {total_sources}")
        print(f"   • Topics      : {total_topics}")
        print(f"   • FSM Logs    : {total_logs}")

        print("\n[5/5] Demo data seeding COMPLETE ✓")
        print("=" * 60)
        print("You can now run: python app.py")
        print("And open:        http://127.0.0.1:8000")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
