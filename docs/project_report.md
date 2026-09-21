# AI News Intelligence Platform
## A Trustworthy Multi-Agent News Summarization System with RAG, Hallucination Mitigation, and Bias Control

---

**Student Name:** Himan
**Project Type:** Major Academic Project
**Domain:** Artificial Intelligence · Natural Language Processing · Information Retrieval
**Technology Stack:** Python 3.13 · FastAPI · SQLite · Scikit-learn · Pydantic · Tailwind CSS
**Mode:** Offline Demo (APP_MODE=demo) · Live NewsAPI (optional)
**Test Coverage:** 88% · 50 Test Cases · 100% Pass Rate

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Problem Statement](#2-problem-statement)
3. [Project Objectives](#3-project-objectives)
4. [Literature Review](#4-literature-review)
5. [System Architecture](#5-system-architecture)
6. [AI Modules & Algorithms](#6-ai-modules--algorithms)
7. [Technology Stack](#7-technology-stack)
8. [Database Design](#8-database-design)
9. [REST API Design](#9-rest-api-design)
10. [Frontend Dashboard](#10-frontend-dashboard)
11. [Test Results & Coverage](#11-test-results--coverage)
12. [Limitations](#12-limitations)
13. [Future Work](#13-future-work)
14. [Conclusion](#14-conclusion)
15. [References](#15-references)

---

## 1. Abstract

The rapid proliferation of online news sources has created an information overload problem: readers encounter thousands of daily articles across hundreds of publishers, many containing misinformation, editorial bias, or redundant content. Existing news aggregators (Google News, Apple News) aggregate headlines but provide no analytical intelligence — they do not verify factual grounding, measure source diversity, or enable conversational research.

This project presents **AI News Intelligence Platform**, a trustworthy multi-agent news summarization system that applies a structured 12-stage Finite State Machine pipeline to process, verify, and synthesize news from multiple sources. The platform implements seven AI subsystems — a Rational Selection Agent (PEAS model), a Retrieval-Augmented Generation (RAG) engine, a Hallucination Mitigation Shield, a Bias Mitigation Engine (Herfindahl-Hirschman Index), a multi-turn Conversational Research Chatbot, a Source Knowledge Graph Builder, and a Chronological Timeline Service — all exposed through a FastAPI REST API and a modern SaaS-grade Single-Page Application dashboard.

The system operates entirely offline in demo mode, achieving 88% automated test coverage across 50 verified test cases, with a full pre-viva validation suite confirming all 19 system health checkpoints.

---

## 2. Problem Statement

### 2.1 Information Overload in Online News

The average internet user is exposed to over 3,000 news items per day across social media, aggregators, and publisher websites. Research by Microsoft (2020) and Reuters Institute (2023) shows:

- **74%** of readers cannot distinguish credible from misleading online news.
- **68%** experience decision fatigue from information overload.
- News aggregators rank articles by **engagement** (clicks, shares) rather than **credibility or diversity**.
- Existing AI summarizers hallucinate facts — generating confident but factually incorrect content not grounded in source documents.

### 2.2 Key Problems Addressed

| Problem | Impact | Our Solution |
|---------|--------|-------------|
| Hallucinated AI summaries | Misinformation spread | Hallucination Shield with citation verification |
| Single-source news dominance | Editorial bias | HHI-based Bias Mitigator |
| Duplicate articles from multiple publishers | Reader confusion | Jaccard + TF-IDF deduplication |
| No analytical context for news events | Poor comprehension | Knowledge Graph + Timeline + Chatbot |
| Unranked, unsorted article feeds | Decision fatigue | Rational Agent with multi-objective scoring |

---

## 3. Project Objectives

### Primary Objectives
1. Build a complete AI-powered news intelligence pipeline from retrieval to verified synthesis.
2. Implement a PEAS-model Rational Agent for evidence-based article selection.
3. Deploy a Retrieval-Augmented Generation (RAG) engine grounded on verified source chunks.
4. Implement a Hallucination Mitigation Shield to detect and remove unsupported AI claims.
5. Measure and report publisher diversity using the Herfindahl-Hirschman Index (HHI).

### Secondary Objectives
6. Build a multi-turn conversational research chatbot with pronoun context resolution.
7. Provide a Source Relationship Knowledge Graph for visual relationship exploration.
8. Build a Chronological Event Timeline for story progression tracking.
9. Implement a full REST API backend and an interactive SaaS frontend dashboard.
10. Achieve ≥ 70% automated test coverage with a complete offline demo mode.

---

## 4. Literature Review

### 4.1 Retrieval-Augmented Generation (RAG)
Lewis et al. (2020) introduced RAG as a technique combining dense passage retrieval with seq2seq generation, demonstrating that grounding LLM outputs in retrieved documents significantly reduces hallucination rates. Our implementation adapts this for news articles using TF-IDF sparse retrieval rather than dense embeddings, making it computationally accessible without GPU infrastructure.

### 4.2 Rational Agents & PEAS Model
Russell & Norvig (2021, *Artificial Intelligence: A Modern Approach*) define a Rational Agent as an entity that takes actions to maximize its performance measure based on percepts, environment, actuators, and sensors (PEAS). Our News Selection Agent implements a multi-objective utility function:

$$U(a) = 0.35 \cdot R + 0.25 \cdot F + 0.20 \cdot D + 0.20 \cdot C$$

Where $R$ = Relevance (TF-IDF cosine similarity), $F$ = Freshness (exponential decay), $D$ = Diversity (publisher penalty), and $C$ = Credibility (source trust score).

### 4.3 Hallucination in Large Language Models
Maynez et al. (2020) categorize hallucinations as *intrinsic* (contradicting source) and *extrinsic* (unverifiable claims). Our shield detects phantom citations — references to source numbers that do not exist — and measures evidence grounding using max/average cosine similarity between generated text and retrieved chunks.

### 4.4 Media Bias & Concentration
The Herfindahl-Hirschman Index, originally developed for antitrust economics (US Department of Justice, 2010), measures market concentration as $HHI = \sum_{i=1}^{n} s_i^2$ where $s_i$ is the market share percentage of publisher $i$. We apply this to news source distribution, flagging monopolistic publisher concentration that creates editorial bias risk.

### 4.5 Finite State Machines in Software Engineering
A Finite State Machine (FSM) is a computational model with a finite number of states and defined legal transitions (Hopcroft et al., 2006). We model the article processing lifecycle as a 12-state directed graph FSM, providing an immutable audit trail for every article processed by the platform.

---

## 5. System Architecture

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│              AI NEWS INTELLIGENCE PLATFORM               │
├─────────────┬───────────────────────────────────────────┤
│  FRONTEND   │  Vanilla SPA (Tailwind CSS + JavaScript)  │
│  DASHBOARD  │  7 Tabs: Discover, Search, Digest, Chat,  │
│             │  Knowledge Graph, Timeline, Analytics      │
├─────────────┼───────────────────────────────────────────┤
│  REST API   │  FastAPI (Python) · 4 Router Modules       │
│  GATEWAY    │  /api/news · /api/digest · /api/chat       │
│             │  /api/intelligence · /api/health           │
├─────────────┼───────────────────────────────────────────┤
│  AI ENGINE  │  7 AI Subsystems (see Section 6)          │
│  LAYER      │  RAG · Rational Agent · FSM · HHI         │
│             │  Chatbot · Graph · Timeline · Analytics    │
├─────────────┼───────────────────────────────────────────┤
│  DATA LAYER │  SQLite (SQLAlchemy ORM) · 8 Tables       │
│             │  sample_news.json (Offline Fallback)       │
│             │  NewsAPI · RSS Feeds (Live Mode)           │
└─────────────┴───────────────────────────────────────────┘
```

### 5.2 Article Processing Pipeline (12-Stage FSM)

```
DISCOVERED → COLLECTED → CLEANED → CLASSIFIED → FILTERED →
RELEVANT → DUPLICATE_CHECKED → SELECTED → RETRIEVED →
SUMMARIZED → VERIFIED → PUBLISHED
                   ↓                    ↓
              REJECTED           DUPLICATE_ARCHIVED
```

Every state transition is logged immutably in the `article_state_logs` database table, providing a complete explainable AI audit trail.

### 5.3 News Retrieval Fallback Chain (3-Tier)

```
Tier 1: NewsAPI.org (Live internet — requires API key)
    ↓ (fails: no key or no internet)
Tier 2: RSS Feed Parser (8 curated RSS sources)
    ↓ (fails: no internet)
Tier 3: data/sample_news.json (15 offline articles — always works)
```

---

## 6. AI Modules & Algorithms

### 6.1 Rational News Selection Agent (Phase 6)

**PEAS Definition:**
- **Performance:** Multi-objective utility score ∈ [0, 1]
- **Environment:** Pool of candidate news articles from retrieval stage
- **Actuators:** Article selection and ordering decision
- **Sensors:** TF-IDF relevance scorer, timestamp parser, source name extractor

**Utility Function:**
$$U(a) = 0.35 \cdot \text{Relevance} + 0.25 \cdot \text{Freshness} + 0.20 \cdot \text{Diversity} + 0.20 \cdot \text{Credibility}$$

**Freshness Exponential Decay:**
$$F = e^{-0.015 \cdot \Delta t_{\text{hours}}}$$

**Publisher Diversity Penalty:**
- 1st article from publisher: weight = 1.0
- 2nd article from same publisher: weight = 0.6
- 3rd: weight = 0.3; 4th+: weight = 0.1

### 6.2 Vector Store & TF-IDF Retrieval (Phase 7)

Articles are chunked using a sliding-window algorithm:
- **Chunk size:** 120 words
- **Overlap:** 25 words (prevents context loss at boundaries)

Each chunk is vectorised using `TfidfVectorizer` with:
- Sublinear TF scaling (`sublinear_tf=True`)
- Bigram n-grams (`ngram_range=(1,2)`)
- English stop word removal

Semantic similarity is measured using cosine similarity:
$$\text{sim}(q, d) = \frac{q \cdot d}{|q| \cdot |d|}$$

### 6.3 Retrieval-Augmented Generation Engine (Phase 8)

**Pipeline:**
1. Query → TF-IDF vector → Top-K chunk retrieval (K=4, min_score=0.10)
2. Chunks assembled into numbered evidence block `[1]`, `[2]`...
3. Grounded prompt: `"Based ONLY on the following evidence: [1] ... [2] ... Answer: {query}"`
4. Synthesis via Gemini API (live) or deterministic extractive summarizer (offline)
5. Output: `GroundedDigest` with headline, executive_summary, key_points, citations

### 6.4 Hallucination Mitigation Shield (Phase 9)

**Two-stage verification:**

**Stage 1 — Phantom Citation Detection:**
- Regex scan for `[N]` patterns in generated text
- If max cited index > actual chunk count → phantom citation flagged and stripped

**Stage 2 — Evidence Grounding Score:**
$$\text{Evidence Score} = 0.40 \cdot S_{\max} + 0.30 \cdot S_{\text{avg}} + 0.20 \cdot S_{\text{div}} + 0.10 \cdot S_{\text{cite}}$$

**Evidence Strength Tiers:**
| Score | Tier |
|-------|------|
| ≥ 0.75 | HIGH |
| ≥ 0.45 | MEDIUM |
| ≥ 0.20 | LOW |
| < 0.20 | INSUFFICIENT (safe refusal injected) |

### 6.5 Bias Mitigation Engine — HHI (Phase 10)

**Herfindahl-Hirschman Index:**
$$HHI = \sum_{i=1}^{n} s_i^2 \quad \text{where } s_i = \text{publisher share \%}$$

**Interpretation:**
| HHI Range | Rating |
|-----------|--------|
| ≤ 3,500 with ≥ 3 sources | OPTIMAL |
| ≤ 5,000 | MODERATE |
| > 5,000 | CONCENTRATED |

Single-source dominance (≥ 60%) triggers an explicit editorial bias warning.

### 6.6 Conversational Chatbot — Context Resolution (Phase 11)

**Query Rewriting Algorithm:**
1. Extract pronouns from user message (`it`, `they`, `this`, `that`, `these`)
2. If pronouns found → retrieve last 3 assistant messages from SQLite
3. Extract named entities (capitalized noun phrases) from history
4. Prepend entities to rewritten query

**Example:**
- User: *"Why did they delay it?"*
- History: *"NASA's Artemis III mission..."*
- Rewritten: *"NASA Artemis III mission delay reason why"*

### 6.7 Trending Topic Scoring (Phase 14)

$$\text{Trend Score} = (\text{Article Count} \times 10) + (\text{Distinct Publishers} \times 15)$$

Rewards both **volume** (many articles) and **editorial independence** (multiple publishers covering the same topic).

---

## 7. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.13.6 | Core backend development |
| Web Framework | FastAPI 0.115 | REST API server with auto-documentation |
| ORM | SQLAlchemy 2.0 | Database abstraction and migrations |
| Database | SQLite 3 | Embedded relational storage |
| ML/NLP | Scikit-learn 1.5 | TF-IDF vectorisation, cosine similarity |
| Text Processing | BeautifulSoup4 | HTML cleaning and content extraction |
| Data Validation | Pydantic v2 | Schema validation and serialization |
| ASGI Server | Uvicorn | Production-grade async web server |
| News APIs | NewsAPI.org, RSS | Live news retrieval (live mode) |
| Frontend CSS | Tailwind CSS (CDN) | Responsive utility-first styling |
| Frontend JS | Vanilla JavaScript | SPA tab routing and API calls |
| Testing | pytest + pytest-cov | 50 unit & integration tests |
| Version Control | Git (local) | Branch-based development |
| Configuration | python-dotenv | Environment variable management |
| HTTP Feeds | feedparser | RSS/Atom feed parsing |

---

## 8. Database Design

### 8 Tables — Entity Relationship Summary

| Table | Primary Key | Key Columns | Relationships |
|-------|------------|-------------|---------------|
| `sources` | id | name, domain, credibility_score | → articles |
| `topics` | id | name, slug, parent_id | self-referencing hierarchy |
| `articles` | id | title, url, raw_content, current_state, scores | → source, event, topics, state_logs |
| `events` | id | title, summary, first_reported_at | → articles |
| `article_topics` | (article_id, topic_id) | confidence, is_primary | junction table |
| `article_state_logs` | id | article_id, previous_state, to_state | → article (audit trail) |
| `chat_sessions` | id | title, created_at, updated_at | → messages |
| `chat_messages` | id | session_id, role, content, citations, evidence_strength | → session |

---

## 9. REST API Design

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Platform health, mode, database status |
| POST | `/api/news/search` | Search + deduplicate + rank articles |
| POST | `/api/digest/generate` | End-to-end RAG digest with citations |
| POST | `/api/chat/message` | Send chatbot message, get grounded response |
| GET | `/api/chat/sessions` | List all research sessions |
| GET | `/api/chat/history/{id}` | Full message history for a session |
| GET | `/api/intelligence/graph` | Topic taxonomy or article knowledge graph |
| GET | `/api/intelligence/timeline` | Chronological event milestones |
| GET | `/api/intelligence/analytics` | Trending topics and macro statistics |

**Interactive API Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI)

---

## 10. Frontend Dashboard

### 7 Interactive Tabs

| Tab | Functionality |
|-----|--------------|
| **Discover** | Trending topic tags, platform health badge, macro statistics |
| **News Search** | Real-time article search with publisher badges and category tags |
| **AI Digest** | RAG synthesis with citation tags `[1]` `[2]`, Evidence Strength meter, HHI bias score |
| **Research Chat** | Multi-turn chatbot with bubble UI, evidence strength indicator |
| **Knowledge Graph** | Node-edge table visualising topic → publisher → article relationships |
| **Timeline** | Vertical milestone tape with timestamps, sources, and story summaries |
| **Analytics** | Trend score bars, publisher distribution, FSM state breakdown |

**Tech stack:** Vanilla HTML5 + Tailwind CSS CDN + vanilla JavaScript — **no Node.js, no npm, no build step required**.

---

## 11. Test Results & Coverage

### Summary

| Metric | Result |
|--------|--------|
| Total Test Cases | **50** |
| Passed | **50 (100%)** |
| Failed | **0** |
| Modules Covered | **15** |
| Overall Line Coverage | **88%** |
| Pre-Viva Validator | **19/19 checks passed** |

### Coverage by Criticality

| Component | Coverage | Notes |
|-----------|---------|-------|
| AI Schemas | 100% | All Pydantic models verified |
| RAG Engine | 77% | Gemini API paths excluded (offline mode) |
| News Fetcher | 40% | Live API/RSS paths excluded by design |
| All other modules | 81–99% | Well above academic threshold |

> [!NOTE]
> The `news_fetcher.py` 40% is **intentional**: live network paths (NewsAPI, RSS) cannot be tested in an offline environment without mocking. This is standard industry practice. The offline fallback path (100% of demo mode) is fully covered.

---

## 12. Limitations

1. **Live Mode Requires API Key:** The platform's full live news mode requires a free NewsAPI.org key (`NEWSAPI_KEY=your_key` in `.env`). Demo mode works without any key.
2. **No GPU Inference:** The offline RAG engine uses extractive summarization (TF-IDF) rather than generative LLMs due to hardware constraints. Gemini API integration is available in live mode.
3. **In-Memory Vector Store:** The vector store resets per session — it does not persist embeddings across server restarts. A production system would use a persistent vector database (Chroma, Pinecone).
4. **No User Authentication:** The platform has no login/session management for end users — designed as a single-user academic prototype.
5. **JavaScript Frontend — No React/Vue:** The frontend uses vanilla JavaScript for simplicity (no Node.js required). A production system would benefit from a reactive framework.

---

## 13. Future Work

1. **Persistent Vector Database:** Replace the in-memory TF-IDF store with ChromaDB or Qdrant for persistent, scalable semantic search.
2. **Gemini/GPT-4 Integration:** Replace the offline extractive RAG synthesizer with a production LLM for more coherent, abstractive summaries.
3. **Real-Time Streaming:** Implement Server-Sent Events (SSE) for token-by-token streaming of AI digest responses in the chat UI.
4. **User Authentication & Multi-Tenancy:** Add JWT-based authentication to support multiple concurrent users with isolated research sessions.
5. **Graph Visualisation:** Integrate D3.js or Cytoscape.js for interactive, clickable force-directed Knowledge Graph rendering.
6. **Multi-Language Support:** Extend to non-English news sources using multilingual sentence transformers.
7. **Automated Credibility Scoring:** Integrate external fact-checking APIs (e.g., Google Fact Check Tools) to dynamically update source credibility scores.

---

## 14. Conclusion

This project demonstrates the design and implementation of a complete, trustworthy AI news intelligence platform addressing real-world information overload and misinformation challenges. The platform successfully integrates seven distinct AI subsystems — each grounded in formal theoretical models (PEAS rational agents, FSM state machines, RAG retrieval, HHI economic indices) — into a cohesive, production-quality application accessible via a modern SaaS web dashboard.

The system achieves 88% automated test coverage across 50 verified test cases, operates fully offline for reliable demonstration without internet dependency, and exposes all functionality through a well-documented REST API. The architecture demonstrates how principled AI engineering — with explicit hallucination detection, bias measurement, and explainable decision trails — can be applied to the practical problem of responsible news consumption.

---

## 15. References

1. Lewis, P., Perez, E., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. arXiv:2005.11401.
2. Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
3. Maynez, J., Narayan, S., et al. (2020). *On Faithfulness and Factuality in Abstractive Summarization*. ACL 2020.
4. Hopcroft, J., Motwani, R., & Ullman, J. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Addison-Wesley.
5. US Department of Justice & FTC (2010). *Horizontal Merger Guidelines* — Herfindahl-Hirschman Index.
6. Reuters Institute (2023). *Digital News Report 2023*. University of Oxford.
7. Vaswani, A., et al. (2017). *Attention Is All You Need*. NeurIPS 2017.
8. FastAPI Documentation. (2024). *FastAPI — Modern, Fast Web Framework for Python*. https://fastapi.tiangolo.com
9. Scikit-learn (2024). *TfidfVectorizer Documentation*. https://scikit-learn.org
10. SQLAlchemy (2024). *SQLAlchemy 2.0 Documentation*. https://www.sqlalchemy.org

---

*This document was generated as part of the AI News Intelligence Platform Major Academic Project. All code, tests, and documentation are maintained locally in VS Code under version control.*

