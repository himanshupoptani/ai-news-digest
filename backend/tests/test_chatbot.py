import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.schemas.chat import ChatTurnRequest, ChatTurnResponse
from backend.app.services.chatbot_service import ChatbotService

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_query_context_resolution(db):
    session = ChatSession(title="Nvidia Inquiry")
    db.add(session)
    db.commit()

    msg1 = ChatMessage(session_id=session.id, role="user", content="What happened with Nvidia Blackwell chips?")
    msg2 = ChatMessage(session_id=session.id, role="assistant", content="Nvidia announced mass shipments but faced packaging challenges.")
    db.add_all([msg1, msg2])
    db.commit()

    history = [msg1, msg2]

    # Follow-up with pronoun "it"
    followup = "Why did it get delayed?"
    rewritten = ChatbotService.resolve_query_context(followup, history)

    # Rewritten query must incorporate previous entity context
    assert "nvidia" in rewritten.lower() or "blackwell" in rewritten.lower()
    assert "delayed" in rewritten.lower()

    # Independent query must NOT be altered
    independent = "Who won the basketball championship?"
    not_rewritten = ChatbotService.resolve_query_context(independent, history)
    assert not_rewritten == independent

def test_end_to_end_chat_turn(db):
    req1 = ChatTurnRequest(session_id=None, message="Tell me about Nvidia earnings")
    res1 = ChatbotService.ask(req1, db)

    assert isinstance(res1, ChatTurnResponse)
    assert res1.session_id is not None
    assert res1.content != ""
    assert res1.evidence_strength in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]
    
    # Verify messages saved to SQLite
    saved_messages = db.query(ChatMessage).filter_by(session_id=res1.session_id).all()
    assert len(saved_messages) == 2
    assert saved_messages[0].role == "user"
    assert saved_messages[1].role == "assistant"

    # Multi-turn follow up using existing session
    req2 = ChatTurnRequest(session_id=res1.session_id, message="Did any other source confirm this?")
    res2 = ChatbotService.ask(req2, db)

    assert res2.session_id == res1.session_id
    updated_messages = db.query(ChatMessage).filter_by(session_id=res1.session_id).all()
    assert len(updated_messages) == 4

