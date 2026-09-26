from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.schemas.news import RawArticle
from backend.app.services.news_fetcher import news_fetcher
from backend.app.services.text_processor import text_processor
from backend.app.services.rational_agent import rational_agent
from backend.app.services.vector_store import InMemoryVectorStore
from backend.app.services.rag_engine import rag_engine, GroundedDigest
from backend.app.services.hallucination_shield import hallucination_shield, HallucinationAuditReport
from backend.app.services.bias_mitigator import bias_mitigator, BiasAnalysisReport

router = APIRouter(prefix="/api/digest", tags=["AI News Digest & RAG"])

class DigestGenerationRequest(BaseModel):
    query: str = Field(..., min_length=2, description="News topic for digest synthesis")
    mode: Optional[str] = Field(default=None, description="Force 'live' or 'demo' mode")

class DigestFullResponse(BaseModel):
    digest: GroundedDigest
    audit_report: HallucinationAuditReport
    bias_report: BiasAnalysisReport

@router.post("/generate", response_model=DigestFullResponse)
def generate_ai_digest(request: DigestGenerationRequest):
    """
    Synthesizes an end-to-end AI News Intelligence Dossier:
    1. Retrieves articles via NewsFetcher
    2. Cleans & deduplicates
    3. Ranks via Rational Agent
    4. Indexes into vector store
    5. Retrieves semantic chunks & executes Grounded RAG Synthesis
    6. Verifies citations & strips hallucinations
    7. Evaluates media diversity & bias (HHI)
    """
    # 1. Fetch
    raw_res = news_fetcher.search(query=request.query, limit=10, mode=request.mode)
    
    # 2. Clean & Deduplicate
    unique_articles, _ = text_processor.deduplicate_articles(raw_res.articles)

    # 3. Agent Ranking
    ranked_tuples = rational_agent.rank_and_select(unique_articles, query=request.query, top_k=5)
    selected_articles = [a for a, _ in ranked_tuples]

    # 4. Vector Store Indexing
    store = InMemoryVectorStore()
    store.add_articles(selected_articles)

    # 5. Semantic Vector Search
    relevant_chunks = store.similarity_search(request.query, top_k=4, min_score=0.03)

    # 6. RAG Synthesis
    digest = rag_engine.synthesize_digest(request.query, relevant_chunks)

    # 7. Hallucination Shield
    raw_summary = f"{digest.executive_summary} " + " ".join(digest.key_points)
    _, audit_report = hallucination_shield.inspect_generation(raw_summary, relevant_chunks)

    # 8. Bias Analysis
    bias_report = bias_mitigator.evaluate_bias_and_diversity(selected_articles)

    return DigestFullResponse(
        digest=digest,
        audit_report=audit_report,
        bias_report=bias_report
    )

