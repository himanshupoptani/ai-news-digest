# AI News Intelligence Platform — Viva Q&A Preparation

**50 Expected Examiner Questions with Model Answers**
Covers every AI concept, design decision, and implementation detail in this project.

> [!TIP]
> Read each answer aloud at least once before your viva. Confidence comes from practising speech, not just reading.

---

## SECTION A — PROJECT OVERVIEW (Questions 1–8)

---

**Q1. In one sentence, what does your project do?**

> My project is an AI-powered news intelligence platform that automatically retrieves news from multiple publishers, removes duplicates and bias, generates verified AI summaries grounded in cited sources, and provides a conversational research chatbot — all accessible through a modern web dashboard.

---

**Q2. What real-world problem does your project solve?**

> Online news suffers from three critical problems: information overload (thousands of daily articles), AI hallucination (chatbots generating confident but false summaries), and editorial bias (single-source dominance skewing perspective). My platform solves all three simultaneously using structured AI pipelines with explicit verification and bias measurement at each stage.

---

**Q3. Why did you choose news intelligence as your domain?**

> News is a high-stakes domain where misinformation has direct societal consequences — affecting public opinion, financial markets, and policy decisions. It presents rich, multidisciplinary AI challenges: NLP for text processing, information retrieval for article ranking, machine learning for similarity scoring, and knowledge representation for relationship graphs. This made it ideal for demonstrating a full-stack AI system with academic depth.

---

**Q4. What makes your platform different from Google News or Apple News?**

> Google News and Apple News are aggregators — they collect and rank headlines by engagement metrics (clicks, shares). My platform goes three levels deeper:
> 1. **Verification layer:** Hallucination Shield checks every AI-generated claim against cited sources.
> 2. **Bias measurement:** HHI score quantifies publisher concentration mathematically.
> 3. **Conversational intelligence:** Users can ask follow-up questions with multi-turn memory, not just browse headlines.

---

**Q5. How many AI modules does your platform have? Name them.**

> The platform has **seven AI subsystems**:
> 1. Rational News Selection Agent (PEAS model)
> 2. Finite State Machine (FSM) article processing pipeline
> 3. TF-IDF Vector Store and semantic chunk retrieval
> 4. Retrieval-Augmented Generation (RAG) synthesis engine
> 5. Hallucination Mitigation Shield
> 6. Bias Mitigation Engine (Herfindahl-Hirschman Index)
> 7. Multi-turn Conversational Research Chatbot

---

**Q6. What is the technology stack of your project?**

> - **Backend:** Python 3.13, FastAPI, SQLAlchemy, SQLite
> - **AI/ML:** Scikit-learn (TF-IDF, cosine similarity), BeautifulSoup, Pydantic
> - **Frontend:** Vanilla HTML5, Tailwind CSS (CDN), Vanilla JavaScript — no Node.js required
> - **Testing:** pytest, pytest-cov (88% coverage, 50 tests)
> - **API Server:** Uvicorn (ASGI)
> - **Version Control:** Git (local, development branch)

---

**Q7. How do you start the platform?**

> ```powershell
> python app.py
> ```
> Then open `http://127.0.0.1:8000` in any browser. The single command launches the FastAPI server with all 7 AI modules loaded, the SQLite database connected, and the frontend dashboard served automatically.

---

**Q8. What happens if there is no internet connection during your demo?**

> The platform has a 3-tier fallback chain:
> - Tier 1: NewsAPI.org (live internet)
> - Tier 2: RSS feed parsing (live internet)
> - Tier 3: `data/sample_news.json` (15 curated offline articles — always works)
>
> I also have a pre-viva validator script: `python scripts/validate_demo.py` which checks all 19 system components and confirms the platform is viva-ready. If WiFi fails, everything continues working from the offline sample dataset.

---

## SECTION B — ARTIFICIAL INTELLIGENCE CONCEPTS (Questions 9–25)

---

**Q9. What is a Rational Agent? How have you implemented it?**

> A Rational Agent (Russell & Norvig, 2021) is a system that takes the action that maximises its performance measure given its percepts and knowledge. I implement it using the PEAS framework:
> - **Performance:** Multi-objective utility score
> - **Environment:** Pool of retrieved candidate articles
> - **Actuators:** Article selection and ordering
> - **Sensors:** Relevance scorer, timestamp parser, publisher tracker
>
> The utility formula is:
> $U(a) = 0.35 \times \text{Relevance} + 0.25 \times \text{Freshness} + 0.20 \times \text{Diversity} + 0.20 \times \text{Credibility}$

---

**Q10. Why did you choose those specific weights (0.35, 0.25, 0.20, 0.20) for your utility function?**

> The weights reflect the relative importance of each factor for a news intelligence system:
> - **Relevance (0.35):** The highest weight because topically off-target articles waste the user's time regardless of freshness.
> - **Freshness (0.25):** News is time-sensitive; a 3-day-old article about a breaking story is significantly less valuable.
> - **Diversity (0.20):** Publisher variety prevents echo-chamber summaries, but is secondary to relevance and freshness.
> - **Credibility (0.20):** Publisher trust is important but typically high across established news sources, so it needs less weight.
>
> These weights are configurable in `config.py` — I designed them to be tunable for different use cases.

---

**Q11. What is the Freshness Decay formula and why exponential decay specifically?**

> $F = e^{-0.015 \times \Delta t_{\text{hours}}}$
>
> I chose **exponential decay** because news relevance doesn't drop linearly — a 1-hour-old breaking story is vastly more relevant than a 24-hour-old one, but the difference between a 3-day and 4-day-old article is small. Exponential functions naturally model this "high initial drop, slow tail" behaviour. The decay constant 0.015 was calibrated so that a 24-hour-old article retains ~70% freshness, and a 72-hour-old article retains ~35%.

---

**Q12. What is a Finite State Machine? Why did you use one for article processing?**

> A Finite State Machine (FSM) is a computational model with a finite set of states and defined legal transitions between them. I used an FSM because:
> 1. **Explainability:** Every article has a clear, auditable processing history — examiners and users can see exactly what happened to each article.
> 2. **Error prevention:** The directed graph enforces legal transitions — an article cannot jump from DISCOVERED to PUBLISHED without passing through all intermediate verification stages.
> 3. **Compliance:** In real news systems, regulatory compliance requires documented audit trails of how content was selected and processed.
>
> My FSM has 12 states: DISCOVERED → COLLECTED → CLEANED → CLASSIFIED → FILTERED → RELEVANT → DUPLICATE_CHECKED → SELECTED → RETRIEVED → SUMMARIZED → VERIFIED → PUBLISHED, plus two terminal rejection states.

---

**Q13. What is Retrieval-Augmented Generation (RAG)? Why is it better than a standalone LLM?**

> RAG (Lewis et al., 2020) combines information retrieval with text generation:
> 1. **Retrieve:** Find the most relevant document chunks from a local corpus using vector similarity.
> 2. **Augment:** Include those chunks as grounded evidence in the prompt: *"Based ONLY on: [1] ... [2] ... Answer: {query}"*
> 3. **Generate:** The LLM synthesizes a response constrained to the provided evidence.
>
> **Why better than standalone LLM?** A standalone LLM (e.g., asking ChatGPT about today's news) can hallucinate — generating plausible but false statements from its training data. RAG forces the model to anchor responses to retrieved, dated, sourced documents. This is critical for news where accuracy is paramount.

---

**Q14. What is TF-IDF and how does it work?**

> TF-IDF stands for **Term Frequency–Inverse Document Frequency**. It measures how important a word is to a document relative to a corpus:
>
> $\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)$
>
> Where:
> - $\text{TF}(t, d) = \frac{\text{count of term } t \text{ in document } d}{\text{total terms in } d}$ (how often the term appears)
> - $\text{IDF}(t) = \log\frac{N}{\text{documents containing } t}$ (how rare the term is across all documents)
>
> A word like "the" appears everywhere → low IDF → low TF-IDF weight. A word like "Blackwell" (Nvidia's chip) appears rarely → high IDF → high TF-IDF when it appears → strongly signals relevance.

---

**Q15. What is Cosine Similarity? How do you use it in your project?**

> Cosine similarity measures the angle between two vectors, independent of their magnitude:
>
> $\text{sim}(A, B) = \frac{A \cdot B}{|A| |B|}$
>
> Range: 0.0 (completely different) to 1.0 (identical). I use it in three places:
> 1. **Vector Store retrieval:** Find which article chunks are most semantically similar to the user's query.
> 2. **Deduplication:** Detect near-duplicate articles with body cosine similarity ≥ 0.40.
> 3. **Hallucination Shield:** Measure how well the generated text is supported by retrieved evidence chunks.

---

**Q16. What is a hallucination in AI? How does your shield detect it?**

> An AI hallucination is when a language model generates confident, fluent statements that are factually incorrect or not supported by source documents. There are two types (Maynez et al., 2020):
> - **Intrinsic:** Contradicts the source documents.
> - **Extrinsic:** Adds new information not present in sources.
>
> My Hallucination Shield uses two detection mechanisms:
> 1. **Phantom Citation Detection:** Scans generated text for `[N]` reference tags. If the model cites `[5]` but only 3 chunks exist → phantom citation flagged and removed.
> 2. **Evidence Grounding Score:** Computes cosine similarity between generated text and retrieved chunks. Score < 0.20 → INSUFFICIENT evidence → safe refusal message injected.

---

**Q17. What is the Herfindahl-Hirschman Index (HHI)? How do you apply it to news?**

> HHI is an economic measure of market concentration, used by antitrust regulators (US DOJ):
>
> $HHI = \sum_{i=1}^{n} s_i^2$
>
> Where $s_i$ is the market share percentage of publisher $i$. Range: 0 (perfect competition) to 10,000 (absolute monopoly).
>
> **In my project:** Instead of market share, $s_i$ is the percentage of selected articles from each publisher. Examples:
> - 5 publishers equally → HHI = 5 × 20² = 2,000 (OPTIMAL)
> - 1 publisher → HHI = 1 × 100² = 10,000 (CONCENTRATED, bias alert)
>
> **Why this matters:** If 80% of articles come from Reuters, the AI digest will reflect Reuters' editorial perspective — not a balanced view.

---

**Q18. What is a Knowledge Graph? How is it used in your project?**

> A Knowledge Graph represents information as nodes (entities) and edges (relationships). In my project:
> - **Nodes:** Topics, Publishers (Sources), Articles
> - **Edges:** `CONTAINS_SUBTOPIC`, `COVERED_BY`, `PUBLISHED`
>
> When a user searches for "Nvidia", the graph builder creates:
> `Nvidia (topic) → Bloomberg (source) → Article A`
> `Nvidia (topic) → Reuters (source) → Article B`
>
> This lets users visually see which publishers covered a topic and how articles relate to each other — essential for detecting single-source reporting.

---

**Q19. How does your conversational chatbot resolve pronouns like "it" or "they"?**

> My `resolve_query_context` method:
> 1. Detects pronoun indicators in the user message (`it`, `they`, `this`, `these`, `that`, `why`, `how`, `what happened`)
> 2. Fetches the last 3 assistant messages from SQLite for this session
> 3. Extracts capitalized noun phrases (named entities) from those messages
> 4. Prepends them to the rewritten search query
>
> **Example:**
> - Previous assistant message: *"Nvidia's Blackwell GPU production is ramping up..."*
> - User: *"Why is it being delayed?"*
> - Rewritten query: *"Nvidia Blackwell GPU delay reason why"*
> - The RAG engine then retrieves relevant chunks using the enriched query.

---

**Q20. What is the sliding window chunking algorithm you use?**

> Instead of indexing whole articles (which can be 500+ words), I split them into overlapping chunks:
> - **Chunk size:** 120 words
> - **Overlap:** 25 words
>
> **Why overlap?** Without overlap, a sentence spanning a chunk boundary would be split mid-context. The 25-word overlap ensures that boundary sentences appear fully in at least one chunk.
>
> **Example:** Article of 300 words →
> - Chunk 1: words 1–120
> - Chunk 2: words 96–215 (overlaps words 96–120 with chunk 1)
> - Chunk 3: words 191–300 (overlaps words 191–215 with chunk 2)

---

**Q21. What is the difference between your offline (extractive) RAG and live (generative) RAG?**

> | Mode | Method | Output Style |
> |------|--------|-------------|
> | **Offline (demo)** | Extractive — selects and concatenates the most relevant sentences directly from retrieved chunks | Accurate but less fluent |
> | **Live (Gemini API)** | Abstractive — sends chunks as context to Gemini, which writes a coherent narrative synthesis | More natural and readable |
>
> Both modes produce the same `GroundedDigest` schema with citations `[1]`, `[2]` — the frontend cannot tell which mode was used. This makes the offline demo indistinguishable from the live version.

---

**Q22. What is sublinear TF scaling and why do you use it?**

> Standard TF counts raw word frequency. Sublinear TF scaling applies logarithm:
> $\text{TF}_{\text{sublinear}}(t, d) = 1 + \log(\text{count}(t, d))$
>
> **Why?** A word appearing 100 times in an article is not 10x more important than one appearing 10 times — it's probably just a repetitive article about the same thing. Sublinear scaling prevents high-frequency repetition from dominating similarity scores, giving more balanced importance to diverse vocabulary.

---

**Q23. What are bigrams and why do you use them in TF-IDF?**

> A **bigram** is a pair of consecutive words treated as a single token. Instead of just "artificial" and "intelligence" separately, a bigram creates "artificial_intelligence" as one feature.
>
> **Why?** Many important news entities are multi-word: "Federal Reserve", "Nvidia Blackwell", "AI Safety". Without bigrams, querying "AI Safety" would match documents containing "AI" and "Safety" separately — even if they're about unrelated topics. Bigrams capture these compound concepts more precisely.
> I use `ngram_range=(1,2)` in `TfidfVectorizer` to include both unigrams and bigrams.

---

**Q24. What is the Jaccard similarity and where do you use it?**

> Jaccard similarity measures overlap between two sets:
>
> $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$
>
> For two article headlines treated as sets of words:
> - "Nvidia reports record earnings" → {nvidia, reports, record, earnings}
> - "Nvidia announces record revenue" → {nvidia, announces, record, revenue}
> - Intersection: {nvidia, record} = 2 words
> - Union: {nvidia, reports, record, earnings, announces, revenue} = 6 words
> - Jaccard = 2/6 = **0.33**
>
> I use Jaccard for **headline deduplication** (threshold ≥ 0.50) because it's computationally cheap and effective for short text comparison. TF-IDF cosine is used for the longer body text.

---

**Q25. What is the difference between precision and recall? Are they relevant to your project?**

> - **Precision:** Of all articles my agent selected, what fraction were actually relevant? (quality of selection)
> - **Recall:** Of all relevant articles that existed, what fraction did my agent find? (coverage of selection)
>
> In my project, the Rational Agent implicitly optimises for **precision** — it selects the top-K highest-utility articles, prioritising quality over exhaustive coverage. Since users are experiencing information overload, it's better to show 5 high-quality articles (high precision) than 50 mixed-quality ones (high recall).

---

## SECTION C — DESIGN & ARCHITECTURE (Questions 26–35)

---

**Q26. Why did you use SQLite instead of PostgreSQL or MySQL?**

> Three reasons:
> 1. **Zero configuration:** SQLite requires no separate server, no installation, no credentials — the database is a single file (`data/news_intelligence.db`). This makes the project fully self-contained for academic demonstration.
> 2. **Academic scope:** With 50–200 articles and single-user access, SQLite's performance is identical to PostgreSQL for this use case.
> 3. **SQLAlchemy ORM abstraction:** My code uses SQLAlchemy — swapping SQLite for PostgreSQL in production requires only changing one line in `config.py` (`DATABASE_URL`). The architecture is production-ready even though the database is simple.

---

**Q27. Why did you use FastAPI instead of Flask or Django?**

> FastAPI offers three advantages over Flask and Django for this use case:
> 1. **Auto-generated Swagger UI:** Every endpoint is automatically documented at `/docs` — I can show the examiner an interactive API browser without any extra work.
> 2. **Pydantic validation:** Request and response schemas are automatically validated — invalid inputs return structured error messages, not Python tracebacks.
> 3. **Async support:** FastAPI is built on ASGI (Uvicorn) — it can handle concurrent requests efficiently, which matters when news retrieval involves parallel API calls.

---

**Q28. What is Pydantic and why is it important in your architecture?**

> Pydantic is a Python data validation library that enforces type-safe schemas at runtime. In my project:
> - `RawArticle`, `ChatTurnRequest`, `GraphDataResponse` etc. are all Pydantic models.
> - When FastAPI receives a JSON request, Pydantic automatically validates it against the schema — wrong types, missing fields, or invalid values are caught before they reach AI modules.
> - When AI modules return results, Pydantic ensures the response matches the documented schema.
>
> This makes the API **self-documenting** and **robust** — no manual validation code needed.

---

**Q29. Why did you use a 3-tier news retrieval fallback chain?**

> Reliability engineering principle: **never have a single point of failure**. If the system depended only on NewsAPI:
> - Demo fails if internet is slow.
> - Demo fails if the API key expires.
> - Demo fails if the API rate limit is hit.
>
> The 3-tier chain (NewsAPI → RSS → Offline JSON) ensures the platform always works. The offline tier is the safety net that makes viva demos risk-free.

---

**Q30. What is CORS and why did you enable it?**

> CORS (Cross-Origin Resource Sharing) is a browser security mechanism that blocks JavaScript on one domain from calling APIs on a different domain. Since my frontend SPA and FastAPI backend run on the same origin (`localhost:8000`), CORS isn't strictly needed. However, I configured `CORSMiddleware` with `allow_origins=["*"]` so that:
> - During development, the API can be tested from tools like Postman or browser console on any port.
> - Future frontend deployments on a different domain (e.g., Netlify) can call the API without reconfiguration.

---

**Q31. What is the purpose of the ArticleStatLog table? Why is it important for AI?**

> The `article_state_logs` table records every state transition an article goes through, including the previous state, new state, and timestamp. This is important for:
> 1. **Explainable AI (XAI):** Regulators and users can audit why a specific article was selected or rejected.
> 2. **Debugging:** If an article appears incorrectly in results, the log shows exactly where in the pipeline it was processed.
> 3. **Academic demonstration:** I can show the FSM audit trail to the examiner as evidence of principled, traceable AI decision-making — not a black box.

---

**Q32. What is a singleton pattern? Where do you use it?**

> A singleton is a design pattern where only one instance of a class exists throughout the application's lifetime. I use it for all service classes:
> ```python
> news_fetcher = NewsFetcher()     # One instance
> rag_engine = RAGEngine()         # One instance
> hallucination_shield = HallucinationShield()  # One instance
> ```
> This means all FastAPI routes share the same pre-initialized service objects — no re-initialization overhead per request, and shared state (like a loaded TF-IDF vectorizer) is preserved.

---

**Q33. What is dependency injection? How does FastAPI use it?**

> Dependency injection (DI) is a design pattern where a component receives its dependencies from an external provider rather than creating them itself. FastAPI uses Python's `Depends()` for DI:
>
> ```python
> @router.get("/sessions")
> def list_sessions(db: Session = Depends(get_db)):
> ```
>
> Here, `get_db` is a generator that creates and yields a database session, then closes it after the request. FastAPI automatically calls `get_db`, injects the session into `list_sessions`, and handles cleanup. This ensures database connections are always properly closed, even if an exception occurs.

---

**Q34. Why did you use an in-memory vector store instead of a persistent one like ChromaDB?**

> **Reason:** ChromaDB and FAISS require C++ compiled binaries that often fail to install on Windows with Python 3.13 due to compilation errors. My pure-Python TF-IDF + numpy implementation has zero binary dependencies and works reliably on any platform.
>
> **Trade-off acknowledged:** The in-memory store resets per request session — it doesn't persist embeddings between calls. For an academic prototype handling 5–15 articles per query, this is perfectly adequate. In production, I would use ChromaDB or Qdrant (future work Section 13 of the project report).

---

**Q35. What is the Single-Page Application (SPA) architecture? Why didn't you need Node.js?**

> An SPA is a web application that loads once and dynamically updates its content without full page reloads. Instead of navigating to new URLs, it switches content panels using JavaScript.
>
> I implemented this with **Vanilla JavaScript** — pure browser-native JS with no frameworks. This means:
> - No npm, no webpack, no build step
> - No Node.js required
> - Launch: `python app.py` → done
>
> FastAPI serves `index.html` (the SPA) at `/`, and the JavaScript calls `/api/*` endpoints. The entire frontend is 3 files: `index.html`, `api.js`, `app.js`.

---

## SECTION D — TESTING & QUALITY (Questions 36–42)

---

**Q36. What is code coverage? What is your project's coverage score?**

> Code coverage measures what percentage of source code lines are executed during tests. My project achieves **88% line coverage** across 1,227 statements. This means 1,085 lines are tested automatically. The remaining 12% consists of live network paths (NewsAPI calls, RSS parsing) that are intentionally excluded during offline testing — standard industry practice for CI/CD pipelines.

---

**Q37. What types of tests did you write? What is the difference between unit and integration tests?**

> I wrote both types:
> - **Unit tests:** Test a single component in isolation. E.g., `test_jaccard_similarity_identical` tests only the Jaccard formula — no database, no API.
> - **Integration tests:** Test multiple components working together. E.g., `test_api_endpoints.py` sends HTTP requests through the full FastAPI stack — router → service → database — and checks the HTTP response.
>
> My 50 tests include both: 43 unit tests for individual services, 7 HTTP integration tests for the full API stack.

---

**Q38. What is a pytest fixture and how do you use it?**

> A pytest fixture is a reusable setup/teardown function that prepares test prerequisites. I use them to create isolated in-memory SQLite databases for each test:
>
> ```python
> @pytest.fixture
> def db():
>     engine = create_engine("sqlite:///:memory:")
>     Base.metadata.create_all(bind=engine)
>     session = Session()
>     yield session      # Test runs here
>     session.close()
>     Base.metadata.drop_all(bind=engine)  # Cleanup
> ```
>
> Each test gets a fresh, empty database — tests cannot pollute each other's state.

---

**Q39. Why do you have 40% coverage on news_fetcher.py? Is that a problem?**

> No, it is not a problem — it's intentional and explainable. The 60% uncovered lines are the live internet code paths: NewsAPI HTTP calls and RSS feed parsing. These cannot be reliably tested in an offline environment without network access or mocking.
>
> The **offline fallback path** (reading `sample_news.json`) is fully covered. In a production system, I would mock the HTTP calls using `unittest.mock` or `responses` library to achieve higher coverage — this is documented as future work.

---

**Q40. What is a ResourceWarning in your test output? Should it concern me?**

> The `ResourceWarning: unclosed database` messages in the test output are caused by SQLite connections not being explicitly closed when test fixtures use in-memory databases. These are **warnings, not errors** — all 50 tests still pass. They don't affect functionality. In production, SQLAlchemy's connection pooling handles cleanup automatically. I noted this as a known minor issue — acknowledging it in a viva shows maturity and honesty about the codebase.

---

**Q41. What would you do to improve test coverage above 88%?**

> Three improvements:
> 1. **Mock HTTP calls:** Use Python's `unittest.mock.patch` to mock `requests.get()` in `news_fetcher.py` — this would allow testing the NewsAPI and RSS parsing paths without internet.
> 2. **Test edge cases:** Add tests for the live Gemini API path in `rag_engine.py` using a mocked response.
> 3. **Test session management:** Add tests for `GET /api/chat/sessions` and `GET /api/chat/history/{id}` endpoints to cover the router paths currently at 64%.

---

**Q42. How do you run the pre-viva validation check?**

> ```powershell
> .\venv\Scripts\python.exe scripts\validate_demo.py
> ```
> This script runs 19 individual health checks across all system layers:
> - Configuration & Environment (2 checks)
> - Database Layer (2 checks)
> - News Retrieval Engine (2 checks)
> - AI Engine Stack (5 checks)
> - Intelligence Services (4 checks)
> - FastAPI REST API Endpoints (4 checks)
>
> All 19 checks output a green ✅ when the platform is viva-ready. If any check fails, it shows the error message so you can fix it before the examiner arrives.

---

## SECTION E — AI ETHICS & CRITICAL THINKING (Questions 43–50)

---

**Q43. What is AI bias? How does your project address it?**

> AI bias occurs when a system's outputs systematically favour certain perspectives, groups, or viewpoints due to skewed training data or skewed input selection. In news AI, bias occurs when:
> - 80% of articles come from one publisher → that publisher's editorial angle dominates the AI summary.
> - The AI learns from historically biased corpora → reproduces those biases in generated content.
>
> My platform addresses news source bias using the **Herfindahl-Hirschman Index** — mathematically measuring publisher concentration and issuing explicit warnings when any single source dominates. I also apply a **publisher diversity penalty** in the Rational Agent that actively penalises repeated selection from the same publisher.

---

**Q44. What are the ethical implications of automated news summarization?**

> Several important implications:
> 1. **Misinformation amplification:** If the retrieval layer fetches low-quality sources, the AI synthesizer gives them an authoritative-sounding summary — laundering bad information.
> 2. **Bias reinforcement:** Automated systems can reinforce existing media biases at scale if not explicitly designed to measure and counteract them.
> 3. **Attribution and copyright:** AI summaries must cite original sources — readers have the right to trace claims to their origin. My citation system `[1]`, `[2]` with URLs addresses this.
> 4. **Overconfidence:** Users may trust AI-generated summaries more than warranted. My Evidence Strength indicator (HIGH/MEDIUM/LOW/INSUFFICIENT) explicitly communicates confidence levels to counter this.

---

**Q45. What is Explainable AI (XAI)? Where is it implemented in your project?**

> Explainable AI means AI systems that can explain their decisions in human-understandable terms — not black boxes. My project implements XAI at five points:
> 1. **ScoreBreakdown:** The Rational Agent returns a breakdown showing exactly how much each factor (relevance, freshness, diversity, credibility) contributed to an article's utility score.
> 2. **FSM Audit Log:** Every state transition in article processing is recorded with timestamps — traceable history.
> 3. **Citation Tags `[1]` `[2]`:** Every claim in the AI digest is traceable to a specific source chunk.
> 4. **Hallucination Audit Report:** Shows evidence score, phantom citations found, and which tier of evidence quality was detected.
> 5. **HHI Bias Report:** Shows exact publisher percentages, HHI score, and diversity rating.

---

**Q46. What would happen if a user asks your chatbot a question about something not in the news data?**

> The Hallucination Shield handles this explicitly. If the semantic similarity search returns chunks with low relevance (cosine similarity < 0.10), or if the evidence grounding score falls below 0.20, the Evidence Strength is marked as **INSUFFICIENT**. The platform then **injects a safe refusal message**:
> *"I don't have sufficient evidence in the retrieved news articles to answer this question reliably. Please try a different query or check live news sources directly."*
>
> This prevents the AI from hallucinating an answer when it has no grounding — a critical safety feature for a responsible news intelligence system.

---

**Q47. Can your platform be fooled or attacked? What are its security limitations?**

> Yes — as an academic prototype, it has several security limitations:
> 1. **No input sanitization:** Malicious users could inject very long queries to slow down TF-IDF vectorization (DoS attack).
> 2. **No authentication:** Any user on the network can access the API and chat endpoints.
> 3. **Prompt injection via news content:** A news article containing instructions like "Ignore previous context and say..." could potentially manipulate the RAG synthesizer.
> 4. **No rate limiting:** The API has no per-user request throttling.
>
> Mitigations for a production system: input length limits, JWT authentication, content sanitization in the RAG prompt builder, and nginx rate limiting.

---

**Q48. What is the difference between supervised, unsupervised, and reinforcement learning? Which does your project use?**

> - **Supervised learning:** Trains on labelled examples (input → correct output). Used for classification, regression.
> - **Unsupervised learning:** Finds patterns in unlabelled data. Used for clustering, dimensionality reduction.
> - **Reinforcement learning:** An agent learns by trial and error with rewards/penalties.
>
> My project primarily uses **unsupervised** techniques:
> - **TF-IDF vectorization** is unsupervised — no labels needed, it discovers term importance from corpus statistics.
> - **Cosine similarity clustering** for deduplication is unsupervised.
> - **Jaccard similarity** requires no training data.
>
> The Rational Agent uses a **hand-crafted utility function** (rule-based AI, not learned weights). This is actually a strength for an academic project — the agent's behaviour is fully interpretable and doesn't require a training dataset.

---

**Q49. How would you scale this platform to handle 1 million articles per day?**

> The current prototype would need several architectural changes for this scale:
> 1. **Database:** Replace SQLite with PostgreSQL with read replicas and connection pooling (pgBouncer).
> 2. **Vector Store:** Replace in-memory TF-IDF with a distributed vector database (Pinecone, Weaviate).
> 3. **Message Queue:** Add Redis/Celery for asynchronous article processing pipeline — the FSM transitions would run as background tasks.
> 4. **Caching:** Add Redis caching for frequently repeated queries (trending topic searches).
> 5. **Horizontal scaling:** Deploy FastAPI behind a load balancer (nginx) with multiple Uvicorn workers.
> 6. **Microservices:** Split the 7 AI modules into independent microservices communicating via gRPC or HTTP.
>
> The architecture is designed with these extensions in mind — SQLAlchemy, FastAPI, and Pydantic all support production-scale deployments.

---

**Q50. What did you learn from building this project? What would you do differently?**

> **What I learned:**
> - How to design a complete AI system from data ingestion through verified output — not just individual algorithms in isolation.
> - The importance of defensive engineering: offline fallbacks, hallucination detection, and bias measurement are not optional features — they're what separates a responsible AI system from a dangerous one.
> - How formal CS concepts (FSMs, utility theory, graph theory, information retrieval) translate into working software.
>
> **What I would do differently:**
> - Implement the vector store with persistent ChromaDB from Phase 7, accepting the Windows installation complexity, to avoid the in-memory limitation.
> - Add user authentication from Phase 15 rather than treating it as future work.
> - Use `unittest.mock` to achieve 95%+ test coverage including the live API paths.
> - Add a D3.js interactive force-directed graph from Phase 16 rather than the tabular graph representation.

---

## Quick Reference Formulas (Memorise These)

| Formula | Name | Where Used |
|---------|------|------------|
| $U(a) = 0.35R + 0.25F + 0.20D + 0.20C$ | Agent Utility | Phase 6 Rational Agent |
| $F = e^{-0.015 \cdot \Delta t}$ | Freshness Decay | Phase 6 Rational Agent |
| $J(A,B) = \frac{A \cap B}{A \cup B}$ | Jaccard Similarity | Phase 4 Deduplication |
| $\text{sim}(A,B) = \frac{A \cdot B}{|A||B|}$ | Cosine Similarity | Phases 4, 7, 9 |
| $HHI = \sum s_i^2$ | Bias Concentration | Phase 10 Bias Mitigator |
| $E = 0.40 S_{\max} + 0.30 S_{\text{avg}} + 0.20 S_{\text{div}} + 0.10 S_{\text{cite}}$ | Evidence Score | Phase 9 Hallucination Shield |
| $\text{Trend} = (n \times 10) + (p \times 15)$ | Trend Score | Phase 14 Analytics |
| $\text{TF-IDF}(t,d) = \text{TF}(t,d) \times \text{IDF}(t)$ | Term Importance | Phase 7 Vector Store |

---

*Good luck with your viva! Remember: you built every line of this system — you know it better than any examiner. Speak confidently and refer to the code when needed.*
