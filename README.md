# 🤖 AI News Intelligence Platform

> **Major Academic Project** — A Trustworthy Multi-Agent News Summarization System with RAG, Hallucination Mitigation & Bias Control

[![Python](https://img.shields.io/badge/Python-3.13.6-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-50%20passed-brightgreen)](docs/test_report.md)
[![Coverage](https://img.shields.io/badge/Coverage-88%25-yellowgreen)](docs/coverage_report/index.html)
[![Mode](https://img.shields.io/badge/Mode-Offline%20Demo-orange)](data/sample_news.json)

---

## 📋 Table of Contents

- [What This Project Does](#-what-this-project-does)
- [AI Modules](#-ai-modules)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Dashboard Tabs](#-dashboard-tabs)
- [API Endpoints](#-api-endpoints)
- [Running Tests](#-running-tests)
- [Pre-Viva Validation](#-pre-viva-validation)
- [Documentation](#-documentation)
- [Technology Stack](#-technology-stack)

---

## 🎯 What This Project Does

The **AI News Intelligence Platform** automatically:

1. **Retrieves** news from live APIs, RSS feeds, or offline sample data (3-tier fallback)
2. **Cleans & Deduplicates** articles using Jaccard + TF-IDF cosine similarity
3. **Selects** the best articles using a PEAS-model Rational Agent with multi-objective scoring
4. **Synthesizes** a grounded AI digest with numbered citations `[1]` `[2]` using RAG
5. **Verifies** every AI claim through a Hallucination Mitigation Shield
6. **Measures** publisher diversity using the Herfindahl-Hirschman Index (HHI)
7. **Provides** a conversational research chatbot with multi-turn memory
8. **Visualises** source relationships as a Knowledge Graph and Chronological Timeline
9. **Reports** trending topics and macro analytics on a modern dashboard

---

## 🧠 AI Modules

| Phase | Module | Algorithm / Concept |
|-------|--------|-------------------|
| 5 | Article FSM Pipeline | 12-State Finite State Machine |
| 6 | Rational News Agent | PEAS Model · Multi-Objective Utility |
| 7 | Vector Store | TF-IDF · Cosine Similarity · Sliding Window Chunking |
| 8 | RAG Engine | Retrieval-Augmented Generation · Grounded Synthesis |
| 9 | Hallucination Shield | Phantom Citation Detection · Evidence Grounding Score |
| 10 | Bias Mitigator | Herfindahl-Hirschman Index (HHI) |
| 11 | Research Chatbot | Multi-Turn Memory · Pronoun Context Resolution |
| 12 | Knowledge Graph | Node-Edge Graph · Topic-Source-Article Relationships |
| 13 | Timeline Service | Chronological Ordering · Milestone Extraction |
| 14 | Analytics Engine | Trend Scoring · Publisher Distribution |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+ installed
- Git installed
- No Node.js, no npm, no Docker required

### 1. Clone / Open Project
```powershell
cd c:\Users\Himan\OneDrive\Desktop\AI-DIGEST
```

### 2. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Seed Demo Database (first time only)
```powershell
python scripts\seed_demo_data.py
```

### 4. Launch the Platform
```powershell
python app.py
```

### 5. Open in Browser
```
http://127.0.0.1:8000          → Dashboard
http://127.0.0.1:8000/docs     → Swagger API UI
http://127.0.0.1:8000/redoc    → ReDoc API UI
```

> **Works 100% offline** — no internet connection required in demo mode.

---

## 📁 Project Structure

```
AI-DIGEST/
│
├── app.py                          # 🚀 Single-command launcher
├── .env                            # Environment configuration
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Test configuration
│
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI application + CORS + routing
│       ├── config.py               # Settings (Pydantic)
│       ├── database.py             # SQLAlchemy engine + session
│       │
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── source.py           # News publisher sources
│       │   ├── topic.py            # Hierarchical topic taxonomy
│       │   ├── article.py          # Articles, Events, ArticleTopics
│       │   ├── state.py            # FSM audit log
│       │   └── chat.py             # Chat sessions & messages
│       │
│       ├── schemas/                # Pydantic request/response schemas
│       │   ├── news.py             # RawArticle, NewsSearchRequest/Response
│       │   ├── chat.py             # ChatTurnRequest/Response
│       │   ├── graph.py            # GraphNode, GraphEdge, GraphDataResponse
│       │   ├── timeline.py         # TimelineEntry, TimelineResponse
│       │   └── analytics.py        # TrendingTopic, AnalyticsDashboardResponse
│       │
│       ├── routers/                # FastAPI API routers
│       │   ├── news.py             # POST /api/news/search
│       │   ├── digest.py           # POST /api/digest/generate
│       │   ├── chat.py             # POST /api/chat/message
│       │   └── intelligence.py     # GET /api/intelligence/{graph,timeline,analytics}
│       │
│       └── services/               # AI engine implementations
│           ├── news_fetcher.py     # 3-tier news retrieval
│           ├── text_processor.py   # HTML cleaning + deduplication
│           ├── state_machine.py    # 12-state FSM
│           ├── rational_agent.py   # PEAS utility agent
│           ├── vector_store.py     # TF-IDF in-memory vector store
│           ├── rag_engine.py       # RAG synthesis engine
│           ├── hallucination_shield.py  # Citation + evidence verification
│           ├── bias_mitigator.py   # HHI publisher diversity analysis
│           ├── chatbot_service.py  # Multi-turn research chatbot
│           ├── graph_service.py    # Knowledge graph builder
│           ├── timeline_service.py # Chronological timeline builder
│           └── analytics_service.py # Trending topics + dashboard stats
│
├── backend/tests/                  # 50 automated test cases
│   ├── test_database.py
│   ├── test_fetcher.py
│   ├── test_text_processor.py
│   ├── test_state_machine.py
│   ├── test_rational_agent.py
│   ├── test_vector_store.py
│   ├── test_rag_engine.py
│   ├── test_hallucination_shield.py
│   ├── test_bias_mitigator.py
│   ├── test_chatbot.py
│   ├── test_graph_service.py
│   ├── test_timeline_service.py
│   ├── test_analytics_service.py
│   ├── test_api_endpoints.py
│   └── test_offline_demo.py
│
├── frontend/
│   ├── templates/
│   │   └── index.html              # Main SPA dashboard
│   └── static/
│       ├── css/styles.css          # Custom design accents
│       └── js/
│           ├── api.js              # HTTP client for all endpoints
│           └── app.js              # Tab routing + UI rendering
│
├── data/
│   ├── sample_news.json            # 15 offline demo articles
│   └── news_intelligence.db        # SQLite database
│
├── scripts/
│   ├── init_db.py                  # Initial database setup
│   ├── seed_demo_data.py           # Demo data seeder (run before first launch)
│   └── validate_demo.py            # Pre-viva 19-point health checker
│
└── docs/
    ├── project_report.md           # Full academic project report
    ├── test_report.md              # 50-test QA matrix
    ├── viva_qa.md                  # 50 viva Q&A with model answers
    ├── coverage.xml                # Machine-readable coverage data
    └── coverage_report/            # HTML coverage report (open index.html)
```

---

## 🖥️ Dashboard Tabs

| Tab | What It Shows |
|-----|--------------|
| **Discover** | Trending topics, platform health, macro statistics |
| **News Search** | Query-based article search with publisher badges |
| **AI Digest** | RAG synthesis · Citations `[1][2]` · Evidence strength · HHI bias score |
| **Research Chat** | Multi-turn chatbot with source attribution |
| **Knowledge Graph** | Topic → Publisher → Article relationship map |
| **Timeline** | Chronological milestone sequence for any news event |
| **Analytics** | Trend scores, category distribution, FSM state breakdown |

---

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Platform health check |
| `POST` | `/api/news/search` | Search, deduplicate & rank articles |
| `POST` | `/api/digest/generate` | Generate AI digest with citations |
| `POST` | `/api/chat/message` | Send chatbot message |
| `GET` | `/api/chat/sessions` | List research sessions |
| `GET` | `/api/chat/history/{id}` | Get session message history |
| `GET` | `/api/intelligence/graph` | Knowledge graph data |
| `GET` | `/api/intelligence/timeline` | Chronological timeline |
| `GET` | `/api/intelligence/analytics` | Trending topics & analytics |

**Interactive docs:** `http://127.0.0.1:8000/docs`

---

## 🧪 Running Tests

```powershell
# Run all 50 tests
.\venv\Scripts\pytest

# Run with coverage report
.\venv\Scripts\pytest --cov=backend/app --cov-report=html:docs/coverage_report

# Open HTML coverage report
start docs\coverage_report\index.html

# Run a specific test module
.\venv\Scripts\pytest backend\tests\test_rag_engine.py -v
```

**Results:** 50 passed · 0 failed · 88% line coverage · ~11 seconds

---

## ✅ Pre-Viva Validation

Run this before your viva to confirm everything works offline:

```powershell
.\venv\Scripts\python.exe scripts\validate_demo.py
```

Expected output:
```
============================================================
  AI NEWS INTELLIGENCE PLATFORM — OFFLINE VALIDATION
============================================================
  ✅  Settings load correctly
  ✅  sample_news.json exists with 8+ articles
  ✅  SQLite database connection
  ✅  Sources and articles seeded in DB
  ✅  News fetcher returns articles in demo mode
  ✅  Text deduplication pipeline works
  ✅  Rational Agent ranking (PEAS model)
  ✅  Vector Store indexing and semantic search
  ✅  RAG Engine grounded synthesis (offline)
  ✅  Hallucination Shield verification
  ✅  Bias Mitigator HHI analysis
  ✅  Conversational Chatbot (multi-turn RAG)
  ✅  Knowledge Graph generation
  ✅  Timeline chronological ordering
  ✅  Analytics dashboard aggregation
  ✅  GET /api/health
  ✅  POST /api/news/search
  ✅  POST /api/digest/generate
  ✅  POST /api/chat/message

  🎉 ALL 19 CHECKS PASSED — PLATFORM IS VIVA-READY!
============================================================
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`docs/project_report.md`](docs/project_report.md) | Full academic report (Abstract → References) |
| [`docs/test_report.md`](docs/test_report.md) | 50-test QA matrix with coverage breakdown |
| [`docs/viva_qa.md`](docs/viva_qa.md) | 50 viva questions with model answers |
| [`docs/coverage_report/index.html`](docs/coverage_report/index.html) | Visual HTML coverage report |

---

## 🛠️ Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.13.6 |
| Web Framework | FastAPI | 0.115+ |
| Database ORM | SQLAlchemy | 2.0+ |
| Database | SQLite | 3 |
| ML / NLP | Scikit-learn | 1.5+ |
| HTML Parsing | BeautifulSoup4 | 4.12+ |
| Data Validation | Pydantic | v2 |
| ASGI Server | Uvicorn | 0.30+ |
| RSS Parsing | feedparser | 6.0+ |
| Testing | pytest + pytest-cov | 9.1+ |
| Frontend CSS | Tailwind CSS | CDN |
| Frontend JS | Vanilla JavaScript | ES6+ |

---

## 🔑 Environment Variables (`.env`)

```env
APP_MODE=demo              # 'demo' (offline) or 'live' (requires API key)
NEWSAPI_KEY=               # Optional: get free key at newsapi.org
DATABASE_URL=sqlite:///./data/news_intelligence.db
SECRET_KEY=ai-digest-secret-key
HOST=127.0.0.1
PORT=8000
DEBUG=True
ENVIRONMENT=development
PROJECT_NAME=AI News Intelligence Platform
```

---

## 📊 Key Formulas (Viva Reference)

| Formula | Name |
|---------|------|
| $U(a) = 0.35R + 0.25F + 0.20D + 0.20C$ | Rational Agent Utility |
| $F = e^{-0.015 \cdot \Delta t_{\text{hrs}}}$ | Freshness Decay |
| $\text{sim}(A,B) = \frac{A \cdot B}{\|A\| \cdot \|B\|}$ | Cosine Similarity |
| $HHI = \sum_{i=1}^{n} s_i^2$ | Publisher Bias (HHI) |
| $J(A,B) = \frac{\|A \cap B\|}{\|A \cup B\|}$ | Jaccard Deduplication |

---

*Built with ❤️ as a Major Academic Project · All rights reserved · Local development only*
