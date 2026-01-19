"""JSON Schemas for structured LLM outputs"""

MCQ_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["mcq"]},
                    "question_text": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 6
                    },
                    "correct_answer": {"type": "string"},
                    "explanation": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "topic": {"type": "string"},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "image_url": {"type": "string"}
                },
                "required": ["id", "type", "question_text", "options", "correct_answer", "explanation", "confidence_score"]
            }
        }
    },
    "required": ["questions"]
}

OPEN_ENDED_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["open_ended"]},
                    "question_text": {"type": "string"},
                    "sample_answer": {"type": "string"},
                    "explanation": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "topic": {"type": "string"},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "image_url": {"type": "string"}
                },
                "required": ["id", "type", "question_text", "sample_answer", "explanation", "confidence_score"]
            }
        }
    },
    "required": ["questions"]
}

REFINEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "refined_question": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "question_text": {"type": "string"},
                "options": {"type": "array", "items": {"type": "string"}},
                "correct_answer": {"type": "string"},
                "sample_answer": {"type": "string"},
                "explanation": {"type": "string"},
                "difficulty": {"type": "string"},
                "topic": {"type": "string"}
            },
            "required": ["id", "type", "question_text", "explanation"]
        },
        "changes_made": {"type": "string"}
    },
    "required": ["refined_question", "changes_made"]
}
