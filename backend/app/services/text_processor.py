import re
from typing import List, Tuple, Dict, Any
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.schemas.news import RawArticle

# Common English stop words for lightweight, fast set-filtering
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", 
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", 
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", 
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself"
}

class TextProcessor:
    """
    Text processing service for news intelligence:
    - HTML and boilerplate stripping
    - Jaccard similarity for headlines (with stop-word removal)
    - TF-IDF Cosine similarity for full content
    - Automated deduplication and story clustering
    """

    @staticmethod
    def clean_text(raw_html_or_text: str) -> str:
        """Strips HTML tags, scripts, non-breaking spaces, and redundant whitespace."""
        if not raw_html_or_text:
            return ""

        soup = BeautifulSoup(raw_html_or_text, "html.parser")
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()

        text = soup.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def tokenize(cls, text: str, remove_stop_words: bool = True) -> set:
        """Converts text into normalized lowercase alphanumeric word tokens."""
        tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        if remove_stop_words:
            return {t for t in tokens if len(t) > 1 and t not in STOP_WORDS}
        return {t for t in tokens if len(t) > 1}

    @classmethod
    def compute_jaccard_similarity(cls, text1: str, text2: str) -> float:
        """
        Calculates Jaccard Similarity between content-bearing words:
        J(A, B) = |A ∩ B| / |A ∪ B|
        """
        set1 = cls.tokenize(text1)
        set2 = cls.tokenize(text2)

        if not set1 or not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return float(intersection) / float(union) if union > 0 else 0.0

    @staticmethod
    def compute_tfidf_cosine_similarity(text1: str, text2: str) -> float:
        """
        Calculates Cosine Similarity in TF-IDF vector space:
        cos(θ) = (A • B) / (||A|| * ||B||)
        """
        if not text1.strip() or not text2.strip():
            return 0.0

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.0

    @classmethod
    def is_duplicate(
        cls, 
        art1: RawArticle, 
        art2: RawArticle, 
        headline_threshold: float = 0.50, 
        body_threshold: float = 0.40,
        combined_threshold: float = 0.45
    ) -> Tuple[bool, float, str]:
        """
        Determines if two articles report the exact same story.
        Returns: (is_duplicate: bool, confidence_score: float, reason: str)
        """
        # 1. Headline Jaccard similarity (filtered for key topic terms)
        h_score = cls.compute_jaccard_similarity(art1.title, art2.title)
        if h_score >= headline_threshold:
            return True, h_score, f"High headline similarity ({h_score:.2f} >= {headline_threshold})"

        # 2. Body TF-IDF Cosine similarity
        b_score = cls.compute_tfidf_cosine_similarity(art1.content, art2.content)
        if b_score >= body_threshold:
            return True, b_score, f"High content TF-IDF similarity ({b_score:.2f} >= {body_threshold})"

        # 3. Combined weighted similarity
        combined_score = (h_score * 0.5) + (b_score * 0.5)
        if combined_score >= combined_threshold:
            return True, combined_score, f"High combined semantic similarity ({combined_score:.2f} >= {combined_threshold})"

        return False, combined_score, "Articles are sufficiently unique."

    @classmethod
    def deduplicate_articles(
        cls, 
        articles: List[RawArticle], 
        similarity_threshold: float = 0.45
    ) -> Tuple[List[RawArticle], List[Dict[str, Any]]]:
        """
        Deduplicates an article list.
        Returns:
        - unique_articles: Canonical primary articles (non-duplicates)
        - duplicate_clusters: Audit list mapping canonical article to its duplicate variants
        """
        if not articles:
            return [], []

        cleaned_articles = []
        for a in articles:
            cleaned_articles.append(
                RawArticle(
                    title=cls.clean_text(a.title),
                    url=a.url,
                    source_name=a.source_name,
                    author=a.author,
                    published_at=a.published_at,
                    content=cls.clean_text(a.content),
                    category=a.category,
                    image_url=a.image_url
                )
            )

        unique_articles: List[RawArticle] = []
        duplicate_clusters: List[Dict[str, Any]] = []

        for candidate in cleaned_articles:
            matched_duplicate = False
            for primary in unique_articles:
                is_dup, score, reason = cls.is_duplicate(
                    candidate, 
                    primary, 
                    combined_threshold=similarity_threshold
                )
                if is_dup:
                    matched_duplicate = True
                    duplicate_clusters.append({
                        "primary_title": primary.title,
                        "primary_url": primary.url,
                        "primary_source": primary.source_name,
                        "duplicate_title": candidate.title,
                        "duplicate_url": candidate.url,
                        "duplicate_source": candidate.source_name,
                        "similarity_score": round(score, 3),
                        "reason": reason
                    })
                    break

            if not matched_duplicate:
                unique_articles.append(candidate)

        return unique_articles, duplicate_clusters

text_processor = TextProcessor()
