"""Database models for persistence"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.database import Base


class GenerationSession(Base):
    """Stores generation sessions (PDF uploads, similar questions, etc.)"""
    __tablename__ = "generation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_type = Column(String, index=True)  # 'pdf', 'similar', 'refinement'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source_file = Column(String, nullable=True)  # PDF filename or image path
    source_text = Column(Text, nullable=True)  # Original question text
    config = Column(JSON, nullable=True)  # Question type, count, etc.
    
    questions = relationship("GeneratedQuestion", back_populates="session", cascade="all, delete-orphan")


class GeneratedQuestion(Base):
    """Stores individual generated questions"""
    __tablename__ = "generated_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("generation_sessions.id"))
    
    question_type = Column(String)  # 'mcq' or 'open_ended'
    question_text = Column(Text)
    explanation = Column(Text)
    difficulty = Column(String, nullable=True)  # 'easy', 'medium', 'hard'
    confidence_score = Column(Float, nullable=True)  # AI confidence (0-1)
    
    options = Column(JSON, nullable=True)  # List of options
    correct_answer = Column(String, nullable=True)
    
    sample_answer = Column(Text, nullable=True)
    
    image_url = Column(String, nullable=True)  # URL or base64 data for question image
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    session = relationship("GenerationSession", back_populates="questions")
