import sys
import os

# Add project root to sys.path so backend imports work reliably
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, SessionLocal, Base
from backend.app.models import (
    Source,
    Topic,
    Article,
    Event,
    ArticleTopic,
    ArticleStateLog,
    ChatSession,
    ChatMessage
)

def init_database():
    print("==================================================")
    print("INITIALIZING DATABASE TABLES...")
    print("==================================================")
    
    # 1. Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully in SQLite database!")

    # 2. Seed initial reference sources and topics
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Source).count() == 0:
            print("\nSeeding initial trusted sources...")
            sources = [
                Source(name="Reuters", domain="reuters.com", credibility_score=0.95, reliability_tier="TIER_1", bias_rating="CENTER"),
                Source(name="BBC News", domain="bbc.com", credibility_score=0.93, reliability_tier="TIER_1", bias_rating="CENTER"),
                Source(name="Associated Press", domain="apnews.com", credibility_score=0.96, reliability_tier="TIER_1", bias_rating="CENTER"),
                Source(name="TechCrunch", domain="techcrunch.com", credibility_score=0.88, reliability_tier="TIER_2", bias_rating="TECH_NICHE"),
                Source(name="MIT Tech Review", domain="technologyreview.com", credibility_score=0.94, reliability_tier="TIER_2", bias_rating="TECH_NICHE"),
                Source(name="Bloomberg", domain="bloomberg.com", credibility_score=0.92, reliability_tier="TIER_1", bias_rating="CENTER"),
            ]
            db.add_all(sources)
            db.commit()
            print(f"✓ Seeded {len(sources)} initial sources.")

        if db.query(Topic).count() == 0:
            print("\nSeeding initial topic taxonomy...")
            root_tech = Topic(name="Technology", slug="technology", description="General technology news and innovations")
            db.add(root_tech)
            db.commit()

            subtopics = [
                Topic(name="Artificial Intelligence", slug="artificial-intelligence", description="AI, LLMs, Neural Networks, Robotics", parent_id=root_tech.id),
                Topic(name="Semiconductors", slug="semiconductors", description="Chips, GPUs, Fabrication, TSMC, Nvidia", parent_id=root_tech.id),
                Topic(name="Cybersecurity", slug="cybersecurity", description="Data privacy, breaches, encryption, threats", parent_id=root_tech.id),
                Topic(name="Clean Energy", slug="clean-energy", description="Solar, EV batteries, Grid innovation", parent_id=root_tech.id),
            ]
            db.add_all(subtopics)
            db.commit()
            print(f"✓ Seeded 1 root topic and {len(subtopics)} hierarchical subtopics.")

        # 3. Test insertion of an article with state transition
        if db.query(Article).count() == 0:
            print("\nTesting sample article and state transition...")
            reuters = db.query(Source).filter_by(name="Reuters").first()
            ai_topic = db.query(Topic).filter_by(slug="artificial-intelligence").first()

            test_article = Article(
                title="AI Research Lab Unveils Breakthrough Reasoning Architecture",
                url="https://reuters.com/technology/ai-breakthrough-reasoning-2026",
                author="Jane Doe",
                raw_content="<p>Researchers today demonstrated a new transformer reasoning paradigm...</p>",
                clean_content="Researchers today demonstrated a new transformer reasoning paradigm with verified test-time compute scaling.",
                ai_summary="New AI architecture achieves state-of-the-art results through test-time compute scaling.",
                source_id=reuters.id,
                current_state="PUBLISHED",
                relevance_score=0.94,
                freshness_score=0.98,
                diversity_score=0.85,
                credibility_score=0.95,
                final_agent_score=0.93
            )
            db.add(test_article)
            db.commit()

            # Link Article to Topic
            article_topic = ArticleTopic(
                article_id=test_article.id,
                topic_id=ai_topic.id,
                confidence=0.98,
                is_primary=True
            )
            db.add(article_topic)

            # Record FSM State Transition Log
            state_log = ArticleStateLog(
                article_id=test_article.id,
                previous_state="VERIFIED",
                to_state="PUBLISHED",
                reason="Passed hallucination mitigation check and source diversity quota."
            )
            db.add(state_log)
            db.commit()
            print(f"✓ Created test article #{test_article.id} with Topic link and FSM State Log.")

        print("\n==================================================")
        print("DATABASE VERIFICATION PASSED SUCCESSFULLY!")
        print("==================================================")
        print(f"Total Sources in DB:  {db.query(Source).count()}")
        print(f"Total Topics in DB:   {db.query(Topic).count()}")
        print(f"Total Articles in DB: {db.query(Article).count()}")
        print(f"Total State Logs:     {db.query(ArticleStateLog).count()}")
        print("==================================================")

    except Exception as e:
        db.rollback()
        print(f"Error during database initialization: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
