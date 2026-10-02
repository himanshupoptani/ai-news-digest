import re
import json
import logging
import requests
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.schemas.chat import ChatTurnRequest, ChatTurnResponse, ChatMessageDTO
from backend.app.services.news_fetcher import news_fetcher
from backend.app.services.text_processor import text_processor
from backend.app.services.vector_store import InMemoryVectorStore
from backend.app.services.rag_engine import rag_engine, GroundedCitation, GroundedDigest
from backend.app.services.hallucination_shield import hallucination_shield, HallucinationAuditReport
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Trigger words indicating that the query is a conversational follow-up
FOLLOWUP_TRIGGERS = {
    "it", "they", "this", "that", "these", "those", "he", "she", "why",
    "how", "what else", "which sources", "before", "after", "who else",
    "compare", "did they", "was it", "explain more", "tell me more",
    "more about", "elaborate", "details", "what happened"
}

# Suggested conversation starters
SUGGESTED_PROMPTS = [
    "What is the latest news on AI and large language models?",
    "What are the biggest tech stories this week?",
    "Summarize the latest business and market developments",
    "What are the latest developments with OpenAI?",
    "What happened in the science world recently?",
    "Give me a briefing on global economic news",
    "What are the trending topics in technology right now?",
    "Explain the latest developments in India and global tech",
]


class ChatbotService:
    """
    Enterprise-grade Conversational News Research Chatbot:
    - Multi-turn SQLite session persistence
    - Full conversation context passed to Gemini LLM
    - Gemini-powered natural language responses with inline citations
    - Suggested follow-up question generation
    - Pronoun and conversational context resolution (Query Rewriter)
    - 100% grounded — all answers sourced from live news
    """

    @staticmethod
    def get_or_create_session(session_id: Optional[int], first_message: str, db: Session) -> ChatSession:
        """Retrieves an existing chat session or creates a new one."""
        if session_id:
            session = db.query(ChatSession).filter_by(id=session_id).first()
            if session:
                return session
        title = first_message[:50] + "..." if len(first_message) > 50 else first_message
        new_session = ChatSession(title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    @classmethod
    def resolve_query_context(cls, current_message: str, history: List[ChatMessage]) -> str:
        """
        Anaphora Resolution / Query Rewriter:
        Detects follow-up questions and rewrites them into explicit standalone queries.
        """
        clean_msg = current_message.strip().lower()
        words = set(re.findall(r"\b[a-zA-Z]+\b", clean_msg))

        if not history:
            return current_message

        is_followup = bool(words.intersection(FOLLOWUP_TRIGGERS)) or len(words) < 4

        if not is_followup:
            return current_message

        last_user_turn = None
        for msg in reversed(history):
            if msg.role == "user":
                last_user_turn = msg.content
                break

        if not last_user_turn:
            return current_message

        prev_tokens = text_processor.tokenize(last_user_turn, remove_stop_words=True)
        topic_anchor = " ".join(list(prev_tokens)[:5])
        rewritten = f"{topic_anchor} {current_message}".strip()
        logger.info(f"Query rewritten: '{current_message}' -> '{rewritten}'")
        return rewritten

    @classmethod
    def _build_conversation_prompt(
        cls,
        query: str,
        search_results,
        history: List[ChatMessage]
    ) -> str:
        """
        Builds a rich conversational Gemini prompt that:
        - Includes the full conversation history for true multi-turn context
        - Passes all retrieved news evidence with numbered citations
        - Instructs Gemini to respond naturally like a knowledgeable news analyst
        - Asks for 3 follow-up question suggestions
        """
        context_blocks = []
        for idx, res in enumerate(search_results, start=1):
            chunk = res.chunk
            context_blocks.append(
                f"[{idx}] SOURCE: {chunk.source_name}\n"
                f"    HEADLINE: {chunk.article_title}\n"
                f"    CONTENT: \"{chunk.text[:300]}\"\n"
                f"    URL: {chunk.url}\n"
            )
        context_str = "\n".join(context_blocks)

        history_str = ""
        recent = [m for m in history if m.role in ("user", "assistant")][-8:]
        if recent:
            history_str = "\n--- CONVERSATION HISTORY ---\n"
            for msg in recent:
                prefix = "User" if msg.role == "user" else "Assistant"
                history_str += f"{prefix}: {msg.content[:200]}\n"
            history_str += "---\n"

        prompt = f"""You are an expert AI News Intelligence Assistant with deep knowledge of global news, finance, technology, politics, and science.

Your personality: Sharp, insightful, concise. You answer like a senior Bloomberg analyst — factual, direct, and engaging.

{history_str}

LIVE NEWS EVIDENCE RETRIEVED FOR THIS QUERY:
{context_str}

CURRENT USER QUESTION: {query}

STRICT INSTRUCTIONS:
1. Answer the user's question directly and conversationally. Do NOT start with "I" — start with the most important fact.
2. Use ONLY the evidence above. Cite every fact with its source number like [1], [2].
3. Write 2-4 sentences for the main answer. Be concise but informative.
4. If the user asks a follow-up from history, reference that context naturally.
5. After your answer, add a blank line then write exactly:
   FOLLOW_UPS:
   - [follow-up question 1]
   - [follow-up question 2]
   - [follow-up question 3]
6. Make the follow-up questions specific and interesting based on the topic.
7. If evidence is insufficient, say: "Breaking coverage on this is limited — here's what I know: [best attempt]"

RESPOND NOW:"""

        return prompt

    @classmethod
    def _call_gemini_chat(cls, prompt: str) -> Optional[str]:
        """Calls Gemini API with conversational chat prompt."""
        if not settings.GEMINI_API_KEY:
            return None
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 800,
                    "topP": 0.9
                }
            }
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code != 200:
                logger.warning(f"Gemini chat API returned {resp.status_code}")
                return None
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                return None
            return parts[0]["text"]
        except Exception as e:
            logger.warning(f"Gemini chat call failed: {e}")
            return None

    @classmethod
    def _parse_gemini_response(cls, raw_text: str) -> Tuple[str, List[str]]:
        """
        Parses Gemini response into:
        - main_answer (str)
        - follow_up_questions (List[str])
        """
        follow_ups = []
        main_answer = raw_text.strip()

        if "FOLLOW_UPS:" in raw_text:
            parts = raw_text.split("FOLLOW_UPS:", 1)
            main_answer = parts[0].strip()
            followup_block = parts[1].strip()
            for line in followup_block.split("\n"):
                line = line.strip().lstrip("- •*").strip()
                if line and len(line) > 10:
                    follow_ups.append(line)

        follow_ups = follow_ups[:3]
        return main_answer, follow_ups

    @classmethod
    def _local_chat_synthesis(cls, query: str, search_results, citations: List[GroundedCitation]) -> Tuple[str, List[str]]:
        """
        Fallback local RAG synthesis when Gemini is unavailable.
        Produces a readable answer from extracted sentences.
        """
        if not search_results:
            answer = f"I searched for news on \"{query}\" but couldn't find relevant live coverage right now. Try rephrasing or check the Live Feed tab."
            return answer, []

        top = search_results[0].chunk
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", top.text) if len(s.strip()) > 20]

        if sentences:
            answer = f"{sentences[0]} [1]"
            if len(sentences) > 1:
                answer += f" {sentences[1]} [1]"
        else:
            answer = f"Recent reporting from {top.source_name} covers this topic: {top.text[:180]}... [1]"

        if len(search_results) > 1:
            s2 = search_results[1].chunk
            s2_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", s2.text) if len(s.strip()) > 20]
            if s2_sents:
                answer += f" Additionally, {s2.source_name} reports: {s2_sents[0]} [2]"

        follow_ups = [
            f"What are the broader implications of {query}?",
            f"Who are the key players involved in {query}?",
            f"What happened before this with {query}?"
        ]
        return answer, follow_ups

    @classmethod
    def ask(cls, request: ChatTurnRequest, db: Session) -> ChatTurnResponse:
        """
        Full Conversational Intelligence Pipeline:
        1.  Session management (persist / retrieve)
        2.  Conversation history loading
        3.  Context-aware query rewriting (anaphora resolution)
        4.  Live news retrieval (Google News + NewsAPI)
        5.  Vector indexing + semantic similarity search
        6.  Gemini conversational synthesis with full history
        7.  Response parsing -> main answer + follow-up suggestions
        8.  Hallucination shield verification
        9.  SQLite persistence
        10. Rich response return with citations + follow-ups
        """
        session = cls.get_or_create_session(request.session_id, request.message, db)
        history = db.query(ChatMessage).filter_by(session_id=session.id).order_by(ChatMessage.created_at.asc()).all()

        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.message,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user_msg)
        db.commit()

        rewritten_query = cls.resolve_query_context(request.message, history)

        search_res = news_fetcher.search(query=rewritten_query, limit=12)
        raw_articles = search_res.articles

        session_vector_store = InMemoryVectorStore()
        session_vector_store.add_articles(raw_articles)
        relevant_chunks = session_vector_store.similarity_search(rewritten_query, top_k=5, min_score=0.03)

        citations = []
        seen_sources = set()
        for idx, res in enumerate(relevant_chunks, start=1):
            chunk = res.chunk
            seen_sources.add(chunk.source_name)
            citations.append(GroundedCitation(
                index=idx,
                source_name=chunk.source_name,
                article_title=chunk.article_title,
                url=chunk.url,
                passage_snippet=chunk.text[:150] + "..." if len(chunk.text) > 150 else chunk.text
            ))

        follow_up_questions = []
        final_answer = ""

        if relevant_chunks:
            gemini_prompt = cls._build_conversation_prompt(rewritten_query, relevant_chunks, history)
            gemini_raw = cls._call_gemini_chat(gemini_prompt)

            if gemini_raw:
                final_answer, follow_up_questions = cls._parse_gemini_response(gemini_raw)
            else:
                final_answer, follow_up_questions = cls._local_chat_synthesis(rewritten_query, relevant_chunks, citations)
        else:
            final_answer = f"I searched live news for \"{request.message}\" but found no matching articles right now. Try a broader search or check the Live Feed tab."
            follow_up_questions = [
                "What are the latest technology news?",
                "Show me today's business headlines",
                "What's happening in AI right now?"
            ]

        _, audit_report = hallucination_shield.inspect_generation(final_answer, relevant_chunks)

        if relevant_chunks and relevant_chunks[0].similarity_score >= 0.25:
            evidence_strength = "HIGH"
        elif relevant_chunks and relevant_chunks[0].similarity_score >= 0.10:
            evidence_strength = "MEDIUM"
        elif relevant_chunks:
            evidence_strength = "LOW"
        else:
            evidence_strength = "INSUFFICIENT"

        citations_json = json.dumps([c.model_dump() for c in citations])
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=final_answer,
            citations=citations_json,
            evidence_strength=evidence_strength,
            created_at=datetime.now(timezone.utc)
        )
        db.add(assistant_msg)
        db.commit()

        return ChatTurnResponse(
            session_id=session.id,
            original_query=request.message,
            rewritten_query=rewritten_query,
            role="assistant",
            content=final_answer,
            citations=citations,
            evidence_strength=evidence_strength,
            audit_report=audit_report,
            follow_up_questions=follow_up_questions
        )


# Singleton instance
chatbot_service = ChatbotService()
