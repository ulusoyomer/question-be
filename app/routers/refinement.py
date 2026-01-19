"""API endpoints for interactive question refinement (Canvas flow)"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.question import RefineQuestionRequest, RefineQuestionResponse, ErrorResponse
from app.services.ai_service import AIService
from app.database.database import get_db
from app.database import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["refinement"])


@router.post(
    "/refine-question",
    response_model=RefineQuestionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def refine_question(request: RefineQuestionRequest, db: Session = Depends(get_db)):
    """
    Interactively refine a question using natural language prompts
    
    This endpoint implements the "Canvas" experience:
    1. Accepts a question and a refinement prompt
    2. Maintains conversation context
    3. Updates the question based on natural language instructions
    4. Returns the refined question with change description
    
    Example refinement prompts:
    - "Change the correct answer to B"
    - "Make option C harder"
    - "Make the distractors more confusing"
    - "Change the numbers to create an integer result"
    - "Increase the difficulty level"
    """
    try:
        if not request.current_question:
            raise HTTPException(
                status_code=400,
                detail="current_question is required"
            )
        
        if not request.refinement_prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="refinement_prompt cannot be empty"
            )
        
        logger.info(f"Refining question {request.question_id} with prompt: {request.refinement_prompt}")
        
        ai_service = AIService()
        result = ai_service.refine_question(
            current_question=request.current_question,
            refinement_prompt=request.refinement_prompt,
            conversation_history=request.conversation_history
        )
        
        refined_question = result.get("refined_question")
        changes_made = result.get("changes_made", "Question refined successfully")
        
        if not refined_question:
            raise ValueError("AI service did not return a refined question")
        
        try:
            session = crud.create_session(
                db=db,
                session_type="refinement",
                source_text=f"Refined: {request.refinement_prompt[:100]}",
                config={
                    "original_question_id": request.question_id,
                    "refinement_prompt": request.refinement_prompt,
                    "changes_made": changes_made
                }
            )
            
            crud.save_question(
                db=db,
                session_id=session.id,
                question_data=refined_question
            )
            
            logger.info(f"Saved refined question to session {session.id}")
        except Exception as db_error:
            logger.error(f"Failed to save refined question to database: {db_error}")
        
        return RefineQuestionResponse(
            refined_question=refined_question,
            changes_made=changes_made
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refine_question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while refining the question: {str(e)}"
        )
