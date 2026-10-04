"""
Learning Roadmap & Re-Planning Engine
-------------------------------------
Generates personalized phase timelines, estimates completion schedules based on
daily hours, dynamically re-plans on new evidence, and computes career switch diffs.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from core.models import StudentState
from core.repositories.session_repo import data_repo
from core.services.mastery import compute_skill_gaps


def generate_roadmap(student: StudentState) -> Dict[str, Any]:
    """
    Builds personalized roadmap phases tailored to student's skill gaps and study pace.
    """
    careers = data_repo.get_careers()
    career_id = student.goal.career_id
    career_info = careers.get(career_id, careers.get("software_engineer", {}))

    template_phases = career_info.get("roadmap_template", [
        "foundations", "core_concepts", "practical_projects", "mock_interviews"
    ])
    gaps = compute_skill_gaps(student)
    gap_map = {g["skill_id"]: g for g in gaps}

    hours_per_day = max(0.5, student.profile.hours_per_day)
    current_date = datetime.now(timezone.utc)

    roadmap_phases = []
    total_hours_est = 0

    phase_titles = {
        "programming_basics": ("Phase 1: Programming Core", ["python", "cpp", "javascript"], 20),
        "oop_mastery": ("Phase 2: Object-Oriented Principles & Patterns", ["oop"], 25),
        "dsa_core": ("Phase 3: Data Structures & Algorithms", ["dsa"], 40),
        "database_systems": ("Phase 4: Database Systems & SQL", ["dbms", "sql"], 25),
        "computer_systems": ("Phase 5: Operating Systems & Networking", ["os", "networks"], 30),
        "mock_interview_prep": ("Phase 6: Technical Interview Mastery", ["system_design", "dsa"], 20),

        # Data & AI
        "python_for_data": ("Phase 1: Python for Data Science", ["python", "data_analysis"], 25),
        "statistics_prob": ("Phase 2: Statistical Foundations", ["statistics"], 30),
        "data_wrangling_sql": ("Phase 3: Data Wrangling & SQL Analytics", ["sql", "data_analysis"], 30),
        "ml_foundations": ("Phase 4: Classical Machine Learning", ["machine_learning"], 40),
        "deep_learning_intro": ("Phase 5: Deep Learning & Neural Nets", ["deep_learning"], 45),
        "portfolio_projects": ("Phase 6: Capstone Project & Deployment", ["machine_learning", "python"], 30)
    }

    for idx, p_key in enumerate(template_phases):
        title, skills_covered, base_hours = phase_titles.get(
            p_key,
            (f"Phase {idx + 1}: {p_key.replace('_', ' ').title()}", [], 25)
        )

        # Personalize hours based on student gap in these skills
        max_gap = 0.0
        for s in skills_covered:
            if s in gap_map:
                max_gap = max(max_gap, gap_map[s]["gap"])

        # If student already mastered, collapse phase
        if max_gap <= 0.05 and skills_covered:
            status = "completed"
            adjusted_hours = 5
        elif max_gap >= 0.50:
            status = "in_progress" if idx == 0 else "expanded"
            adjusted_hours = int(base_hours * 1.3)
        else:
            status = "in_progress" if idx == 0 else "scheduled"
            adjusted_hours = base_hours

        total_hours_est += adjusted_hours
        days_needed = adjusted_hours / hours_per_day
        end_date = current_date + timedelta(days=days_needed)

        roadmap_phases.append({
            "phase_id": f"phase_{idx+1}_{p_key}",
            "number": idx + 1,
            "title": title,
            "skills_covered": skills_covered,
            "estimated_hours": adjusted_hours,
            "status": status,
            "target_completion": end_date.strftime("%b %d, %Y"),
            "focus_reason": f"Adjusted based on maximum skill gap of {int(max_gap*100)}%" if max_gap > 0 else "Mastery verified"
        })

        current_date = end_date

    total_days = total_hours_est / hours_per_day
    projected_date = (datetime.now(timezone.utc) + timedelta(days=total_days)).strftime("%B %d, %Y")

    return {
        "career_id": career_id,
        "career_title": career_info.get("name", "Software Engineer"),
        "total_estimated_hours": total_hours_est,
        "projected_completion_date": projected_date,
        "phases": roadmap_phases
    }


def compute_career_switch_diff(old_career_id: str, new_career_id: str, student: StudentState) -> Dict[str, Any]:
    """
    Computes comparative diff when student switches goals:
    Shows carryover skills vs new gaps to acquire.
    """
    careers = data_repo.get_careers()
    skills_graph = data_repo.get_skills()

    old_info = careers.get(old_career_id, {})
    new_info = careers.get(new_career_id, {})

    old_skills = {s["skill_id"] for s in old_info.get("skills", [])}
    new_skills = {s["skill_id"] for s in new_info.get("skills", [])}

    carried_over = old_skills.intersection(new_skills)
    new_gaps = new_skills - old_skills

    return {
        "old_career": old_info.get("name", old_career_id),
        "new_career": new_info.get("name", new_career_id),
        "carried_over_count": len(carried_over),
        "carried_over_skills": [skills_graph.get(s, {}).get("name", s) for s in carried_over],
        "new_gaps_count": len(new_gaps),
        "new_gap_skills": [skills_graph.get(s, {}).get("name", s) for s in new_gaps]
    }
