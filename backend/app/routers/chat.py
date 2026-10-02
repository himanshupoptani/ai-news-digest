from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.schemas.chat import ChatTurnRequest, ChatTurnResponse
from backend.app.services.chatbot_service import chatbot_service, SUGGESTED_PROMPTS

router = APIRouter(prefix="/api/chat", tags=["Conversational News Chatbot"])

@router.get("/suggest")
def get_suggested_prompts():
    """Returns a list of suggested conversation starters for the chatbot."""
    return {"suggestions": SUGGESTED_PROMPTS}


@router.post("/message", response_model=ChatTurnResponse)
def send_chat_message(request: ChatTurnRequest, db: Session = Depends(get_db)):
    """
    Submits a user message to the conversational news chatbot.
    Performs context resolution, RAG retrieval, citation verification, and SQLite persistence.
    """
    try:
        return chatbot_service.ask(request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.get("/sessions")
def list_chat_sessions(db: Session = Depends(get_db)):
    """Lists all active and past research sessions."""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        }
        for s in sessions
    ]

@router.get("/history/{session_id}")
def get_session_history(session_id: int, db: Session = Depends(get_db)):
    """Retrieves all chat messages for a specific session."""
    session = db.query(ChatSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(ChatMessage).filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
    return {
        "session_id": session.id,
        "title": session.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "evidence_strength": m.evidence_strength,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]
    }

