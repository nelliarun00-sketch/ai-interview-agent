"""
Adaptive Diagnostic Assessment Service
---------------------------------------
Generates career-specific diagnostic question sets, deterministically scores
MCQs, updates Bayesian skill mastery, and estimates student proficiency level.
"""

from typing import Dict, Any, List
from core.models import StudentState
from core.repositories.session_repo import data_repo
from core.services.mastery import calculate_mastery_update


def get_diagnostic_questions_for_goal(career_id: str) -> List[Dict[str, Any]]:
    """
    Selects 10 career-aligned diagnostic questions covering core required skills.
    """
    all_q_data = data_repo.get_question_bank()
    diag_pool = all_q_data.get("diagnostic", [])
    careers = data_repo.get_careers()

    career_info = careers.get(career_id, careers.get("software_engineer", {}))
    target_skill_ids = {s["skill_id"] for s in career_info.get("skills", [])}

    # Match questions relevant to this career's skills
    matched = [q for q in diag_pool if q.get("skill_id") in target_skill_ids]

    # Fill remaining from general pool if needed to reach up to 10
    if len(matched) < 10:
        remaining = [q for q in diag_pool if q not in matched]
        matched.extend(remaining[:(10 - len(matched))])

    return matched[:10]


def evaluate_diagnostic_submission(
    student: StudentState,
    answers: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministically scores diagnostic submission and updates student state.
    """
    questions = get_diagnostic_questions_for_goal(student.goal.career_id)
    skills_graph = data_repo.get_skills()

    total_questions = len(questions)
    correct_count = 0
    per_skill_performance: Dict[str, List[float]] = {}
    detailed_results = []

    for q in questions:
        q_id = q["id"]
        skill_id = q["skill_id"]
        correct_opt = q.get("correct_option")

        user_ans = answers.get(q_id)
        is_correct = False

        if user_ans is not None:
            try:
                is_correct = (int(user_ans) == int(correct_opt))
            except (ValueError, TypeError):
                is_correct = False

        score_norm = 1.0 if is_correct else 0.0
        if is_correct:
            correct_count += 1

        if skill_id not in per_skill_performance:
            per_skill_performance[skill_id] = []
        per_skill_performance[skill_id].append(score_norm)

        detailed_results.append({
            "question_id": q_id,
            "skill_id": skill_id,
            "skill_name": skills_graph.get(skill_id, {}).get("name", skill_id),
            "question": q["question"],
            "options": q["options"],
            "selected_option": int(user_ans) if user_ans is not None else None,
            "correct_option": correct_opt,
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })

    # Update knowledge tracing for each tested skill
    for skill_id, scores in per_skill_performance.items():
        avg_score = sum(scores) / len(scores)
        curr_data = student.skills.get(skill_id, {"mastery": 0.25, "confidence": 0.1, "attempts": 0})

        update_info = calculate_mastery_update(
            current_mastery=float(curr_data.get("mastery", 0.25)),
            current_confidence=float(curr_data.get("confidence", 0.1)),
            attempts=int(curr_data.get("attempts", 0)),
            observed_score=avg_score,
            difficulty="medium"
        )
        update_info["name"] = skills_graph.get(skill_id, {}).get("name", skill_id)
        student.skills[skill_id] = update_info

    # Estimate overall proficiency level
    percentage = (correct_count / total_questions * 100.0) if total_questions > 0 else 0
    if percentage >= 75.0:
        estimated_level = "Advanced"
    elif percentage >= 45.0:
        estimated_level = "Intermediate"
    else:
        estimated_level = "Beginner"

    student.profile.experience_level = estimated_level

    return {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "score_percentage": round(percentage, 1),
        "estimated_level": estimated_level,
        "detailed_results": detailed_results,
        "updated_skills": student.skills
    }
