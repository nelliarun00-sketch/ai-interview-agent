"""
Career Readiness Score & Diagnostic Analytics
---------------------------------------------
Computes multi-dimensional readiness index using transparent weights,
supports weight re-normalization for unmeasured components, and recommends
top 3 actions ranked by expected score gain.
"""

from typing import Dict, Any, List
from config import config
from core.models import StudentState
from core.repositories.session_repo import data_repo
from core.services.mastery import compute_skill_gaps


def compute_career_readiness(student: StudentState) -> Dict[str, Any]:
    """
    Computes overall readiness score (0-100%) with component breakdowns.
    Formula:
    readiness = 0.30*technical + 0.15*projects + 0.20*interview + 0.15*resume + 0.10*communication + 0.10*learning_progress
    """
    weights = config.READINESS_WEIGHTS

    # 1. Technical Mastery Component
    gaps = compute_skill_gaps(student)
    if gaps:
        avg_mastery = sum(g["current_mastery"] for g in gaps) / len(gaps)
        tech_score = avg_mastery * 100.0
        tech_measured = True
    else:
        tech_score = 0.0
        tech_measured = False

    # 2. Projects Component
    completed_projects = sum(1 for status in student.project_status.values() if status == "Done")
    proj_score = min(100.0, (completed_projects / 2.0) * 100.0)
    proj_measured = len(student.project_status) > 0

    # 3. Interview Component
    interviews = student.interviews
    if interviews:
        avg_interview = sum(i.get("overall_score", 0.0) for i in interviews) / len(interviews)
        interview_score = avg_interview * 10.0 # Scale 0-10 to 0-100
        interview_measured = True
    else:
        interview_score = 0.0
        interview_measured = False

    # 4. Resume Component
    if student.resume_analysis:
        resume_score = float(student.resume_analysis.get("ats_score", 70))
        resume_measured = True
    else:
        resume_score = 0.0
        resume_measured = False

    # 5. Communication Component
    all_turns = []
    for inv in interviews:
        all_turns.extend(inv.get("turns", []))
    if all_turns:
        comm_scores = [t.get("score", 5) for t in all_turns]
        comm_score = (sum(comm_scores) / len(comm_scores)) * 10.0
        comm_measured = True
    else:
        comm_score = 0.0
        comm_measured = False

    # 6. Learning Progress Component
    completed_resources = sum(1 for r in student.resources.values() if r.get("status") == "completed")
    learn_score = min(100.0, (completed_resources / 4.0) * 100.0)
    learn_measured = len(student.resources) > 0

    components = {
        "technical": {"score": round(tech_score, 1), "weight": weights["technical"], "measured": tech_measured, "label": "Technical Skill Mastery"},
        "projects": {"score": round(proj_score, 1), "weight": weights["projects"], "measured": proj_measured, "label": "Practical Portfolio"},
        "interview": {"score": round(interview_score, 1), "weight": weights["interview"], "measured": interview_measured, "label": "Mock Interview Performance"},
        "resume": {"score": round(resume_score, 1), "weight": weights["resume"], "measured": resume_measured, "label": "ATS Resume Screening"},
        "communication": {"score": round(comm_score, 1), "weight": weights["communication"], "measured": comm_measured, "label": "Communication & Clarity"},
        "learning_progress": {"score": round(learn_score, 1), "weight": weights["learning_progress"], "measured": learn_measured, "label": "Curriculum Syllabus Progress"}
    }

    # Weight Re-Normalization for unmeasured items
    active_weight_sum = sum(c["weight"] for c in components.values() if c["measured"])
    if active_weight_sum > 0:
        weighted_total = sum(c["score"] * (c["weight"] / active_weight_sum) for c in components.values() if c["measured"])
    else:
        weighted_total = 0.0

    final_readiness = round(weighted_total, 1)

    # Readiness Category
    if final_readiness >= 80.0:
        readiness_badge = "Placement Ready (FAANG / Tier 1)"
    elif final_readiness >= 60.0:
        readiness_badge = "Competitive Candidate"
    elif final_readiness >= 40.0:
        readiness_badge = "Foundation Developing"
    else:
        readiness_badge = "Diagnostic Required"

    # Top 3 High-Impact Improvement Actions ranked by potential readiness gain
    actions = []
    if not tech_measured or tech_score < 70.0:
        actions.append({
            "title": "Complete Skill Diagnostic & Practice Weak Areas",
            "expected_gain": "+15-20 pts",
            "link": "/assessment"
        })
    if not interview_measured or interview_score < 70.0:
        actions.append({
            "title": "Complete Full 5-Turn Mock Technical Interview",
            "expected_gain": "+12-18 pts",
            "link": "/interview"
        })
    if not resume_measured:
        actions.append({
            "title": "Upload & Screen Resume with ATS Checker",
            "expected_gain": "+10-15 pts",
            "link": "/resume"
        })
    if not proj_measured:
        actions.append({
            "title": "Start Milestone 1 of Recommended Portfolio Project",
            "expected_gain": "+10 pts",
            "link": "/projects"
        })

    return {
        "overall_readiness": final_readiness,
        "overall": final_readiness,
        "badge": readiness_badge,
        "components": components,
        "improvement_actions": actions[:3],
        "recommendations": [f"{a['title']} (Expected gain: {a['expected_gain']})" for a in actions[:3]]
    }
