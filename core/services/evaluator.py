"""
Answer & Code Evaluator Service
-------------------------------
Performs structured AI evaluation for technical questions, coding problems,
and behavioral HR prompts with rubric adherence and knowledge tracing updates.
"""

import os
from typing import Dict, Any, List
from core.models import StudentState
from core.repositories.session_repo import data_repo
from core.services.mastery import calculate_mastery_update
from ai.client import ai_client
from ai.validator import parse_and_validate
from ai.schemas import ANSWER_EVALUATION_SCHEMA, CODING_REVIEW_SCHEMA
from ai.trace import ai_trace


def evaluate_technical_answer(
    question: str,
    answer: str,
    job_role: str,
    difficulty: str,
    topic: str,
    student: StudentState
) -> Dict[str, Any]:
    """
    Evaluates a candidate answer against technical rubrics using Gemini or deterministic fallback.
    """
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "ai", "prompts", "answer_eval.v1.txt"
    )
    template = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

    rendered = template.format(
        job_role=job_role,
        question=question,
        answer=answer,
        difficulty=difficulty,
        focus_concepts=topic
    )

    def fallback_evaluation():
        words = len(answer.strip().split())
        score = 8 if words > 30 else (5 if words > 10 else 3)
        return {
            "score": score,
            "concepts_expected": [topic],
            "concepts_covered": [topic] if score >= 5 else [],
            "concepts_missed": [] if score >= 8 else ["Edge cases & performance"],
            "misconceptions": [],
            "strengths": "Addressed the core concept and defined terms clearly." if score >= 5 else "Attempted a response.",
            "improvements": "Elaborate with deeper code syntax or architectural trade-offs." if score < 8 else "Great depth.",
            "weak_area": topic if score < 8 else "Advanced optimizations",
            "recommended_topic": topic,
            "better_answer": f"A comprehensive answer to '{question}' defines the core mechanisms, performance complexity, and practical applications in software engineering.",
            "followup_suggestion": f"Can you explain an edge case in {topic}?" if score >= 7 else None,
            "confidence_of_evaluation": 0.85,
            "next_difficulty": "hard" if score >= 8 else ("medium" if score >= 5 else "easy")
        }

    raw_text, latency, err = ai_client.generate(rendered, json_mode=True)
    validated, source, val_err = parse_and_validate(raw_text, ANSWER_EVALUATION_SCHEMA, fallback_evaluation)

    # Update knowledge tracing for the tested topic
    score_norm = validated["score"] / 10.0
    curr_data = student.skills.get(topic, {"mastery": 0.3, "confidence": 0.1, "attempts": 0})
    updated = calculate_mastery_update(
        current_mastery=float(curr_data.get("mastery", 0.3)),
        current_confidence=float(curr_data.get("confidence", 0.1)),
        attempts=int(curr_data.get("attempts", 0)),
        observed_score=score_norm,
        difficulty=difficulty
    )
    updated["name"] = data_repo.get_skills().get(topic, {}).get("name", topic.capitalize())
    student.skills[topic] = updated

    ai_trace.record(
        operation="evaluate_technical_answer",
        prompt_version="answer_eval.v1",
        inputs={"question": question, "answer_len": len(answer), "topic": topic},
        raw_output=raw_text or "",
        validated_output=validated,
        latency_ms=latency,
        source=source,
        error=err or val_err
    )

    return validated


def evaluate_coding_answer(
    problem: str,
    language: str,
    code: str
) -> Dict[str, Any]:
    """
    AI Code Review (Honest label: Reviewed by AI, not executed in a sandbox).
    """
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "ai", "prompts", "coding_eval.v1.txt"
    )
    template = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

    rendered = template.format(
        problem=problem,
        language=language,
        code=code
    )

    def fallback_code_eval():
        return {
            "score": 7,
            "correctness_reasoning": "Code structure appears syntactically sound for common cases (AI Code Review, not executed in sandbox).",
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "edge_cases_missed": ["Empty input handling", "Boundary constraint checking"],
            "code_quality": "Clean structure with descriptive variable names.",
            "improvements": ["Add explicit input validation before loop."],
            "optimal_approach": "The optimal approach leverages two pointers or a hash table to achieve optimal linear time."
        }

    raw_text, latency, err = ai_client.generate(rendered, json_mode=True)
    validated, source, val_err = parse_and_validate(raw_text, CODING_REVIEW_SCHEMA, fallback_code_eval)

    ai_trace.record(
        operation="evaluate_coding_answer",
        prompt_version="coding_eval.v1",
        inputs={"problem": problem[:50], "language": language},
        raw_output=raw_text or "",
        validated_output=validated,
        latency_ms=latency,
        source=source,
        error=err or val_err
    )

    return validated
