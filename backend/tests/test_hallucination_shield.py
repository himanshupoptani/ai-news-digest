import pytest
from backend.app.services.vector_store import SearchResult, DocumentChunk
from backend.app.services.hallucination_shield import HallucinationShield, HallucinationAuditReport

def test_phantom_citation_stripping():
    # Only 2 chunks were retrieved and passed to the model
    total_chunks = 2
    raw_ai_text = "Nvidia revenue surged 150% [1]. Some analysts expect new hardware in 2030 [5]."
    
    sanitized, valid, phantoms = HallucinationShield.audit_and_sanitize_text(raw_ai_text, total_chunks)
    
    # [1] is valid, [5] is phantom and must be stripped
    assert valid == [1]
    assert phantoms == [5]
    assert "[1]" in sanitized
    assert "[5]" not in sanitized
    assert "in 2030." in sanitized

def test_evidence_strength_calculation():
    chunk1 = DocumentChunk(
        chunk_id="c1", article_title="AI Safety", source_name="Reuters",
        url="https://reuters.com", text="Content 1", chunk_index=0
    )
    chunk2 = DocumentChunk(
        chunk_id="c2", article_title="AI Treaty", source_name="Bloomberg",
        url="https://bloomberg.com", text="Content 2", chunk_index=0
    )

    results_high = [
        SearchResult(chunk=chunk1, similarity_score=0.45),
        SearchResult(chunk=chunk2, similarity_score=0.40)
    ]
    score_high, strength_high = HallucinationShield.compute_evidence_score(results_high, valid_citations=[1, 2])
    assert strength_high == "HIGH"
    assert score_high >= 0.75

    # Empty results should be INSUFFICIENT
    score_insuf, strength_insuf = HallucinationShield.compute_evidence_score([], valid_citations=[])
    assert strength_insuf == "INSUFFICIENT"
    assert score_insuf == 0.0

def test_full_hallucination_inspection_with_safe_refusal():
    chunk = DocumentChunk(
        chunk_id="c1", article_title="Low Match", source_name="Blog",
        url="https://blog.com", text="Minimal text", chunk_index=0
    )
    # Extremely low similarity (noise)
    results_low = [SearchResult(chunk=chunk, similarity_score=0.04)]
    
    speculative_text = "The secret recipe involves cinnamon [1] and saffron [9]."
    sanitized_text, report = HallucinationShield.inspect_generation(speculative_text, results_low)

    assert isinstance(report, HallucinationAuditReport)
    assert report.evidence_strength == "INSUFFICIENT"
    assert "could not find sufficient evidence" in sanitized_text.lower()
    assert report.mitigation_applied is True
