"""AI Service for OpenRouter integration with structured outputs"""

import json
import logging
from typing import Dict, Any, List
from openai import OpenAI
from app.config import get_settings
from app.utils.schemas import MCQ_SCHEMA, OPEN_ENDED_SCHEMA, REFINEMENT_SCHEMA
from app.utils.prompts import (
    PDF_GENERATION_PROMPT,
    SIMILARITY_GENERATION_PROMPT,
    REFINEMENT_PROMPT,
    OCR_ANALYSIS_PROMPT
)

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with OpenRouter API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.settings.openrouter_api_key,
        )
    
    def _call_llm_with_schema(
        self,
        system_prompt: str,
        user_message: str,
        schema: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Call LLM with structured output enforcement
        
        Args:
            system_prompt: System instruction for the LLM
            user_message: User's message/content
            schema: JSON schema for response validation
            max_retries: Maximum number of retry attempts
            
        Returns:
            Parsed JSON response matching the schema
        """
        for attempt in range(max_retries):
            try:
                enhanced_prompt = f"""{system_prompt}

You MUST respond with valid JSON that matches this exact schema:
{json.dumps(schema, indent=2)}

Do not include any text before or after the JSON object."""

                response = self.client.chat.completions.create(
                    model=self.settings.model_name,
                    messages=[
                        {"role": "system", "content": enhanced_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                )
                
                content = response.choices[0].message.content
                
                result = json.loads(content)
                
                logger.info(f"Successfully generated structured output on attempt {attempt + 1}")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to get valid JSON after {max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Error calling LLM on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise ValueError("Failed to generate response")
    
    def generate_questions_from_text(
        self,
        text_content: str,
        question_type: str,
        count: int
    ) -> Dict[str, Any]:
        """
        Generate questions from text content
        
        Args:
            text_content: Extracted text from PDF
            question_type: 'mcq' or 'open_ended'
            count: Number of questions to generate
            
        Returns:
            Dictionary with generated questions
        """
        schema = MCQ_SCHEMA if question_type == "mcq" else OPEN_ENDED_SCHEMA
        
        system_prompt = PDF_GENERATION_PROMPT.format(
            count=count,
            question_type="Multiple Choice Questions (MCQ)" if question_type == "mcq" else "Open-Ended Questions"
        )
        
        user_message = f"Generate {count} {question_type} questions from this text:\n\n{text_content}"
        
        return self._call_llm_with_schema(system_prompt, user_message, schema)
    
    def generate_similar_questions(
        self,
        original_question: str,
        count: int,
        question_type: str = "mcq"
    ) -> Dict[str, Any]:
        """
        Generate similar questions based on an original question
        
        Args:
            original_question: The original question text or extracted content
            count: Number of similar questions to generate
            question_type: Type of question (mcq or open_ended)
            
        Returns:
            Dictionary with generated similar questions
        """
        schema = MCQ_SCHEMA if question_type == "mcq" else OPEN_ENDED_SCHEMA
        
        system_prompt = SIMILARITY_GENERATION_PROMPT.format(count=count)
        
        user_message = f"""Orijinal soru:
{original_question}

ÖNEMLİ TALİMATLAR:
- {count} adet benzer ÇOKTAN SEÇMELİ soru üret
- Sorular MUTLAKA TÜRKÇE olmalı
- Her soru TAM OLARAK 4 şık içermeli (A, B, C, D)
- 'options' alanına tüm 4 şıkkı ekle
- Doğru cevabı net şekilde işaretle
- Eğer orijinal soruda görsel/grafik varsa, yeni sorular aynı görsele referans vermeli"""
        
        return self._call_llm_with_schema(system_prompt, user_message, schema)
    
    def refine_question(
        self,
        current_question: Dict[str, Any],
        refinement_prompt: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Refine a question based on user's natural language prompt
        
        Args:
            current_question: The current question data
            refinement_prompt: User's refinement instruction
            conversation_history: Previous refinement steps
            
        Returns:
            Dictionary with refined question and changes description
        """
        if conversation_history is None:
            conversation_history = []
        
        history_text = "\n".join([
            f"User: {item.get('user', '')}\nAssistant: {item.get('assistant', '')}"
            for item in conversation_history
        ]) if conversation_history else "No previous refinements"
        
        system_prompt = REFINEMENT_PROMPT.format(
            current_question=json.dumps(current_question, indent=2),
            refinement_prompt=refinement_prompt,
            conversation_history=history_text
        )
        
        user_message = f"Please refine the question according to this instruction: {refinement_prompt}"
        
        return self._call_llm_with_schema(system_prompt, user_message, REFINEMENT_SCHEMA)
    
    def extract_question_from_image(self, image_base64: str) -> str:
        """
        Extract question text from image using vision model
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Extracted question text
        """
        try:
            response = self.client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",  # Vision-capable model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": OCR_ANALYSIS_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error extracting question from image: {e}")
            raise ValueError(f"Failed to extract question from image: {str(e)}")
