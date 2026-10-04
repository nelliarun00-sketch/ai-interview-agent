"""
AI Structured Schemas
---------------------
Defines the required schemas and validation rules for all LLM outputs.
Every Gemini prompt is bounded by these strict contracts.
"""

from typing import Dict, Any, List


ANSWER_EVALUATION_SCHEMA = {
    "type": "object",
    "required": ["score", "strengths", "improvements", "weak_area", "better_answer"],
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 10},
        "concepts_expected": {"type": "array", "items": {"type": "string"}},
        "concepts_covered": {"type": "array", "items": {"type": "string"}},
        "concepts_missed": {"type": "array", "items": {"type": "string"}},
        "misconceptions": {"type": "array", "items": {"type": "string"}},
        "strengths": {"type": "string"},
        "improvements": {"type": "string"},
        "weak_area": {"type": "string"},
        "recommended_topic": {"type": "string"},
        "better_answer": {"type": "string"},
        "followup_suggestion": {"type": "string"},
        "confidence_of_evaluation": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "next_difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]}
    }
}

QUESTION_GEN_SCHEMA = {
    "type": "object",
    "required": ["question", "topic", "difficulty"],
    "properties": {
        "question": {"type": "string"},
        "topic": {"type": "string"},
        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
        "expected_concepts": {"type": "array", "items": {"type": "string"}}
    }
}

CODING_REVIEW_SCHEMA = {
    "type": "object",
    "required": ["score", "correctness_reasoning", "time_complexity", "space_complexity", "optimal_approach"],
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 10},
        "correctness_reasoning": {"type": "string"},
        "time_complexity": {"type": "string"},
        "space_complexity": {"type": "string"},
        "edge_cases_missed": {"type": "array", "items": {"type": "string"}},
        "code_quality": {"type": "string"},
        "improvements": {"type": "array", "items": {"type": "string"}},
        "optimal_approach": {"type": "string"}
    }
}

RESUME_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": ["ats_score", "skills_extracted", "missing_skills", "suggested_interview_questions"],
    "properties": {
        "ats_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "sections_present": {"type": "array", "items": {"type": "string"}},
        "skills_extracted": {"type": "array", "items": {"type": "string"}},
        "quantified_bullets_found": {"type": "integer"},
        "weak_bullets_with_rewrites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "critique": {"type": "string"},
                    "improved": {"type": "string"}
                }
            }
        },
        "missing_skills": {"type": "array", "items": {"type": "string"}},
        "suggested_interview_questions": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"}
    }
}

ADVISOR_CHAT_SCHEMA = {
    "type": "object",
    "required": ["reply_markdown"],
    "properties": {
        "reply_markdown": {"type": "string"},
        "recommended_action": {"type": "string"},
        "action_payload": {"type": "object"},
        "cited_resource_ids": {"type": "array", "items": {"type": "string"}}
    }
}


# Backward-compatible alias
ANSWER_EVAL_SCHEMA = ANSWER_EVALUATION_SCHEMA
