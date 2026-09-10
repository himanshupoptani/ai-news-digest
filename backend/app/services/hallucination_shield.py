import re
from typing import List, Tuple, Dict, Any, Set
from pydantic import BaseModel

from backend.app.services.vector_store import SearchResult

class HallucinationAuditReport(BaseModel):
    """Explainable Trustworthy AI audit report for the user and viva defense."""
    is_grounded: bool
    evidence_score: float  # 0.0 to 1.0 (0% to 100%)
    evidence_strength: str  # 'HIGH', 'MEDIUM', 'LOW', or 'INSUFFICIENT'
    valid_citations: List[int]
    phantom_citations_removed: List[int]
    warnings: List[str]
    mitigation_applied: bool

class HallucinationShield:
    """
    Enterprise Hallucination Mitigation Engine:
    - Verifies citation integrity against actual retrieved chunks
    - Detects and strips phantom/hallucinated citation badges
    - Computes a mathematical Evidence Strength score
    - Enforces safe refusal when evidence is insufficient
    """

    CITATION_PATTERN = re.compile(r"\[(\d+)\]")

    @classmethod
    def extract_citations(cls, text: str) -> List[int]:
        """Extracts all bracketed integer citation indices from text."""
        matches = cls.CITATION_PATTERN.findall(text)
        return [int(m) for m in matches]

    @classmethod
    def audit_and_sanitize_text(
        cls, 
        text: str, 
        total_chunks_provided: int
    ) -> Tuple[str, List[int], List[int]]:
        """
        Scrutinizes text for phantom citations.
        If the AI cites [5] when only 2 chunks were provided, [5] is stripped.
        Returns: (sanitized_text, valid_citations, phantom_citations_removed)
        """
        if not text:
            return "", [], []

        raw_citations = cls.extract_citations(text)
        valid_citations: List[int] = []
        phantom_citations: List[int] = []

        for cit in raw_citations:
            if 1 <= cit <= total_chunks_provided:
                if cit not in valid_citations:
                    valid_citations.append(cit)
            else:
                if cit not in phantom_citations:
                    phantom_citations.append(cit)

        # Sanitize text by removing phantom citations and cleaning up spacing before punctuation
        sanitized_text = text
        for phantom in phantom_citations:
            pattern = re.compile(r"\s*\[" + str(phantom) + r"\]")
            sanitized_text = pattern.sub("", sanitized_text)

        # Fix punctuation spacing: e.g. "in 2030 ." -> "in 2030."
        sanitized_text = re.sub(r"\s+([.,!?;])", r"\1", sanitized_text)
        sanitized_text = re.sub(r"\s+", " ", sanitized_text).strip()

        return sanitized_text, valid_citations, phantom_citations

    @classmethod
    def compute_evidence_score(
        cls, 
        search_results: List[SearchResult], 
        valid_citations: List[int]
    ) -> Tuple[float, str]:
        """
        Computes the objective Evidence Strength Score:
        Score = (0.40 * MaxSim) + (0.30 * AvgSim) + (0.20 * SourceDiversity) + (0.10 * CitationCoverage)
        """
        if not search_results:
            return 0.0, "INSUFFICIENT"

        scores = [r.similarity_score for r in search_results]
        max_sim = max(scores)
        
        # Hard gate: If the best chunk has negligible similarity (< 0.10), evidence is insufficient
        if max_sim < 0.10:
            return round(max_sim, 3), "INSUFFICIENT"

        avg_sim = sum(scores) / len(scores)

        # Unique publishers among retrieved chunks
        sources = {r.chunk.source_name for r in search_results}
        diversity_ratio = min(1.0, len(sources) / 2.0)  # 2+ sources gives maximum diversity

        # Citation coverage ratio
        citation_ratio = min(1.0, len(valid_citations) / max(1, len(search_results)))

        # Weighted calculation
        raw_score = (
            (0.40 * max_sim) +
            (0.30 * avg_sim) +
            (0.20 * diversity_ratio) +
            (0.10 * citation_ratio)
        )

        # Normalize score into a friendly 0.0 - 1.0 range
        evidence_score = round(min(1.0, max(0.0, raw_score * 1.8)), 3)

        if evidence_score >= 0.75:
            strength = "HIGH"
        elif evidence_score >= 0.45:
            strength = "MEDIUM"
        elif evidence_score >= 0.20:
            strength = "LOW"
        else:
            strength = "INSUFFICIENT"

        return evidence_score, strength

    @classmethod
    def inspect_generation(
        cls, 
        generated_text: str, 
        search_results: List[SearchResult]
    ) -> Tuple[str, HallucinationAuditReport]:
        """
        Full Hallucination Inspection Pipeline:
        1. Sanitizes phantom citations
        2. Computes evidence strength
        3. Generates transparent audit report
        4. Injects safe refusal if evidence is insufficient
        """
        total_chunks = len(search_results)
        sanitized_text, valid_cits, phantoms = cls.audit_and_sanitize_text(generated_text, total_chunks)
        score, strength = cls.compute_evidence_score(search_results, valid_cits)

        warnings = []
        mitigation_applied = False

        if phantoms:
            warnings.append(f"Detected and stripped {len(phantoms)} hallucinated phantom citations: {[f'[{p}]' for p in phantoms]}.")
            mitigation_applied = True

        if strength == "INSUFFICIENT":
            sanitized_text = "I could not find sufficient evidence in the retrieved news sources to answer this reliably."
            warnings.append("Evidence threshold not met. Replaced speculative text with safe refusal.")
            mitigation_applied = True
        elif strength == "LOW":
            warnings.append("Low evidence confidence: Coverage is based on limited or single-source information.")

        report = HallucinationAuditReport(
            is_grounded=(strength in ["HIGH", "MEDIUM"]),
            evidence_score=score,
            evidence_strength=strength,
            valid_citations=valid_cits,
            phantom_citations_removed=phantoms,
            warnings=warnings,
            mitigation_applied=mitigation_applied
        )

        return sanitized_text, report

# Singleton instance
hallucination_shield = HallucinationShield()
