"""
Knowledge Tracing, Skill Graph & Mastery Decay
----------------------------------------------
Implements Bayesian / exponential-moving-average mastery estimation,
confidence calculation, forgetting decay, and prerequisite graph traversal.
NO RANDOM NUMBERS - Completely deterministic and explainable.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from config import config
from core.models import StudentState, SkillMastery
from core.repositories.session_repo import data_repo


def calculate_mastery_update(
    current_mastery: float,
    current_confidence: float,
    attempts: int,
    observed_score: float,   # Normalized 0.0 to 1.0
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """
    Bayesian Knowledge Tracing / Exponential Moving Average update formula:
    mastery_new = mastery_old + alpha * (observed_score - mastery_old) * difficulty_weight
    """
    # Difficulty weighting rewards harder items more than easy items
    difficulty_weights = {"easy": 0.8, "medium": 1.0, "hard": 1.25}
    diff_weight = difficulty_weights.get(difficulty.lower(), 1.0)

    # Learning rate alpha stabilizes as evidence (attempts) accumulates
    alpha = max(0.15, config.MASTERY_ALPHA_INITIAL / (1.0 + 0.25 * attempts))

    # Update mastery
    delta = alpha * (observed_score - current_mastery) * diff_weight
    new_mastery = max(0.0, min(1.0, current_mastery + delta))

    # Confidence grows with number of attempts
    new_attempts = attempts + 1
    new_confidence = min(1.0, new_attempts / float(config.MIN_EVIDENCE_ATTEMPTS))

    # Determine trend
    if observed_score > current_mastery + 0.1:
        trend = "improving"
    elif observed_score < current_mastery - 0.1:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "mastery": round(new_mastery, 3),
        "confidence": round(new_confidence, 2),
        "attempts": new_attempts,
        "trend": trend,
        "last_seen": datetime.now(timezone.utc).isoformat()
    }


def apply_forgetting_decay(mastery_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies forgetting curve decay based on days elapsed since last practice.
    mastery_decayed = mastery * (1 - decay_rate * days_elapsed)
    """
    last_seen_str = mastery_data.get("last_seen")
    if not last_seen_str:
        return mastery_data

    try:
        last_dt = datetime.fromisoformat(last_seen_str)
        now_dt = datetime.now(timezone.utc)
        days_elapsed = max(0, (now_dt - last_dt).total_seconds() / 86400.0)

        current_mastery = float(mastery_data.get("mastery", 0.0))
        decay_factor = max(0.5, 1.0 - (config.MASTERY_DECAY_RATE_PER_DAY * days_elapsed))
        decayed_mastery = round(current_mastery * decay_factor, 3)

        result = dict(mastery_data)
        result["mastery"] = decayed_mastery
        return result
    except Exception:
        return mastery_data


def check_prerequisites(skill_id: str, student_skills: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if student has satisfied all prerequisites for a given skill.
    """
    all_skills = data_repo.get_skills()
    skill_info = all_skills.get(skill_id, {})
    prereqs = skill_info.get("prerequisites", [])

    missing = []
    satisfied = True

    for p in prereqs:
        p_mastery = student_skills.get(p, {}).get("mastery", 0.0)
        if p_mastery < 0.60:
            satisfied = False
            missing.append({
                "prerequisite_id": p,
                "name": all_skills.get(p, {}).get("name", p),
                "current_mastery": p_mastery,
                "required_mastery": 0.60
            })

    return {
        "satisfied": satisfied,
        "prerequisites": prereqs,
        "unmet_prerequisites": missing,
        "missing": missing
    }


def compute_skill_gaps(student: StudentState) -> List[Dict[str, Any]]:
    """
    Calculates exact skill gap analysis comparing student state vs target career requirements.
    Gap Priority = Career Skill Weight * max(0, Required Mastery - Current Mastery)
    """
    careers = data_repo.get_careers()
    skills_graph = data_repo.get_skills()

    career_id = student.goal.career_id
    career = careers.get(career_id, careers.get("software_engineer", {}))
    required_skills = career.get("skills", [])

    gaps = []
    for item in required_skills:
        s_id = item["skill_id"]
        weight = item.get("weight", 0.8)
        req_mastery = item.get("required_mastery", 0.70)

        # Get student mastery (apply forgetting decay)
        raw_skill_data = student.skills.get(s_id, {"mastery": 0.0, "confidence": 0.1, "attempts": 0})
        skill_data = apply_forgetting_decay(raw_skill_data)
        curr_mastery = skill_data.get("mastery", 0.0)
        confidence = skill_data.get("confidence", 0.1)

        gap_value = max(0.0, req_mastery - curr_mastery)
        priority_score = round(weight * gap_value, 3)

        # Prerequisite check
        prereq_check = check_prerequisites(s_id, student.skills)

        # Level tag
        if curr_mastery >= req_mastery:
            status = "mastered"
        elif curr_mastery >= 0.40:
            status = "in_progress"
        else:
            status = "critical_gap"

        gaps.append({
            "skill_id": s_id,
            "name": skills_graph.get(s_id, {}).get("name", s_id.capitalize()),
            "category": skills_graph.get(s_id, {}).get("category", "General"),
            "current_mastery": curr_mastery,
            "required_mastery": req_mastery,
            "current": curr_mastery,
            "required": req_mastery,
            "gap": round(gap_value, 3),
            "priority": priority_score,
            "confidence": confidence,
            "attempts": skill_data.get("attempts", 0),
            "status": status,
            "prerequisites_satisfied": prereq_check["satisfied"]
        })

    # Sort gaps by priority descending
    gaps.sort(key=lambda x: x["priority"], reverse=True)
    return gaps
