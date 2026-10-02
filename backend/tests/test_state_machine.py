import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import Source, Article, ArticleStateLog
from backend.app.services.state_machine import ArticleState, ArticleStateMachine

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    
    # Create test source
    source = Source(name="Reuters", domain="reuters.com")
    session.add(source)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_valid_state_transitions(db):
    source = db.query(Source).first()
    article = Article(
        title="Valid FSM Lifecycle Article",
        url="https://reuters.com/fsm-test-1",
        source_id=source.id,
        current_state=ArticleState.DISCOVERED.value
    )
    db.add(article)
    db.commit()

    # Transition 1: DISCOVERED -> COLLECTED
    log1 = ArticleStateMachine.transition(
        article=article,
        target_state=ArticleState.COLLECTED,
        reason="Metadata and raw content ingested.",
        db=db
    )
    assert article.current_state == ArticleState.COLLECTED.value
    assert log1.previous_state == ArticleState.DISCOVERED.value
    assert log1.to_state == ArticleState.COLLECTED.value

    # Transition 2: COLLECTED -> CLEANED
    log2 = ArticleStateMachine.transition(
        article=article,
        target_state=ArticleState.CLEANED,
        reason="HTML boilerplate and advertisements stripped.",
        db=db
    )
    assert article.current_state == ArticleState.CLEANED.value
    assert log2.to_state == ArticleState.CLEANED.value

    # Verify audit trail
    trail = ArticleStateMachine.get_audit_trail(article.id, db)
    assert len(trail) == 2
    assert trail[0]["to_state"] == "COLLECTED"
    assert trail[1]["to_state"] == "CLEANED"

def test_illegal_state_transition_raises_error(db):
    source = db.query(Source).first()
    article = Article(
        title="Illegal Jump Article",
        url="https://reuters.com/fsm-illegal",
        source_id=source.id,
        current_state=ArticleState.DISCOVERED.value
    )
    db.add(article)
    db.commit()

    # Attempting to jump directly from DISCOVERED to PUBLISHED must fail
    with pytest.raises(ValueError) as exc_info:
        ArticleStateMachine.transition(
            article=article,
            target_state=ArticleState.PUBLISHED,
            reason="Attempting illegal skip of cleaning and verification.",
            db=db
        )
    assert "Illegal FSM Transition" in str(exc_info.value)
    # Ensure state remained unchanged
    assert article.current_state == ArticleState.DISCOVERED.value

def test_duplicate_archival_transition(db):
    source = db.query(Source).first()
    article = Article(
        title="Duplicate Wire Article",
        url="https://reuters.com/fsm-dup",
        source_id=source.id,
        current_state=ArticleState.DUPLICATE_CHECKED.value
    )
    db.add(article)
    db.commit()

    # DUPLICATE_CHECKED can transition to DUPLICATE_ARCHIVED
    log = ArticleStateMachine.transition(
        article=article,
        target_state=ArticleState.DUPLICATE_ARCHIVED,
        reason="92% TF-IDF Cosine match with primary canonical story.",
        db=db
    )
    assert article.current_state == ArticleState.DUPLICATE_ARCHIVED.value
    assert log.to_state == ArticleState.DUPLICATE_ARCHIVED.value

