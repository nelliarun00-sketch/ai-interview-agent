"""
Hybrid Recommendation Engine (Grounded & Anti-Hallucination)
-----------------------------------------------------------
Implements multi-factor mathematical scoring for learning resources,
projects, and certifications. Every recommendation cites canonical data IDs
and includes transparent rationale.
"""

from typing import List, Dict, Any, Set
from config import config
from core.models import StudentState
from core.repositories.session_repo import data_repo
from core.services.mastery import compute_skill_gaps, check_prerequisites


def recommend_resources(student: StudentState, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Ranks library resources using transparent multi-criteria formula:
    score = w1*gap_priority + w2*prereq_fit + w3*level_fit + w4*cost_fit + w5*time_fit + w6*quality - w7*completed
    """
    all_resources = data_repo.get_resources()
    gaps = compute_skill_gaps(student)
    gap_map = {g["skill_id"]: g for g in gaps}

    student_level = student.profile.experience_level.lower()
    weights = config.RECOMMENDER_WEIGHTS

    scored = []
    for res in all_resources:
        res_skills = res.get("skill_ids", [])
        res_level = res.get("level", "Beginner").lower()
        res_cost = res.get("cost", "free").lower()
        res_minutes = res.get("estimated_time_minutes", 120)
        source_type = res.get("source_type", "platform")
        r_id = res["id"]

        # Check if already completed
        progress = student.resources.get(r_id, {})
        is_completed = (progress.get("status") == "completed")

        # 1. Gap Priority
        highest_gap = 0.0
        primary_gap_skill = None
        for s in res_skills:
            if s in gap_map:
                if gap_map[s]["priority"] > highest_gap:
                    highest_gap = gap_map[s]["priority"]
                    primary_gap_skill = gap_map[s]

        # 2. Prerequisite Readiness
        prereq_ready = True
        for s in res_skills:
            p_check = check_prerequisites(s, student.skills)
            if not p_check["satisfied"]:
                prereq_ready = False
                break
        prereq_score = 1.0 if prereq_ready else 0.2

        # 3. Level fit
        level_score = 1.0 if res_level == student_level else (0.7 if "intermediate" in (res_level, student_level) else 0.4)

        # 4. Cost fit (Students strongly prefer free/official)
        cost_score = 1.0 if res_cost == "free" else (0.8 if res_cost == "freemium" else 0.5)

        # 5. Quality (official docs & university materials carry higher weight)
        quality_score = 1.0 if source_type in ("official", "university") else 0.8

        # 6. Time fit
        daily_minutes = student.profile.hours_per_day * 60
        time_score = 1.0 if res_minutes <= (daily_minutes * 2) else 0.7

        # Career relevance bonus
        career_bonus = 0.35 if student.goal.career_id in res.get("recommended_for", []) else 0.0

        # Total Composite Score
        composite_score = (
            weights["gap_priority"] * (highest_gap * 1.2) +
            weights["prerequisite_readiness"] * prereq_score +
            weights["level_fit"] * level_score +
            weights["cost_fit"] * cost_score +
            weights["quality"] * quality_score +
            weights["time_fit"] * time_score +
            career_bonus
        )

        if is_completed:
            composite_score -= 0.5

        # Build Explainable Reasoning String
        if primary_gap_skill:
            reason = f"Recommended because {primary_gap_skill['name']} mastery is {int(primary_gap_skill['current_mastery']*100)}% (target: {int(primary_gap_skill['required_mastery']*100)}%)."
        elif prereq_ready:
            reason = f"Builds strong foundational prerequisites for your {student.goal.career_title} roadmap."
        else:
            reason = "Recommended for general technical development."

        item = dict(res)
        item["recommendation_score"] = round(composite_score, 3)
        item["why_recommended"] = reason
        item["is_bookmarked"] = progress.get("bookmarked", False)
        item["progress_status"] = progress.get("status", "not_started")
        scored.append(item)

    scored.sort(key=lambda x: x["recommendation_score"], reverse=True)
    return scored[:limit]


def recommend_projects(student: StudentState, limit: int = 4) -> List[Dict[str, Any]]:
    """Ranks project portfolio recommendations matching student skill gaps."""
    projects = data_repo.get_projects()
    gaps = compute_skill_gaps(student)
    gap_skills = {g["skill_id"] for g in gaps if g["gap"] > 0.15}

    scored = []
    for proj in projects:
        proj_skills = set(proj.get("skills", []))
        overlap = len(proj_skills.intersection(gap_skills))

        # Check status
        status = student.project_status.get(proj["id"], "Planned")

        score = overlap * 1.5
        if student.goal.career_id in proj.get("career_ids", []):
            score += 2.0

        p = dict(proj)
        p["score"] = score
        p["status"] = status
        scored.append(p)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def recommend_certifications(student: StudentState, limit: int = 4) -> List[Dict[str, Any]]:
    """Ranks certifications and courses by relevance to career goal."""
    all_certs = data_repo.get_certifications()
    career_id = student.goal.career_id

    matched = []
    for c in all_certs:
        c_careers = c.get("career_ids", [])
        is_direct = (career_id in c_careers)

        c_item = dict(c)
        c_item["is_direct_match"] = is_direct
        matched.append(c_item)

    matched.sort(key=lambda x: x["is_direct_match"], reverse=True)
    return matched[:limit]
