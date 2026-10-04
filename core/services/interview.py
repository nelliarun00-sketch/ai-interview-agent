"""
Adaptive Mock Interview Engine
------------------------------
Manages interview sessions, session memory, topic selection with recency penalties,
probing questions, and difficulty adaptation.
"""

from typing import Dict, Any, List, Optional
import os
from core.models import StudentState, InterviewSession, InterviewTurn
from core.repositories.session_repo import data_repo
from core.services.mastery import compute_skill_gaps, calculate_mastery_update
from ai.client import ai_client
from ai.validator import parse_and_validate
from ai.schemas import QUESTION_GEN_SCHEMA
from ai.trace import ai_trace


def start_interview_session(
    student: StudentState,
    mode: str = "technical",
    difficulty: str = "medium"
) -> InterviewSession:
    """Initializes a new interview session."""
    session = InterviewSession(
        mode=mode,
        role=student.goal.career_title,
        difficulty=difficulty,
        turns=[]
    )
    return session


def select_next_interview_topic(student: StudentState, turns: List[Dict[str, Any]]) -> str:
    """
    Selects next topic using adaptive selection:
    argmax( weakness * recency_penalty * goal_weight )
    """
    gaps = compute_skill_gaps(student)
    if not gaps:
        return "python"

    recent_topics = [t.get("topic") for t in turns[-3:]]

    best_score = -1.0
    best_topic = gaps[0]["skill_id"]

    for g in gaps:
        s_id = g["skill_id"]
        weakness = g["gap"]
        priority = g["priority"]

        # Recency penalty reduces chance of asking same topic consecutively
        recency_penalty = 0.3 if s_id in recent_topics else 1.0
        score = (weakness * 0.6 + priority * 0.4) * recency_penalty

        if score > best_score:
            best_score = score
            best_topic = s_id

    return best_topic


def generate_interview_question(
    student: StudentState,
    session: InterviewSession,
    topic: str
) -> Dict[str, Any]:
    """
    Generates next question via Gemini AI or seed bank fallback.
    """
    previous_turn = session.turns[-1] if session.turns else None
    recent_score = previous_turn.get("score") if previous_turn else None
    prev_questions = [t.get("question", "") for t in session.turns]

    # Read prompt template
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "ai", "prompts", "question_gen.v1.txt"
    )
    template = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

    rendered_prompt = ""
    if template:
        try:
            rendered_prompt = template.format(
                job_role=session.role,
                skills=", ".join(student.skills.keys()) or "General technical skills",
                focus_area=topic,
                difficulty=session.difficulty,
                previous_questions="\n".join(prev_questions) if prev_questions else "None (First Question)",
                recent_score=f"{recent_score}/10" if recent_score is not None else "N/A"
            )
        except Exception:
            rendered_prompt = f"Role: {session.role}, Focus: {topic}, Difficulty: {session.difficulty}. Generate technical interview question."

    def fallback_question():
        seed_data = data_repo.get_question_bank().get("interview_seed", {})
        topic_seeds = seed_data.get(topic, seed_data.get("python", []))
        idx = len(session.turns) % max(1, len(topic_seeds))
        q_text = topic_seeds[idx] if topic_seeds else f"Explain the core technical principles of {topic} and give an example."
        return {
            "question": q_text,
            "topic": topic,
            "difficulty": session.difficulty,
            "expected_concepts": [topic]
        }

    raw_text, latency, err = ai_client.generate(rendered_prompt, json_mode=True)
    validated, source, val_err = parse_and_validate(raw_text, QUESTION_GEN_SCHEMA, fallback_question)

    if not isinstance(validated, dict) or "question" not in validated or not validated["question"]:
        fb = fallback_question()
        if isinstance(validated, dict):
            validated["question"] = fb["question"]
            validated.setdefault("topic", topic)
            validated.setdefault("difficulty", session.difficulty)
        else:
            validated = fb

    ai_trace.record(
        operation="generate_interview_question",
        prompt_version="question_gen.v1",
        inputs={"role": session.role, "topic": topic, "difficulty": session.difficulty},
        raw_output=raw_text or "",
        validated_output=validated,
        latency_ms=latency,
        source=source,
        error=err or val_err
    )

    return validated
