import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

from backend.app.schemas.news import RawArticle
from backend.app.services.text_processor import TextProcessor

class ScoreBreakdown(BaseModel):
    """Explainable breakdown of how the Rational Agent computed the final utility score."""
    relevance_score: float
    freshness_score: float
    diversity_score: float
    credibility_score: float
    final_score: float

class RationalNewsAgent:
    """
    PEAS Rational Agent for News Intelligence.
    Optimizes multi-objective utility:
    Score = (w_rel * Rel) + (w_fresh * Fresh) + (w_div * Div) + (w_cred * Cred) - DuplicatePenalty
    """

    # Weights configured to prioritize accuracy and freshness while enforcing diversity
    WEIGHT_RELEVANCE = 0.35
    WEIGHT_FRESHNESS = 0.25
    WEIGHT_DIVERSITY = 0.20
    WEIGHT_CREDIBILITY = 0.20

    # Source credibility lookups
    KNOWN_CREDIBILITY = {
        "Reuters": 0.96,
        "Associated Press": 0.96,
        "BBC News": 0.93,
        "BBC Tech": 0.93,
        "Bloomberg": 0.94,
        "MIT Tech Review": 0.94,
        "TechCrunch": 0.88,
        "Ars Technica": 0.89,
        "Wired": 0.87,
    }

    @classmethod
    def calculate_relevance(cls, article: RawArticle, query: str) -> float:
        """Computes semantic relevance between query and article headline/content."""
        if not query.strip():
            return 0.5

        query_tokens = TextProcessor.tokenize(query)
        if not query_tokens:
            return 0.5

        title_tokens = TextProcessor.tokenize(article.title)
        content_tokens = TextProcessor.tokenize(article.content)

        # Title matches carry higher weight (3x) than body matches
        title_matches = len(query_tokens.intersection(title_tokens))
        content_matches = len(query_tokens.intersection(content_tokens))

        title_score = min(1.0, title_matches / len(query_tokens))
        content_score = min(1.0, content_matches / len(query_tokens))

        return round((title_score * 0.7) + (content_score * 0.3), 3)

    @staticmethod
    def calculate_freshness(published_at_str: str) -> float:
        """
        Calculates freshness using an exponential decay function:
        S_fresh = e^(-λ * Δt), where λ = 0.015 (half-life ≈ 46 hours)
        """
        if not published_at_str:
            return 0.5  # Neutral default if timestamp is missing

        try:
            # Handle ISO formats
            clean_ts = published_at_str.replace("Z", "+00:00")
            pub_time = datetime.fromisoformat(clean_ts)
            now = datetime.now(timezone.utc)
            delta_hours = max(0.0, (now - pub_time).total_seconds() / 3600.0)

            # Exponential decay formula
            decay_constant = 0.015
            freshness = math.exp(-decay_constant * delta_hours)
            return round(max(0.05, min(1.0, freshness)), 3)
        except Exception:
            return 0.5

    @classmethod
    def calculate_diversity(cls, source_name: str, selected_sources: List[str]) -> float:
        """
        Awards a diversity bonus to new, unrepresented publishers in the current selection pool.
        Penalizes publisher overconcentration.
        """
        if not selected_sources:
            return 1.0  # First article gets maximum diversity incentive

        count = selected_sources.count(source_name)
        if count == 0:
            return 1.0  # Novel publisher
        elif count == 1:
            return 0.6  # Second article from same publisher
        elif count == 2:
            return 0.3  # Third article from same publisher
        else:
            return 0.1  # Heavy penalty for 4+ articles from same publisher

    @classmethod
    def calculate_credibility(cls, source_name: str) -> float:
        """Retrieves credibility rating for the publishing outlet."""
        return cls.KNOWN_CREDIBILITY.get(source_name, 0.80)

    @classmethod
    def rank_and_select(
        cls, 
        articles: List[RawArticle], 
        query: str, 
        top_k: int = 5
    ) -> List[Tuple[RawArticle, ScoreBreakdown]]:
        """
        Autonomous Agent Selection Loop:
        Iteratively selects the article that provides the highest marginal utility,
        updating the publisher diversity context after each selection.
        """
        if not articles:
            return []

        remaining = list(articles)
        selected_results: List[Tuple[RawArticle, ScoreBreakdown]] = []
        selected_source_names: List[str] = []

        while remaining and len(selected_results) < top_k:
            best_candidate = None
            best_score = -1.0
            best_breakdown = None
            best_idx = -1

            for idx, candidate in enumerate(remaining):
                rel = cls.calculate_relevance(candidate, query)
                fresh = cls.calculate_freshness(candidate.published_at)
                div = cls.calculate_diversity(candidate.source_name, selected_source_names)
                cred = cls.calculate_credibility(candidate.source_name)

                # Multi-objective utility calculation
                final_utility = (
                    (cls.WEIGHT_RELEVANCE * rel) +
                    (cls.WEIGHT_FRESHNESS * fresh) +
                    (cls.WEIGHT_DIVERSITY * div) +
                    (cls.WEIGHT_CREDIBILITY * cred)
                )

                if final_utility > best_score:
                    best_score = final_utility
                    best_candidate = candidate
                    best_idx = idx
                    best_breakdown = ScoreBreakdown(
                        relevance_score=round(rel, 3),
                        freshness_score=round(fresh, 3),
                        diversity_score=round(div, 3),
                        credibility_score=round(cred, 3),
                        final_score=round(final_utility, 3)
                    )

            if best_candidate and best_breakdown:
                selected_results.append((best_candidate, best_breakdown))
                selected_source_names.append(best_candidate.source_name)
                remaining.pop(best_idx)
            else:
                break

        return selected_results

# Singleton instance
rational_agent = RationalNewsAgent()

