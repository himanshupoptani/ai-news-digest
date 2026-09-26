import re
import json
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.schemas.chat import ChatTurnRequest, ChatTurnResponse, ChatMessageDTO
from backend.app.services.news_fetcher import news_fetcher
from backend.app.services.text_processor import text_processor
from backend.app.services.vector_store import InMemoryVectorStore
from backend.app.services.rag_engine import rag_engine, GroundedCitation
from backend.app.services.hallucination_shield import hallucination_shield, HallucinationAuditReport

logger = logging.getLogger(__name__)

# Trigger words indicating that the query is a conversational follow-up
FOLLOWUP_TRIGGERS = {
    "it", "they", "this", "that", "these", "those", "he", "she", "why", 
    "how", "what else", "which sources", "before", "after", "who else", 
    "compare", "did they", "was it", "explain more"
}

class ChatbotService:
    """
    Enterprise Conversational News Research Chatbot Service:
    - Multi-turn SQLite session persistence
    - Pronoun and conversational context resolution (Query Rewriter)
    - Full 14-stage RAG retrieval, grounded synthesis, and hallucination inspection
    """

    @staticmethod
    def get_or_create_session(session_id: Optional[int], first_message: str, db: Session) -> ChatSession:
        """Retrieves an existing chat session or creates a new one with a descriptive title."""
        if session_id:
            session = db.query(ChatSession).filter_by(id=session_id).first()
            if session:
                return session

        # Create new session
        title = first_message[:40] + "..." if len(first_message) > 40 else first_message
        new_session = ChatSession(title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    @classmethod
    def resolve_query_context(cls, current_message: str, history: List[ChatMessage]) -> str:
        """
        Anaphora Resolution / Query Rewriter:
        Detects if current question is a follow-up referring to previous turns,
        and rewrites it into an explicit, standalone semantic search query.
        """
        clean_msg = current_message.strip().lower()
        words = set(re.findall(r"\b[a-zA-Z]+\b", clean_msg))

        # If no history exists, return message as is
        if not history:
            return current_message

        # Check if any follow-up trigger word is present or query is very brief (< 4 words)
        is_followup = bool(words.intersection(FOLLOWUP_TRIGGERS)) or len(words) < 4

        if not is_followup:
            return current_message

        # Extract topic/entities from the most recent user and assistant messages
        last_user_turn = None
        for msg in reversed(history):
            if msg.role == "user":
                last_user_turn = msg.content
                break

        if not last_user_turn:
            return current_message

        # Extract key content words from previous query (excluding basic query words)
        prev_tokens = text_processor.tokenize(last_user_turn, remove_stop_words=True)
        topic_anchor = " ".join(list(prev_tokens)[:4])

        # Formulate standalone rewritten query
        rewritten = f"{topic_anchor} {current_message}".strip()
        logger.info(f"Query rewritten: '{current_message}' -> '{rewritten}'")
        return rewritten

    @classmethod
    def ask(cls, request: ChatTurnRequest, db: Session) -> ChatTurnResponse:
        """
        Executes the 14-Stage Conversational Intelligence Pipeline:
        1. Retrieve / Create Session
        2. Fetch conversation history
        3. Rewrite query for context resolution
        4. Retrieve live/sample news via NewsFetcher
        5. Clean and index news into isolated session vector store
        6. Perform Cosine Similarity Search
        7. Synthesize grounded answer via RAGEngine
        8. Pass through HallucinationShield
        9. Persist messages to SQLite
        10. Return response with verified citations
        """
        # 1. Get or create session
        session = cls.get_or_create_session(request.session_id, request.message, db)

        # 2. Get past history for context resolution
        history = db.query(ChatMessage).filter_by(session_id=session.id).order_by(ChatMessage.created_at.asc()).all()

        # 3. Save incoming user message to DB
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.message,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user_msg)
        db.commit()

        # 4. Resolve query context
        rewritten_query = cls.resolve_query_context(request.message, history)

        # 5. Retrieve news based on rewritten query
        search_res = news_fetcher.search(query=rewritten_query, limit=10)
        raw_articles = search_res.articles

        # 6. Index into isolated vector store
        session_vector_store = InMemoryVectorStore()
        session_vector_store.add_articles(raw_articles)

        # 7. Semantic Vector Search
        relevant_chunks = session_vector_store.similarity_search(rewritten_query, top_k=4, min_score=0.03)

        # 8. Synthesize grounded answer via RAGEngine
        digest = rag_engine.synthesize_digest(rewritten_query, relevant_chunks)

        # 9. Hallucination Shield Verification
        raw_answer = f"{digest.executive_summary} " + " ".join(digest.key_points)
        sanitized_answer, audit_report = hallucination_shield.inspect_generation(raw_answer, relevant_chunks)

        # 10. Persist Assistant Response in SQLite
        citations_json = json.dumps([c.model_dump() for c in digest.citations])
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=sanitized_answer,
            citations=citations_json,
            evidence_strength=audit_report.evidence_strength,
            created_at=datetime.now(timezone.utc)
        )
        db.add(assistant_msg)
        db.commit()

        return ChatTurnResponse(
            session_id=session.id,
            original_query=request.message,
            rewritten_query=rewritten_query,
            role="assistant",
            content=sanitized_answer,
            citations=digest.citations,
            evidence_strength=audit_report.evidence_strength,
            audit_report=audit_report
        )

# Singleton instance
chatbot_service = ChatbotService()

