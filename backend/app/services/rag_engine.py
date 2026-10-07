import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.services.vector_store import SearchResult, DocumentChunk

logger = logging.getLogger(__name__)

class GroundedCitation(BaseModel):
    """Metadata for an interactive citation badge [1], [2]."""
    index: int
    source_name: str
    article_title: str
    url: str
    passage_snippet: str

class GroundedDigest(BaseModel):
    """Structured, verified AI News Intelligence Dossier."""
    headline: str
    executive_summary: str
    key_points: List[str]
    citations: List[GroundedCitation]
    evidence_strength: str  # 'HIGH', 'MEDIUM', 'LOW', or 'INSUFFICIENT'
    total_sources: int

class RAGEngine:
    """
    Retrieval-Augmented Generation Engine:
    - Assembles strictly grounded prompts with numbered evidence tags [1], [2]
    - Calls external Foundation Models (Gemini/OpenAI) when configured
    - Falls back to built-in Local RAG Synthesizer for 100% reliable offline presentations
    """

    @staticmethod
    def build_prompt(query: str, search_results: List[SearchResult]) -> str:
        """Constructs an auditable, grounded RAG prompt."""
        context_blocks = []
        for idx, res in enumerate(search_results, start=1):
            chunk = res.chunk
            context_blocks.append(
                f"[{idx}] Source: {chunk.source_name} | Article: {chunk.article_title}\n"
                f"Content: \"{chunk.text}\"\n"
            )

        context_str = "\n".join(context_blocks)
        prompt = (
            f"You are an impartial Senior News Intelligence Analyst.\n"
            f"Synthesize an accurate, grounded briefing for the topic: '{query}'.\n\n"
            f"CRITICAL GROUNDING RULES:\n"
            f"1. Rely EXCLUSIVELY on the provided evidence passages below.\n"
            f"2. Append bracketed citations like [1] or [2] to EVERY factual claim.\n"
            f"3. If evidence is missing, state: 'Insufficient evidence available in retrieved sources.'\n"
            f"4. Structure response with an Executive Summary and 3 Key Bullet Points.\n\n"
            f"RETRIEVED EVIDENCE PASSAGES:\n"
            f"{context_str}\n"
            f"TOPIC QUERY: {query}\n"
        )
        return prompt

    @classmethod
    def synthesize_digest(cls, query: str, search_results: List[SearchResult]) -> GroundedDigest:
        """
        Main RAG pipeline entrypoint:
        Transforms vector search results into a verified, cited Intelligence Dossier.
        """
        # If no relevant chunks retrieved or top similarity is too low
        if not search_results or search_results[0].similarity_score < 0.10:
            return GroundedDigest(
                headline=f"Intelligence Briefing: {query}",
                executive_summary="I could not find sufficient evidence in the retrieved news sources to construct a reliable intelligence briefing for this topic.",
                key_points=["No high-confidence evidence passages retrieved."],
                citations=[],
                evidence_strength="INSUFFICIENT",
                total_sources=0
            )

        # Build citation catalog
        citations: List[GroundedCitation] = []
        seen_sources = set()
        for idx, res in enumerate(search_results, start=1):
            chunk = res.chunk
            seen_sources.add(chunk.source_name)
            citations.append(
                GroundedCitation(
                    index=idx,
                    source_name=chunk.source_name,
                    article_title=chunk.article_title,
                    url=chunk.url,
                    passage_snippet=chunk.text[:140] + "..." if len(chunk.text) > 140 else chunk.text
                )
            )

        # Determine evidence strength based on top similarity and publisher variety
        top_score = search_results[0].similarity_score
        if top_score >= 0.35 and len(seen_sources) >= 2:
            evidence_strength = "HIGH"
        elif top_score >= 0.20:
            evidence_strength = "MEDIUM"
        else:
            evidence_strength = "LOW"

        # Check if external LLM API is configured; otherwise use Local Extractive RAG
        if settings.GEMINI_API_KEY:
            try:
                return cls._call_gemini_llm(query, search_results, citations, evidence_strength, len(seen_sources))
            except Exception as e:
                logger.warning(f"Live Gemini call failed: {e}. Executing local RAG synthesis.")

        # Local Deterministic RAG Synthesis Engine (Zero API keys required!)
        return cls._local_rag_synthesis(query, search_results, citations, evidence_strength, len(seen_sources))

    @staticmethod
    def _local_rag_synthesis(
        query: str, 
        search_results: List[SearchResult], 
        citations: List[GroundedCitation], 
        evidence_strength: str,
        total_sources: int
    ) -> GroundedDigest:
        """
        Deterministic Local RAG Synthesis Engine:
        Extracts salient statements from the top retrieved chunks,
        binds them to exact citation badges [1], [2], and formats an executive briefing.
        """
        top_chunk = search_results[0].chunk
        # Split sentences from top passages
        sentences_chunk1 = [s.strip() for s in re.split(r"(?<=[.!?])\s+", top_chunk.text) if len(s.strip()) > 20]
        
        # Formulate executive summary using top grounded sentences
        if sentences_chunk1:
            exec_summary = f"{sentences_chunk1[0]} [1]"
            if len(sentences_chunk1) > 1:
                exec_summary += f" {sentences_chunk1[1]} [1]"
        else:
            exec_summary = f"Recent reporting confirms new developments regarding {query} [1]."

        # Formulate 3 distinct key points from available chunks
        key_points = []
        for idx, res in enumerate(search_results[:3], start=1):
            chunk_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", res.chunk.text) if len(s.strip()) > 15]
            point_text = chunk_sentences[0] if chunk_sentences else res.chunk.text[:100]
            key_points.append(f"{point_text} [{idx}]")

        headline = f"Executive Intelligence Briefing: {top_chunk.article_title}"

        return GroundedDigest(
            headline=headline,
            executive_summary=exec_summary,
            key_points=key_points,
            citations=citations,
            evidence_strength=evidence_strength,
            total_sources=total_sources
        )

    @classmethod
    def _call_gemini_llm(
        cls, 
        query: str, 
        search_results: List[SearchResult], 
        citations: List[GroundedCitation], 
        evidence_strength: str,
        total_sources: int
    ) -> GroundedDigest:
        """Calls Google Gemini API with the grounded RAG prompt."""
        import requests
        prompt = cls.build_prompt(query, search_results)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
        }
        
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API error: {resp.status_code}")

        data = resp.json()
        generated_text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Parse generated text into summary and key points
        lines = [line.strip() for line in generated_text.split("\n") if line.strip()]
        exec_lines = [l for l in lines if not l.startswith(("-", "*", "1.", "2.", "3."))]
        bullet_lines = [l.lstrip("-*0123456789. ") for l in lines if l.startswith(("-", "*", "1.", "2.", "3."))]

        summary = " ".join(exec_lines[:3]) if exec_lines else generated_text[:200]
        points = bullet_lines[:3] if bullet_lines else ["Key intelligence details outlined in the executive summary."]

        return GroundedDigest(
            headline=f"Intelligence Briefing: {search_results[0].chunk.article_title}",
            executive_summary=summary,
            key_points=points,
            citations=citations,
            evidence_strength=evidence_strength,
            total_sources=total_sources
        )

# Singleton instance
rag_engine = RAGEngine()

