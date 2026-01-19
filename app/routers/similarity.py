"""API endpoints for similarity-based question generation"""

import logging
import base64
import os
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.question import GenerateSimilarRequest, GenerateQuestionsResponse, ErrorResponse
from app.services.ai_service import AIService
from app.database.database import get_db
from app.database import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["similarity"])


@router.post(
    "/generate-similar",
    response_model=GenerateQuestionsResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def generate_similar(request: GenerateSimilarRequest, db: Session = Depends(get_db)):
    """
    Generate similar questions based on an input question

    This endpoint:
    1. Accepts either text or image input of a question
    2. Analyzes the difficulty, topic, and format
    3. Generates N similar questions with different contexts
    4. Returns structured questions maintaining the same style

    This is the "style cloning" feature.
    """
    try:
        if not request.question_text and not request.image_base64:
            raise HTTPException(
                status_code=400,
                detail="Either question_text or image_base64 must be provided"
            )

        ai_service = AIService()

        if request.image_base64:
            logger.info("Extracting question from image")
            try:
                extracted_text = ai_service.extract_question_from_image(request.image_base64)
                question_input = extracted_text
            except Exception as e:
                logger.error(f"Failed to extract question from image: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to process image: {str(e)}"
                )
        else:
            question_input = request.question_text

        question_type = "mcq"

        logger.info(f"Generating {request.count} similar {question_type} questions")

        result = ai_service.generate_similar_questions(
            original_question=question_input,
            count=request.count,
            question_type=question_type
        )

        questions = result.get("questions", [])
        
        original_image_url = None
        if request.image_base64:
            try:
                image_data = base64.b64decode(request.image_base64)
                
                image_filename = f"{uuid.uuid4()}.png"
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "questions")
                os.makedirs(upload_dir, exist_ok=True)
                
                image_path = os.path.join(upload_dir, image_filename)
                
                with open(image_path, "wb") as f:
                    f.write(image_data)
                
                backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                original_image_url = f"{backend_url}/uploads/questions/{image_filename}"
                logger.info(f"Saved image to {original_image_url}")
                
                for q in questions:
                    q["image_url"] = original_image_url
            except Exception as e:
                logger.error(f"Failed to save image: {e}")

        try:
            db_session = crud.create_session(
                db=db,
                session_type="similar",
                source_text=question_input[:500] if question_input else None,  # Store first 500 chars of input
                config={"question_type": question_type, "count": request.count}
            )

            for q in questions:
                crud.create_question(
                    db=db,
                    session_id=db_session.id,
                    question_type=q.get("question_type", question_type),
                    question_text=q.get("question_text", ""),
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty"),
                    confidence_score=q.get("confidence_score"),
                    options=q.get("options"),
                    correct_answer=q.get("correct_answer"),
                    sample_answer=q.get("sample_answer"),
                    image_url=original_image_url  # Copy original image to all similar questions
                )

            logger.info(f"Saved similar session {db_session.id} with {len(questions)} questions")
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")

        return GenerateQuestionsResponse(
            questions=questions,
            total_count=len(questions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_similar: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating similar questions: {str(e)}"
        )
