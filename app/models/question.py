from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class QuestionType(str, Enum):
    """Question type enumeration"""
    MCQ = "mcq"
    OPEN_ENDED = "open_ended"


class QuestionDifficulty(str, Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MCQQuestion(BaseModel):
    """Multiple Choice Question model"""
    id: str = Field(..., description="Unique question identifier")
    type: Literal[QuestionType.MCQ] = QuestionType.MCQ
    question_text: str = Field(..., description="The question text")
    options: List[str] = Field(..., min_length=2, max_length=6, description="Answer options")
    correct_answer: str = Field(..., description="The correct answer (must be one of the options)")
    explanation: str = Field(..., description="Detailed explanation of the answer")
    difficulty: QuestionDifficulty = Field(default=QuestionDifficulty.MEDIUM)
    topic: Optional[str] = Field(None, description="Question topic/subject")


class OpenEndedQuestion(BaseModel):
    """Open-ended question model"""
    id: str = Field(..., description="Unique question identifier")
    type: Literal[QuestionType.OPEN_ENDED] = QuestionType.OPEN_ENDED
    question_text: str = Field(..., description="The question text")
    sample_answer: str = Field(..., description="A sample correct answer")
    explanation: str = Field(..., description="Detailed explanation and grading criteria")
    difficulty: QuestionDifficulty = Field(default=QuestionDifficulty.MEDIUM)
    topic: Optional[str] = Field(None, description="Question topic/subject")


class GeneratePDFRequest(BaseModel):
    """Request model for PDF-based question generation"""
    question_type: QuestionType = Field(..., description="Type of questions to generate")
    count: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")


class GenerateSimilarRequest(BaseModel):
    """Request model for similarity-based question generation"""
    question_text: Optional[str] = Field(None, description="Question text input")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image of question")
    count: int = Field(default=3, ge=1, le=10, description="Number of similar questions to generate")


class RefineQuestionRequest(BaseModel):
    """Request model for interactive question refinement"""
    question_id: str = Field(..., description="ID of the question to refine")
    current_question: dict = Field(..., description="Current question data")
    refinement_prompt: str = Field(..., description="User's refinement instruction")
    conversation_history: List[dict] = Field(default_factory=list, description="Previous refinement steps")


class GenerateQuestionsResponse(BaseModel):
    """Response model for question generation"""
    questions: List[dict] = Field(..., description="Generated questions")
    total_count: int = Field(..., description="Total number of questions generated")


class RefineQuestionResponse(BaseModel):
    """Response model for question refinement"""
    refined_question: dict = Field(..., description="The refined question")
    changes_made: str = Field(..., description="Description of changes made")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class QuestionResponse(BaseModel):
    """Response model for individual questions (used in history)"""
    id: int = Field(..., description="Question database ID")
    question_type: str = Field(..., description="Type of question (mcq or open_ended)")
    question_text: str = Field(..., description="The question text")
    explanation: str = Field(..., description="Explanation")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    confidence_score: Optional[float] = Field(None, description="AI confidence score (0-1)")
    options: Optional[List[str]] = Field(None, description="MCQ options")
    correct_answer: Optional[str] = Field(None, description="MCQ correct answer")
    sample_answer: Optional[str] = Field(None, description="Open-ended sample answer")
