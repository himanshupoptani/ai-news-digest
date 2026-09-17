import re
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel

from backend.app.schemas.news import RawArticle
from backend.app.services.text_processor import TextProcessor

class BiasAnalysisReport(BaseModel):
    """Explainable media diversity and bias mitigation audit report."""
    source_distribution: Dict[str, float]  # e.g. {"Reuters": 33.3, "Bloomberg": 33.3, "BBC": 33.3}
    dominant_source: Optional[str] = None
    hhi_score: float  # Herfindahl-Hirschman Index (0 - 10,000)
    diversity_rating: str  # 'OPTIMAL', 'MODERATE', or 'CONCENTRATED'
    warning: Optional[str] = None
    consensus_points: List[str]
    divergent_points: List[str]

class BiasMitigator:
    """
    Algorithmic Bias Mitigation Engine:
    - Analyzes publisher market-share distribution
    - Calculates Herfindahl-Hirschman Index (HHI) to detect media monopolies
    - Issues transparent single-source dominance alerts
    - Extracts multi-source consensus vs. editorial divergence
    """

    @classmethod
    def compute_source_distribution(cls, articles: List[RawArticle]) -> Dict[str, float]:
        """Calculates percentage share of each publisher in the selected pool."""
        if not articles:
            return {}

        counts: Dict[str, int] = {}
        for art in articles:
            name = art.source_name or "Unknown Source"
            counts[name] = counts.get(name, 0) + 1

        total = len(articles)
        distribution = {
            source: round((count / total) * 100.0, 1)
            for source, count in counts.items()
        }
        return distribution

    @staticmethod
    def calculate_hhi(distribution: Dict[str, float]) -> float:
        """
        Calculates Herfindahl-Hirschman Index (HHI):
        HHI = Sum of squared market shares (s_i^2).
        Max score = 10,000 (100% single-source monopoly).
        """
        if not distribution:
            return 0.0
        return round(sum(share ** 2 for share in distribution.values()), 1)

    @classmethod
    def extract_consensus_and_divergence(
        cls, 
        articles: List[RawArticle]
    ) -> Tuple[List[str], List[str]]:
        """
        Cross-examines articles from distinct publishers to discover:
        - Points of Consensus: Facts shared by multiple newsrooms
        - Points of Divergence: Unique numbers, claims, or editorial angles
        """
        if len(articles) < 2:
            return (
                ["Single article coverage: Multiple sources required to evaluate consensus."],
                []
            )

        # Collect distinct sentences across all articles
        publisher_sentences: Dict[str, List[str]] = {}
        for art in articles:
            sentences = [
                s.strip() for s in re.split(r"(?<=[.!?])\s+", art.content) 
                if len(s.strip()) > 20
            ]
            if not sentences and art.content.strip():
                sentences = [art.content.strip()]
            publisher_sentences[art.source_name] = sentences

        publishers = list(publisher_sentences.keys())
        consensus: List[str] = []
        divergent: List[str] = []

        # Compare sentences across pairs of publishers using Jaccard token overlap
        found_matches = set()
        for i in range(len(publishers)):
            for j in range(i + 1, len(publishers)):
                p1, p2 = publishers[i], publishers[j]
                for s1 in publisher_sentences[p1]:
                    for s2 in publisher_sentences[p2]:
                        sim = TextProcessor.compute_jaccard_similarity(s1, s2)
                        # An overlap >= 0.28 on non-stop words indicates factual consensus
                        if sim >= 0.28 and s1 not in found_matches:
                            consensus.append(f"Both {p1} and {p2} confirm: {s1}")
                            found_matches.add(s1)
                            found_matches.add(s2)
                            break

        # Collect unique insights from individual publishers
        for pub, sentences in publisher_sentences.items():
            for s in sentences:
                if s not in found_matches and len(divergent) < 3:
                    divergent.append(f"{pub} uniquely highlights: {s}")

        if not consensus:
            consensus.append("No verbatim factual overlap detected across available excerpts.")

        return consensus[:3], divergent[:3]

    @classmethod
    def evaluate_bias_and_diversity(cls, articles: List[RawArticle]) -> BiasAnalysisReport:
        """
        Full Bias Mitigation Pipeline:
        Analyzes source distribution, computes HHI, and formats alerts.
        """
        distribution = cls.compute_source_distribution(articles)
        hhi = cls.calculate_hhi(distribution)

        dominant_source = None
        warning = None

        # Check for single-source dominance (>= 60%)
        for source, share in distribution.items():
            if share >= 60.0 and len(articles) > 1:
                dominant_source = source
                warning = (
                    f"BIAS ALERT: {share:.0f}% of retrieved intelligence originates from a single publisher ({source}). "
                    f"We recommend reviewing additional independent outlets to ensure balanced perspective."
                )
                break

        # Classify diversity rating based on HHI
        # For a 3-source pool with equal share (33.3% each), HHI = ~3333 -> OPTIMAL
        if hhi <= 3500 and len(distribution) >= 3:
            diversity_rating = "OPTIMAL"
        elif hhi <= 5000:
            diversity_rating = "MODERATE"
        else:
            diversity_rating = "CONCENTRATED"
            if not warning and len(articles) > 1:
                warning = "High publisher concentration detected. Consider expanding search queries."

        consensus, divergent = cls.extract_consensus_and_divergence(articles)

        return BiasAnalysisReport(
            source_distribution=distribution,
            dominant_source=dominant_source,
            hhi_score=hhi,
            diversity_rating=diversity_rating,
            warning=warning,
            consensus_points=consensus,
            divergent_points=divergent
        )

# Singleton instance
bias_mitigator = BiasMitigator()

