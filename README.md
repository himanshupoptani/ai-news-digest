# AI News Intelligence Platform

An enterprise-grade, academic major project that transforms raw global news streams into synthesized intelligence dossiers using Retrieval-Augmented Generation (RAG), a Rational Agent selection model, and automated Hallucination & Bias mitigations.

---

## Key Features

1. **Live & Fallback News Aggregation:** Multi-source ingestion via REST news APIs, curated RSS feeds, and offline snapshot data.
2. **Rational Agent Scoring (PEAS):** Multi-objective ranking balancing relevance, freshness, source diversity, and duplicate penalties.
3. **Article Selection Finite State Machine (FSM):** 12-state auditable lifecycle tracking from `DISCOVERED` to `PUBLISHED`.
4. **Retrieval-Augmented Generation (RAG):** In-memory semantic vector indexing and cosine similarity chunk retrieval.
5. **Trustworthy AI Controls:**
   - **Hallucination Mitigation:** Grounded context rules, similarity thresholds, and automated Evidence Scoring (`HIGH` / `MED` / `LOW`).
   - **Bias Mitigation:** Publisher concentration detection (Herfindahl index) and cross-source consensus vs. dispute analysis.
6. **Conversational News Chatbot:** Multi-turn conversational context with pronoun and follow-up query rewriting.
7. **Interactive Visual Dashboard:** Built with modern CSS/Tailwind, dark/light theme, timeline views, topic-source graph, and analytics.
8. **Offline Demo Mode:** Zero-dependency fail-safe mode designed for 100% reliable viva presentations.

---

## Local Development Quickstart (VS Code)

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Launch the Application
```powershell
python app.py
```
Open `http://localhost:8000` in your web browser.

