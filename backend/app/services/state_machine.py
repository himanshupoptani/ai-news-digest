import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.article import Article
from backend.app.models.state import ArticleStateLog

logger = logging.getLogger(__name__)

class ArticleState(str, Enum):
    """The 12 formal states of the Article Selection State Machine."""
    DISCOVERED = "DISCOVERED"
    COLLECTED = "COLLECTED"
    CLEANED = "CLEANED"
    CLASSIFIED = "CLASSIFIED"
    FILTERED = "FILTERED"
    RELEVANT = "RELEVANT"
    DUPLICATE_CHECKED = "DUPLICATE_CHECKED"
    SELECTED = "SELECTED"
    RETRIEVED = "RETRIEVED"
    SUMMARIZED = "SUMMARIZED"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    
    # Terminal rejection states
    REJECTED = "REJECTED"
    DUPLICATE_ARCHIVED = "DUPLICATE_ARCHIVED"

class ArticleStateMachine:
    """
    Finite State Machine governing article progression.
    Guarantees that no uncleaned, duplicate, or unverified article reaches the user.
    """

    # Permitted state transitions (Directed Graph)
    VALID_TRANSITIONS: Dict[ArticleState, List[ArticleState]] = {
        ArticleState.DISCOVERED: [ArticleState.COLLECTED, ArticleState.REJECTED],
        ArticleState.COLLECTED: [ArticleState.CLEANED, ArticleState.REJECTED],
        ArticleState.CLEANED: [ArticleState.CLASSIFIED, ArticleState.REJECTED],
        ArticleState.CLASSIFIED: [ArticleState.FILTERED, ArticleState.REJECTED],
        ArticleState.FILTERED: [ArticleState.RELEVANT, ArticleState.REJECTED],
        ArticleState.RELEVANT: [ArticleState.DUPLICATE_CHECKED, ArticleState.REJECTED],
        ArticleState.DUPLICATE_CHECKED: [ArticleState.SELECTED, ArticleState.DUPLICATE_ARCHIVED],
        ArticleState.SELECTED: [ArticleState.RETRIEVED, ArticleState.REJECTED],
        ArticleState.RETRIEVED: [ArticleState.SUMMARIZED, ArticleState.REJECTED],
        ArticleState.SUMMARIZED: [ArticleState.VERIFIED, ArticleState.REJECTED],
        ArticleState.VERIFIED: [ArticleState.PUBLISHED, ArticleState.REJECTED],
        ArticleState.PUBLISHED: [],  # Terminal successful state
        ArticleState.REJECTED: [],   # Terminal rejection state
        ArticleState.DUPLICATE_ARCHIVED: [], # Terminal duplicate state
    }

    @classmethod
    def can_transition(cls, current_state_str: str, target_state_str: str) -> bool:
        """Validates whether transitioning from current_state to target_state is permissible."""
        try:
            current = ArticleState(current_state_str)
            target = ArticleState(target_state_str)
            return target in cls.VALID_TRANSITIONS.get(current, [])
        except ValueError:
            return False

    @classmethod
    def transition(
        cls, 
        article: Article, 
        target_state: ArticleState, 
        reason: str, 
        db: Session
    ) -> ArticleStateLog:
        """
        Executes a validated state transition and writes an immutable audit log into the database.
        Raises ValueError if transition violates the state machine rules.
        """
        current_state_str = article.current_state
        target_state_str = target_state.value

        if not cls.can_transition(current_state_str, target_state_str):
            err_msg = (
                f"Illegal FSM Transition: Cannot transition article #{article.id} "
                f"from '{current_state_str}' to '{target_state_str}'. "
                f"Permitted next states are: {[s.value for s in cls.VALID_TRANSITIONS.get(ArticleState(current_state_str), [])]}"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

        # 1. Update article current state
        article.current_state = target_state_str

        # 2. Record audit log
        log_entry = ArticleStateLog(
            article_id=article.id,
            previous_state=current_state_str,
            to_state=target_state_str,
            reason=reason,
            transitioned_at=datetime.now(timezone.utc)
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        return log_entry

    @staticmethod
    def get_audit_trail(article_id: int, db: Session) -> List[Dict[str, Any]]:
        """Retrieves the complete explainable audit trail of an article for the UI or viva demo."""
        logs = db.query(ArticleStateLog).filter_by(article_id=article_id).order_by(ArticleStateLog.transitioned_at.asc()).all()
        return [
            {
                "log_id": log.id,
                "previous_state": log.previous_state,
                "to_state": log.to_state,
                "reason": log.reason,
                "transitioned_at": log.transitioned_at.isoformat() if log.transitioned_at else None
            }
            for log in logs
        ]

# Singleton instance
state_machine = ArticleStateMachine()

