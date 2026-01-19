"""API endpoints for PDF-based question generation"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.question import GenerateQuestionsResponse, ErrorResponse, QuestionType
from app.services.ai_service import AIService
from app.services.pdf_service import PDFService
from app.database.database import get_db
from app.database import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["generation"])


@router.post(
    "/generate-from-pdf",
    response_model=GenerateQuestionsResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def generate_from_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    question_type: str = Form(..., description="Type of questions: 'mcq' or 'open_ended'"),
    count: int = Form(5, ge=1, le=20, description="Number of questions to generate"),
    db: Session = Depends(get_db)
):
    """
    Generate educational questions from uploaded PDF content
    
    This endpoint:
    1. Accepts a PDF file upload
    2. Extracts text content from the PDF
    3. Uses AI to generate questions based on the content
    4. Returns structured questions with explanations
    
    Supports both Multiple Choice Questions (MCQ) and Open-Ended questions.
    """
    try:
        if question_type not in ["mcq", "open_ended"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid question_type. Must be 'mcq' or 'open_ended'"
            )
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        pdf_bytes = await file.read()
        
        pdf_service = PDFService()
        if not pdf_service.validate_pdf(pdf_bytes):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file"
            )
        
        logger.info(f"Extracting text from PDF: {file.filename}")
        text_content = pdf_service.extract_text_from_pdf(pdf_bytes)
        
        if len(text_content) < 100:
            raise HTTPException(
                status_code=400,
                detail="PDF content is too short to generate meaningful questions"
            )
        
        logger.info(f"Generating {count} {question_type} questions")
        ai_service = AIService()
        result = ai_service.generate_questions_from_text(
            text_content=text_content,
            question_type=question_type,
            count=count
        )
        
        questions = result.get("questions", [])
        
        try:
            db_session = crud.create_session(
                db=db,
                session_type="pdf",
                source_file=file.filename,
                config={"question_type": question_type, "count": count}
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
                    image_url=q.get("image_url")
                )
            
            logger.info(f"Saved session {db_session.id} with {len(questions)} questions")
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")
        
        return GenerateQuestionsResponse(
            questions=questions,
            total_count=len(questions)
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in generate_from_pdf: {e}")
        error_msg = str(e)
        
        status_code = 500
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            status_code = 401
            error_msg = "Authentication failed. Please check your API Key."
        elif "insufficient_quota" in error_msg.lower() or "billing" in error_msg.lower():
            status_code = 429
            error_msg = "API Quota exceeded or billing issue."
            
        raise HTTPException(
            status_code=status_code,
            detail=f"Operation failed: {error_msg}"
        )
