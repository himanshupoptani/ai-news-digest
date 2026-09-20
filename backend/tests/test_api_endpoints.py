import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "AI News Intelligence Platform" in data["platform"]
    assert data["database"] == "connected (SQLite)"

def test_news_search_endpoint(client):
    payload = {"query": "Nvidia", "limit": 3, "mode": "demo"}
    response = client.post("/api/news/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Nvidia"
    assert data["total_found"] > 0
    assert len(data["articles"]) <= 3

def test_digest_generate_endpoint(client):
    payload = {"query": "OpenAI AI Safety", "mode": "demo"}
    response = client.post("/api/digest/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "digest" in data
    assert "audit_report" in data
    assert "bias_report" in data
    assert data["digest"]["evidence_strength"] in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]

def test_chat_message_endpoint(client):
    payload = {"message": "What are the latest AI developments?"}
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] is not None
    assert data["content"] != ""
    assert data["role"] == "assistant"

def test_intelligence_graph_endpoint(client):
    response = client.get("/api/intelligence/graph?topic=Technology")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["total_nodes"] > 0

def test_intelligence_timeline_endpoint(client):
    response = client.get("/api/intelligence/timeline?query=Nvidia")
    assert response.status_code == 200
    data = response.json()
    assert data["total_milestones"] > 0
    assert len(data["timeline"]) > 0

def test_intelligence_analytics_endpoint(client):
    response = client.get("/api/intelligence/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "topic_distribution" in data
    assert "source_distribution" in data
    assert "trending_topics" in data

