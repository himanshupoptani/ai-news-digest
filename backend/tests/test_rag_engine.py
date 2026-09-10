import pytest
from backend.app.services.vector_store import SearchResult, DocumentChunk
from backend.app.services.rag_engine import RAGEngine, GroundedDigest, GroundedCitation

@pytest.fixture
def sample_search_results():
    chunk1 = DocumentChunk(
        chunk_id="chk_1",
        article_title="Nvidia Blackwell GPU Ramp Begins",
        source_name="Reuters",
        url="https://reuters.com/nvidia-blackwell",
        text="Nvidia commenced mass production of its Blackwell GPUs, recording 30 billion dollars in data center sales.",
        chunk_index=0
    )
    chunk2 = DocumentChunk(
        chunk_id="chk_2",
        article_title="AI Infrastructure Spending Hits Record Heights",
        source_name="Bloomberg",
        url="https://bloomberg.com/ai-infra",
        text="Hyperscale cloud providers confirmed 50 billion in ongoing capital investments into AI accelerators.",
        chunk_index=0
    )

    return [
        SearchResult(chunk=chunk1, similarity_score=0.42),
        SearchResult(chunk=chunk2, similarity_score=0.38)
    ]

def test_build_rag_prompt_structure(sample_search_results):
    prompt = RAGEngine.build_prompt("Nvidia Blackwell chips", sample_search_results)
    
    assert "You are an impartial Senior News Intelligence Analyst" in prompt
    assert "[1] Source: Reuters" in prompt
    assert "[2] Source: Bloomberg" in prompt
    assert "TOPIC QUERY: Nvidia Blackwell chips" in prompt

def test_synthesize_digest_grounded_output(sample_search_results):
    digest = RAGEngine.synthesize_digest("Nvidia Blackwell chips", sample_search_results)
    
    assert isinstance(digest, GroundedDigest)
    assert digest.evidence_strength == "HIGH"
    assert digest.total_sources == 2
    assert len(digest.citations) == 2
    
    # Check citation metadata
    first_citation = digest.citations[0]
    assert isinstance(first_citation, GroundedCitation)
    assert first_citation.source_name == "Reuters"
    assert "reuters.com" in first_citation.url

    # Check that output contains inline bracketed citations [1] or [2]
    assert "[1]" in digest.executive_summary or "[1]" in " ".join(digest.key_points)

def test_insufficient_evidence_fallback():
    # When no results found or similarity too low
    empty_digest = RAGEngine.synthesize_digest("Unicorn sightings in Atlantis", [])
    
    assert empty_digest.evidence_strength == "INSUFFICIENT"
    assert "could not find sufficient evidence" in empty_digest.executive_summary.lower()
    assert len(empty_digest.citations) == 0

