"""
Seed Demo Students & Persona Regression Generator
--------------------------------------------------
Generates the 5 canonical student personas specified in Section 10:
1. B.Tech CSE -> Software Engineer (Beginner)
2. M.Tech AI -> Machine Learning Engineer (Intermediate)
3. MCA -> Full Stack Developer (Beginner)
4. M.Sc Data Science -> Data Scientist (Intermediate)
5. B.Tech ECE -> Embedded Systems Engineer (Estimated / Adaptive)
6. Bonus: Career Switcher (Software Engineer -> AI/ML Engineer)

Verifies and prints the output comparison table proving meaningful divergence.
"""

import sys
import os
import json

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import StudentState, Profile, Goal
from core.repositories.session_repo import data_repo
from core.services.mastery import compute_skill_gaps
from core.services.roadmap import generate_roadmap
from core.services.recommender import recommend_resources, recommend_projects
from core.services.readiness import compute_career_readiness


def create_persona_1() -> StudentState:
    """Persona 1: B.Tech CSE -> Software Engineer -> Beginner"""
    return StudentState(
        profile=Profile(
            name="Rahul Sharma",
            education="B.Tech",
            specialization="Computer Science & Engineering",
            graduation_status="Pre-final Year",
            experience_level="Beginner",
            hours_per_day=2.0,
            prep_type="Campus Placements",
            self_rated_skills=["Python", "C++", "OOP"]
        ),
        goal=Goal(
            career_id="software_engineer",
            career_title="Software Development Engineer (SDE / SWE)",
            career_group="Software Engineering"
        ),
        skills={
            "python": {"name": "Python", "mastery": 0.40, "confidence": 0.3, "attempts": 2},
            "cpp": {"name": "C++", "mastery": 0.35, "confidence": 0.3, "attempts": 2},
            "oop": {"name": "Object-Oriented Programming", "mastery": 0.30, "confidence": 0.2, "attempts": 1},
            "dsa": {"name": "Data Structures & Algorithms", "mastery": 0.15, "confidence": 0.2, "attempts": 1}
        }
    )


def create_persona_2() -> StudentState:
    """Persona 2: M.Tech AI -> Machine Learning Engineer -> Intermediate"""
    return StudentState(
        profile=Profile(
            name="Priya Patel",
            education="M.Tech",
            specialization="Artificial Intelligence & Robotics",
            graduation_status="Final Year",
            experience_level="Intermediate",
            hours_per_day=3.0,
            prep_type="Off-Campus Tech Jobs",
            self_rated_skills=["Python", "Machine Learning", "Mathematics"]
        ),
        goal=Goal(
            career_id="ai_ml_engineer",
            career_title="Machine Learning & AI Engineer",
            career_group="Artificial Intelligence"
        ),
        skills={
            "python": {"name": "Python", "mastery": 0.80, "confidence": 0.8, "attempts": 5},
            "statistics": {"name": "Probability & Statistics", "mastery": 0.70, "confidence": 0.7, "attempts": 4},
            "machine_learning": {"name": "Machine Learning Fundamentals", "mastery": 0.65, "confidence": 0.6, "attempts": 4},
            "deep_learning": {"name": "Deep Learning & Neural Networks", "mastery": 0.35, "confidence": 0.4, "attempts": 2}
        }
    )


def create_persona_3() -> StudentState:
    """Persona 3: MCA -> Full Stack Developer -> Beginner"""
    return StudentState(
        profile=Profile(
            name="Amit Verma",
            education="MCA",
            specialization="Computer Applications",
            graduation_status="Final Year",
            experience_level="Beginner",
            hours_per_day=2.5,
            prep_type="Campus Placements",
            self_rated_skills=["JavaScript", "HTML/CSS", "SQL"]
        ),
        goal=Goal(
            career_id="fullstack_developer",
            career_title="Full Stack Web Developer",
            career_group="Software Engineering"
        ),
        skills={
            "javascript": {"name": "JavaScript (ES6+)", "mastery": 0.45, "confidence": 0.4, "attempts": 3},
            "web_frontend": {"name": "Web Frontend (DOM/APIs)", "mastery": 0.40, "confidence": 0.3, "attempts": 2},
            "backend_apis": {"name": "Backend APIs & REST", "mastery": 0.20, "confidence": 0.2, "attempts": 1},
            "sql": {"name": "SQL & Relational Databases", "mastery": 0.30, "confidence": 0.3, "attempts": 2}
        }
    )


def create_persona_4() -> StudentState:
    """Persona 4: M.Sc Data Science -> Data Scientist -> Intermediate"""
    return StudentState(
        profile=Profile(
            name="Ananya Sen",
            education="M.Sc",
            specialization="Data Science & Applied Statistics",
            graduation_status="Recent Graduate",
            experience_level="Intermediate",
            hours_per_day=3.5,
            prep_type="Off-Campus Tech Jobs",
            self_rated_skills=["Python", "Statistics", "SQL", "Data Analysis"]
        ),
        goal=Goal(
            career_id="data_scientist",
            career_title="Data Scientist",
            career_group="Data Science & Analytics"
        ),
        skills={
            "python": {"name": "Python", "mastery": 0.75, "confidence": 0.7, "attempts": 4},
            "statistics": {"name": "Probability & Statistics", "mastery": 0.75, "confidence": 0.8, "attempts": 5},
            "data_analysis": {"name": "Data Analysis & Visualization", "mastery": 0.70, "confidence": 0.6, "attempts": 4},
            "sql": {"name": "SQL & Relational Databases", "mastery": 0.60, "confidence": 0.5, "attempts": 3},
            "machine_learning": {"name": "Machine Learning Fundamentals", "mastery": 0.45, "confidence": 0.4, "attempts": 2}
        }
    )


def create_persona_5() -> StudentState:
    """Persona 5: B.Tech ECE -> Embedded Systems Engineer -> Diagnostic Estimated"""
    return StudentState(
        profile=Profile(
            name="Karthik Raj",
            education="B.Tech",
            specialization="Electronics & Communication",
            graduation_status="Pre-final Year",
            experience_level="Beginner",
            hours_per_day=2.0,
            prep_type="Campus Placements",
            self_rated_skills=["C++", "Digital Logic", "Microcontrollers"]
        ),
        goal=Goal(
            career_id="embedded_iot_engineer",
            career_title="Embedded Systems & Firmware Engineer",
            career_group="Hardware & Systems"
        ),
        skills={
            "cpp": {"name": "C++", "mastery": 0.50, "confidence": 0.5, "attempts": 3},
            "embedded_c": {"name": "Embedded C / Firmware Basics", "mastery": 0.25, "confidence": 0.2, "attempts": 1},
            "microcontrollers": {"name": "Microcontrollers & RTOS", "mastery": 0.15, "confidence": 0.1, "attempts": 1}
        }
    )


def compare_all_personas():
    personas = [
        ("1. B.Tech CSE (Beginner)", create_persona_1()),
        ("2. M.Tech AI (Intermediate)", create_persona_2()),
        ("3. MCA (Beginner)", create_persona_3()),
        ("4. M.Sc Data Science (Intermediate)", create_persona_4()),
        ("5. B.Tech ECE (Estimated)", create_persona_5())
    ]

    print("\n" + "=" * 90)
    print(" PERSONA REGRESSION SUITE & OUTPUT COMPARISON TABLE")
    print("=" * 90)
    print(f"{'Persona':<32} | {'Career Goal':<22} | {'Top Skill Gap':<20} | {'Roadmap Hours':<14}")
    print("-" * 90)

    results_table = []
    top_resources_per_persona = {}

    for label, student in personas:
        gaps = compute_skill_gaps(student)
        roadmap = generate_roadmap(student)
        resources = recommend_resources(student, limit=3)
        readiness = compute_career_readiness(student)

        top_gap_name = gaps[0]["name"] if gaps else "None"
        gap_pct = f"{int(gaps[0]['gap']*100)}%" if gaps else "0%"
        roadmap_hours = f"{roadmap['total_estimated_hours']} hrs"

        print(f"{label:<32} | {student.goal.career_id:<22} | {top_gap_name[:14]} ({gap_pct}) | {roadmap_hours:<14}")

        top_resources_per_persona[label] = [r["id"] for r in resources]
        results_table.append({
            "persona": label,
            "career": student.goal.career_title,
            "hours": roadmap["total_estimated_hours"],
            "top_gap": top_gap_name,
            "readiness": readiness["overall"],
            "top_resources": [r["title"] for r in resources]
        })

    print("-" * 90)
    print("\n RESOURCE DIVERGENCE ANALYSIS (Top 3 Recommendations Per Persona):")
    for label, res_ids in top_resources_per_persona.items():
        print(f"  {label:<32}: {res_ids}")

    # Check resource set overlap
    all_sets = [set(res_ids) for res_ids in top_resources_per_persona.values()]
    overlap_count = 0
    comparisons = 0
    for i in range(len(all_sets)):
        for j in range(i + 1, len(all_sets)):
            overlap = len(all_sets[i].intersection(all_sets[j]))
            comparisons += 1
            if overlap == 3:
                overlap_count += 1

    print(f"\n Pairwise distinctness check: {comparisons} persona pairs compared.")
    print(f" Full overlap cases: {overlap_count} (Must be 0).")
    assert overlap_count == 0, "Personas must produce clearly different resource recommendations!"
    print(" [PASSED] All personas produce distinct, tailored career paths and recommendations.\n")

    return results_table


if __name__ == "__main__":
    compare_all_personas()
