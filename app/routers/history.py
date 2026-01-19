"""API endpoints for history and persistence"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.database import get_db
from app.database import crud
from app.models.question import QuestionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/history", tags=["history"])


class SessionResponse(BaseModel):
    id: int
    session_type: str
    created_at: datetime
    source_file: Optional[str]
    source_text: Optional[str]
    config: Optional[dict]
    question_count: int
    
    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    id: int
    session_type: str
    created_at: datetime
    source_file: Optional[str]
    source_text: Optional[str]
    config: Optional[dict]
    question_count: int
    questions: List[QuestionResponse]

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    total_sessions: int
    total_questions: int
    recent_sessions_7d: int


class UpdateQuestionRequest(BaseModel):
    question_text: Optional[str] = None
    explanation: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    sample_answer: Optional[str] = None


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    limit: int = 20,
    session_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get recent generation sessions
    
    - **limit**: Maximum number of sessions to return (default: 20)
    - **session_type**: Filter by type ('pdf', 'similar', 'refinement')
    """
    try:
        sessions = crud.get_recent_sessions(db, limit=limit, session_type=session_type)
        
        result = []
        for session in sessions:
            result.append({
                "id": session.id,
                "session_type": session.session_type,
                "created_at": session.created_at,
                "source_file": session.source_file,
                "source_text": session.source_text,
                "config": session.config,
                "question_count": len(session.questions) if session.questions else 0
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific session with all its questions"""
    try:
        session = crud.get_session_with_questions(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        questions = []
        for q in session.questions:
            question_dict = {
                "id": q.id,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "confidence_score": q.confidence_score
            }
            
            if q.question_type == "mcq":
                question_dict["options"] = q.options
                question_dict["correct_answer"] = q.correct_answer
            else:
                question_dict["sample_answer"] = q.sample_answer
            
            if q.image_url:
                question_dict["image_url"] = q.image_url
            
            questions.append(question_dict)
        
        return {
            "id": session.id,
            "session_type": session.session_type,
            "created_at": session.created_at,
            "source_file": session.source_file,
            "source_text": session.source_text,
            "config": session.config,
            "question_count": len(questions),
            "questions": questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Delete a session and all its questions"""
    try:
        success = crud.delete_session(db, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    request: UpdateQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Update a question (manual editing)
    
    Allows users to manually edit generated questions
    """
    try:
        updated_question = crud.update_question(
            db,
            question_id=question_id,
            question_text=request.question_text,
            explanation=request.explanation,
            options=request.options,
            correct_answer=request.correct_answer,
            sample_answer=request.sample_answer
        )
        
        if not updated_question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question_dict = {
            "id": updated_question.id,
            "question_type": updated_question.question_type,
            "question_text": updated_question.question_text,
            "explanation": updated_question.explanation,
            "difficulty": updated_question.difficulty,
            "confidence_score": updated_question.confidence_score
        }
        
        if updated_question.question_type == "mcq":
            question_dict["options"] = updated_question.options
            question_dict["correct_answer"] = updated_question.correct_answer
        else:
            question_dict["sample_answer"] = updated_question.sample_answer
        
        return question_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall usage statistics"""
    try:
        stats = crud.get_statistics(db)
        return stats
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
