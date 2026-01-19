"""CRUD operations for database"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database.models import GenerationSession, GeneratedQuestion


def create_session(
    db: Session,
    session_type: str,
    source_file: Optional[str] = None,
    source_text: Optional[str] = None,
    config: Optional[dict] = None
) -> GenerationSession:
    """Create a new generation session"""
    db_session = GenerationSession(
        session_type=session_type,
        source_file=source_file,
        source_text=source_text,
        config=config
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def create_question(
    db: Session,
    session_id: int,
    question_type: str,
    question_text: str,
    explanation: str,
    difficulty: Optional[str] = None,
    confidence_score: Optional[float] = None,
    options: Optional[List[str]] = None,
    correct_answer: Optional[str] = None,
    sample_answer: Optional[str] = None,
    image_url: Optional[str] = None
) -> GeneratedQuestion:
    """Create a new generated question"""
    db_question = GeneratedQuestion(
        session_id=session_id,
        question_type=question_type,
        question_text=question_text,
        explanation=explanation,
        difficulty=difficulty,
        confidence_score=confidence_score,
        options=options,
        correct_answer=correct_answer,
        sample_answer=sample_answer,
        image_url=image_url
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_recent_sessions(
    db: Session,
    limit: int = 20,
    session_type: Optional[str] = None
) -> List[GenerationSession]:
    """Get recent generation sessions"""
    query = db.query(GenerationSession)
    
    if session_type:
        query = query.filter(GenerationSession.session_type == session_type)
    
    return query.order_by(GenerationSession.created_at.desc()).limit(limit).all()


def get_session_with_questions(db: Session, session_id: int) -> Optional[GenerationSession]:
    """Get a session with all its questions"""
    return db.query(GenerationSession).filter(GenerationSession.id == session_id).first()


def get_questions_by_session(db: Session, session_id: int) -> List[GeneratedQuestion]:
    """Get all questions for a session"""
    return db.query(GeneratedQuestion).filter(GeneratedQuestion.session_id == session_id).all()


def update_question(
    db: Session,
    question_id: int,
    question_text: Optional[str] = None,
    explanation: Optional[str] = None,
    options: Optional[List[str]] = None,
    correct_answer: Optional[str] = None,
    sample_answer: Optional[str] = None
) -> Optional[GeneratedQuestion]:
    """Update a question (for manual editing)"""
    db_question = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == question_id).first()
    
    if not db_question:
        return None
    
    if question_text is not None:
        db_question.question_text = question_text
    if explanation is not None:
        db_question.explanation = explanation
    if options is not None:
        db_question.options = options
    if correct_answer is not None:
        db_question.correct_answer = correct_answer
    if sample_answer is not None:
        db_question.sample_answer = sample_answer
    
    db_question.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_question)
    return db_question


def delete_session(db: Session, session_id: int) -> bool:
    """Delete a session and all its questions"""
    db_session = db.query(GenerationSession).filter(GenerationSession.id == session_id).first()
    
    if not db_session:
        return False
    
    db.delete(db_session)
    db.commit()
    return True


def get_statistics(db: Session) -> dict:
    """Get overall statistics"""
    total_sessions = db.query(GenerationSession).count()
    total_questions = db.query(GeneratedQuestion).count()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_sessions = db.query(GenerationSession).filter(
        GenerationSession.created_at >= week_ago
    ).count()
    
    return {
        "total_sessions": total_sessions,
        "total_questions": total_questions,
        "recent_sessions_7d": recent_sessions
    }
