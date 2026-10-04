"""
Onboarding & Profile Initialization Service
--------------------------------------------
Validates multi-step registration wizard, creates student state space,
and handles custom career mapping.
"""

from typing import Dict, Any, Tuple, Optional
from core.models import StudentState, Profile, Goal
from core.repositories.session_repo import data_repo
from ai.client import ai_client
from ai.validator import clean_json_string
import json


def create_initial_student(form_data: Dict[str, Any]) -> StudentState:
    """
    Initializes a new StudentState from onboarding form inputs.
    """
    profile = Profile(
        name=form_data.get("name", "Student").strip() or "Student",
        education=form_data.get("education", "B.Tech"),
        specialization=form_data.get("specialization", "Computer Science"),
        graduation_status=form_data.get("graduation_status", "Pre-final Year"),
        experience_level=form_data.get("experience_level", "Beginner"),
        hours_per_day=float(form_data.get("hours_per_day", 2.0)),
        target_company=form_data.get("target_company", "").strip() or None,
        prep_type=form_data.get("prep_type", "Campus Placements"),
        preferred_learning_style=form_data.get("preferred_learning_style", "Practice & Video"),
        self_rated_skills=[s.strip() for s in form_data.get("skills_raw", "").split(",") if s.strip()]
    )

    career_id = form_data.get("career_id", "software_engineer")
    is_custom = (career_id == "custom")
    custom_desc = form_data.get("custom_career", "").strip()

    careers = data_repo.get_careers()
    if is_custom and custom_desc:
        career_title = custom_desc
        career_group = "Custom Career"
    else:
        career_info = careers.get(career_id, careers.get("software_engineer", {}))
        career_title = career_info.get("name", "Software Engineer")
        career_group = career_info.get("group", "Software Engineering")

    goal = Goal(
        career_id=career_id,
        career_title=career_title,
        career_group=career_group,
        is_custom=is_custom,
        custom_role_description=custom_desc if is_custom else None
    )

    student = StudentState(profile=profile, goal=goal)

    # Initialize baseline self-rated skills if entered
    for s_name in profile.self_rated_skills:
        s_key = s_name.lower().replace(" ", "_").replace("+", "p")
        student.skills[s_key] = {
            "name": s_name,
            "mastery": 0.40 if profile.experience_level != "Beginner" else 0.25,
            "confidence": 0.20,
            "attempts": 1,
            "trend": "stable"
        }

    return student


def map_custom_career(custom_role_text: str) -> Dict[str, Any]:
    """
    AI mapping of free-text custom career to known skills and group.
    """
    skills_graph = data_repo.get_skills()
    known_skills = list(skills_graph.keys())

    prompt = f"""Map the custom career role '{custom_role_text}' to the closest technical skills and parent career group.
Known Skills: {', '.join(known_skills)}

Return ONLY valid JSON:
{{
    "career_title": "{custom_role_text}",
    "group": "Software Engineering",
    "relevant_skills": ["python", "dsa"]
}}"""

    raw_text, _, err = ai_client.generate(prompt=prompt, json_mode=True)
    if raw_text and not err:
        try:
            return json.loads(clean_json_string(raw_text))
        except Exception:
            pass

    # Deterministic fallback
    return {
        "career_title": custom_role_text,
        "group": "Software Engineering",
        "relevant_skills": ["python", "dsa", "oop", "dbms"]
    }
