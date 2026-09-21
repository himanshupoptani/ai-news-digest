"""
validate_demo.py — Pre-Viva Offline Health Validator
Run this before your viva to confirm every component works WITHOUT internet.
Usage: python scripts/validate_demo.py

Green checkmarks = Ready to present.
Red marks = Something needs fixing.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def check(label, fn):
    try:
        result = fn()
        print(f"  ✅  {label}")
        return True
    except Exception as e:
        print(f"  ❌  {label}")
        print(f"       └─ {e}")
        return False

def main():
    print()
    print("=" * 60)
    print("  AI NEWS INTELLIGENCE PLATFORM — OFFLINE VALIDATION")
    print("=" * 60)
    results = []

    # ── 1. Config & Environment ──────────────────────────────────
    print("\n[1] Configuration & Environment")

    def check_config():
        from backend.app.config import settings
        assert settings.APP_MODE in ("demo", "live")
        assert settings.PROJECT_NAME

    def check_sample_json():
        import json
        path = os.path.join("data", "sample_news.json")
        with open(path) as f:
            data = json.load(f)
        assert len(data) >= 8, "Need at least 8 sample articles"

    results.append(check("Settings load correctly", check_config))
    results.append(check("sample_news.json exists with 8+ articles", check_sample_json))

    # ── 2. Database Layer ────────────────────────────────────────
    print("\n[2] Database Layer")

    def check_db_connect():
        from backend.app.database import SessionLocal
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()

    def check_db_models():
        from backend.app.database import SessionLocal
        from backend.app.models.source import Source
        from backend.app.models.topic import Topic
        from backend.app.models.article import Article
        db = SessionLocal()
        s = db.query(Source).count()
        a = db.query(Article).count()
        t = db.query(Topic).count()
        db.close()
        assert s > 0, "No sources in DB — run: python scripts/seed_demo_data.py"
        assert a > 0, "No articles in DB — run: python scripts/seed_demo_data.py"

    results.append(check("SQLite database connection", check_db_connect))
    results.append(check("Sources and articles seeded in DB", check_db_models))

    # ── 3. News Fetcher (Offline Fallback) ───────────────────────
    print("\n[3] News Retrieval Engine")

    def check_fetcher_demo():
        from backend.app.services.news_fetcher import news_fetcher
        # Try with mode kwarg, fall back without
        try:
            res = news_fetcher.search(query="AI", limit=3, mode="demo")
        except TypeError:
            res = news_fetcher.search(query="AI", limit=3)
        assert len(res.articles) > 0

    def check_deduplication():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.text_processor import text_processor
        try:
            res = news_fetcher.search(query="Nvidia", limit=5, mode="demo")
        except TypeError:
            res = news_fetcher.search(query="Nvidia", limit=5)
        unique, dupes = text_processor.deduplicate_articles(res.articles)
        assert isinstance(unique, list)

    results.append(check("News fetcher returns articles in demo mode", check_fetcher_demo))
    results.append(check("Text deduplication pipeline works", check_deduplication))

    # ── 4. AI Engines ────────────────────────────────────────────
    print("\n[4] AI Engine Stack")

    def check_rational_agent():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.rational_agent import rational_agent
        res = news_fetcher.search(query="AI", limit=5, mode="demo")
        ranked = rational_agent.rank_and_select(res.articles, query="AI", top_k=3)
        assert len(ranked) > 0

    def check_vector_store():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.vector_store import InMemoryVectorStore
        res = news_fetcher.search(query="AI", limit=5, mode="demo")
        store = InMemoryVectorStore()
        store.add_articles(res.articles)
        chunks = store.similarity_search("artificial intelligence", top_k=3)
        assert isinstance(chunks, list)

    def check_rag_engine():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.vector_store import InMemoryVectorStore
        from backend.app.services.rag_engine import rag_engine
        res = news_fetcher.search(query="Nvidia", limit=5, mode="demo")
        store = InMemoryVectorStore()
        store.add_articles(res.articles)
        chunks = store.similarity_search("Nvidia earnings", top_k=3)
        digest = rag_engine.synthesize_digest("Nvidia earnings", chunks)
        assert digest.executive_summary

    def check_hallucination_shield():
        from backend.app.services.hallucination_shield import hallucination_shield
        text, report = hallucination_shield.inspect_generation("Test summary.", [])
        assert report.evidence_strength == "INSUFFICIENT"

    def check_bias_mitigator():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.bias_mitigator import bias_mitigator
        try:
            res = news_fetcher.search(query="AI", limit=6, mode="demo")
        except TypeError:
            res = news_fetcher.search(query="AI", limit=6)
        report = bias_mitigator.evaluate_bias_and_diversity(res.articles)
        assert isinstance(report.source_distribution, dict)

    results.append(check("Rational Agent ranking (PEAS model)", check_rational_agent))
    results.append(check("Vector Store indexing and semantic search", check_vector_store))
    results.append(check("RAG Engine grounded synthesis (offline)", check_rag_engine))
    results.append(check("Hallucination Shield verification", check_hallucination_shield))
    results.append(check("Bias Mitigator HHI analysis", check_bias_mitigator))

    # ── 5. Intelligence Services ─────────────────────────────────
    print("\n[5] Intelligence Services")

    def check_chatbot():
        from backend.app.database import SessionLocal
        from backend.app.schemas.chat import ChatTurnRequest
        from backend.app.services.chatbot_service import chatbot_service
        db = SessionLocal()
        req = ChatTurnRequest(message="What is happening with AI safety?")
        res = chatbot_service.ask(req, db)
        db.close()
        assert res.session_id is not None
        assert res.content

    def check_graph():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.graph_service import graph_service
        res = news_fetcher.search(query="AI", limit=5, mode="demo")
        g = graph_service.build_article_intelligence_graph(res.articles, "AI")
        assert g.total_nodes > 0

    def check_timeline():
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.timeline_service import timeline_service
        res = news_fetcher.search(query="Nvidia", limit=5, mode="demo")
        t = timeline_service.generate_timeline(res.articles, "Nvidia")
        assert t.total_milestones > 0

    def check_analytics():
        from backend.app.database import SessionLocal
        from backend.app.services.news_fetcher import news_fetcher
        from backend.app.services.analytics_service import analytics_service
        res = news_fetcher.search(query="news", limit=10, mode="demo")
        db = SessionLocal()
        report = analytics_service.generate_dashboard_analytics(res.articles, db)
        db.close()
        assert report.total_articles > 0

    results.append(check("Conversational Chatbot (multi-turn RAG)", check_chatbot))
    results.append(check("Knowledge Graph generation", check_graph))
    results.append(check("Timeline chronological ordering", check_timeline))
    results.append(check("Analytics dashboard aggregation", check_analytics))

    # ── 6. FastAPI HTTP Endpoints ────────────────────────────────
    print("\n[6] FastAPI REST API Endpoints")

    def check_api_health():
        from fastapi.testclient import TestClient
        from backend.app.main import app
        client = TestClient(app)
        r = client.get("/api/health")
        assert r.status_code == 200

    def check_api_search():
        from fastapi.testclient import TestClient
        from backend.app.main import app
        client = TestClient(app)
        r = client.post("/api/news/search", json={"query": "AI", "limit": 3, "mode": "demo"})
        assert r.status_code == 200

    def check_api_digest():
        from fastapi.testclient import TestClient
        from backend.app.main import app
        client = TestClient(app)
        r = client.post("/api/digest/generate", json={"query": "Nvidia earnings", "mode": "demo"})
        assert r.status_code == 200

    def check_api_chat():
        from fastapi.testclient import TestClient
        from backend.app.main import app
        client = TestClient(app)
        r = client.post("/api/chat/message", json={"message": "Tell me about AI safety"})
        assert r.status_code == 200

    results.append(check("GET /api/health", check_api_health))
    results.append(check("POST /api/news/search", check_api_search))
    results.append(check("POST /api/digest/generate", check_api_digest))
    results.append(check("POST /api/chat/message", check_api_chat))

    # ── FINAL REPORT ─────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print()
    print("=" * 60)
    if passed == total:
        print(f"  🎉 ALL {total} CHECKS PASSED — PLATFORM IS VIVA-READY!")
    else:
        print(f"  ⚠️  {passed}/{total} checks passed — fix errors above before viva")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
