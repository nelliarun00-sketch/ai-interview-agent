import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Comprehensive Automated Test Suite (pytest) - AI Career Operating System (v2)
=============================================================================
Tests:
1. Mathematical Mastery & Bayesian Knowledge Tracing (no random numbers)
2. Ebbinghaus-Lite Forgetting Decay
3. Skill Gap Priority Computation (weight * gap)
4. Career Readiness Formula & Weight Re-Normalization
5. Recommender Scoring & Prerequisite Gating
6. Daily Action Plan & Spaced Scheduler
7. AI Schema Validator & Anti-Hallucination Filter
8. Canonical Data Graph Integrity (No dead references or duplicate IDs)
9. Flask Blueprint Route Coverage (Status 200 checks)
10. Persona Regression & Recommendation Divergence
"""

import pytest
import json
import os
from datetime import datetime, timedelta, timezone

from core.models import StudentState, Profile, Goal
from core.repositories.session_repo import data_repo, student_repo
from core.services.mastery import (
    calculate_mastery_update,
    apply_forgetting_decay,
    compute_skill_gaps,
    check_prerequisites
)
from core.services.readiness import compute_career_readiness
from core.services.recommender import recommend_resources, recommend_projects, recommend_certifications
from core.services.planner import generate_daily_plan
from core.services.roadmap import generate_roadmap, compute_career_switch_diff
from ai.validator import parse_and_validate, clean_json_string
from ai.schemas import ANSWER_EVAL_SCHEMA
from app import create_app


# -------------------------------------------------------------
# 1. Knowledge Tracing & Mastery Tests
# -------------------------------------------------------------
def test_mastery_update_formula():
    """Verify Bayesian EMA update: mastery_new = mastery_old + alpha * (score - mastery_old) * diff_weight"""
    # Baseline beginner with low attempts (high alpha)
    res = calculate_mastery_update(
        current_mastery=0.20,
        current_confidence=0.10,
        attempts=0,
        observed_score=1.0,
        difficulty="hard"
    )
    assert res["mastery"] > 0.20, "Mastery must increase after perfect score"
    assert res["confidence"] > 0.10, "Confidence must increase with new evidence"
    assert res["attempts"] == 1
    assert res["trend"] == "improving"

    # Failing a question lowers mastery
    res_drop = calculate_mastery_update(
        current_mastery=0.70,
        current_confidence=0.50,
        attempts=3,
        observed_score=0.0,
        difficulty="easy"
    )
    assert res_drop["mastery"] < 0.70, "Mastery must decrease after failure"
    assert res_drop["trend"] == "declining"


def test_mastery_decay():
    """Verify forgetting decay applies based on elapsed days"""
    now = datetime.now(timezone.utc)
    ten_days_ago = (now - timedelta(days=10)).isoformat()

    decayed = apply_forgetting_decay({"mastery": 0.80, "last_seen": ten_days_ago})
    assert decayed["mastery"] < 0.80, "Mastery must decay after 10 days of inactivity"
    assert decayed["mastery"] > 0.40, "Decay should be gradual, not instantaneous drop"


def test_skill_gap_priority():
    """Verify skill gap priority = weight * gap"""
    student = StudentState(
        goal=Goal(career_id="software_engineer", career_title="Software Engineer"),
        skills={"dsa": {"name": "DSA", "mastery": 0.20, "confidence": 0.5, "attempts": 2}}
    )
    gaps = compute_skill_gaps(student)
    assert len(gaps) > 0

    dsa_gap = next((g for g in gaps if g["skill_id"] == "dsa"), None)
    assert dsa_gap is not None
    # For software_engineer: DSA weight = 1.0, required = 0.75. Current = 0.20 -> gap = 0.55
    assert round(dsa_gap["gap"], 2) == 0.55
    assert round(dsa_gap["priority"], 2) == round(1.0 * 0.55, 2)


# -------------------------------------------------------------
# 2. Career Readiness Formula & Weight Re-Normalization
# -------------------------------------------------------------
def test_readiness_weight_renormalization():
    """Verify unmeasured components are excluded with proper weight re-normalization"""
    student = StudentState()
    # With zero inputs, components are unmeasured
    readiness_empty = compute_career_readiness(student)
    assert "overall_readiness" in readiness_empty
    assert readiness_empty["overall_readiness"] == 0.0

    # Add only technical mastery
    student.skills["python"] = {"name": "Python", "mastery": 0.80, "confidence": 0.5, "attempts": 2}
    readiness_tech = compute_career_readiness(student)
    assert readiness_tech["components"]["technical"]["measured"] is True
    assert readiness_tech["overall_readiness"] > 0.0

    # With only technical measured, technical is re-normalized to 100% of the active score
    tech_score = readiness_tech["components"]["technical"]["score"]
    assert abs(readiness_tech["overall_readiness"] - tech_score) < 0.2


# -------------------------------------------------------------
# 3. Hybrid Recommender & Prerequisite Gating
# -------------------------------------------------------------
def test_prerequisite_gating():
    """Verify topics with unsatisfied prerequisites are flagged or lower ranked"""
    student = StudentState(skills={}) # No skills mastered
    check = check_prerequisites("deep_learning", student.skills)
    assert check["satisfied"] is False, "Deep learning should require prerequisites"
    assert len(check["missing"]) > 0

    # Once prerequisites (machine_learning, python) are added
    student.skills["machine_learning"] = {"mastery": 0.75}
    student.skills["python"] = {"mastery": 0.75}
    check_met = check_prerequisites("deep_learning", student.skills)
    assert check_met["satisfied"] is True


def test_recommender_citations_are_grounded():
    """Verify every recommended resource comes exclusively from resources.json"""
    all_res = {r["id"] for r in data_repo.get_resources()}
    student = StudentState(
        goal=Goal(career_id="software_engineer", career_title="Software Engineer"),
        profile=Profile(name="Test", experience_level="Beginner", hours_per_day=2.0)
    )
    recs = recommend_resources(student, limit=10)
    assert len(recs) > 0
    for r in recs:
        assert r["id"] in all_res, f"Hallucinated resource ID found: {r['id']}"
        assert "why_recommended" in r, "Recommendation must have an explainable why rationale"


# -------------------------------------------------------------
# 4. Daily AI Plan & Scheduler
# -------------------------------------------------------------
def test_daily_plan_generation():
    """Verify 5-day structured plan with Pomodoro allocations"""
    student = StudentState(
        profile=Profile(name="Test Candidate", hours_per_day=2.5),
        goal=Goal(career_id="data_scientist", career_title="Data Scientist")
    )
    plan = generate_daily_plan(student)
    assert plan["target_hours_per_day"] == 2.5
    assert plan["daily_minutes"] == 150
    assert len(plan["tasks"]) == 5
    assert all("task_id" in t and "task_type" in t for t in plan["tasks"])


# -------------------------------------------------------------
# 5. AI Validator & Anti-Hallucination Discarder
# -------------------------------------------------------------
def test_validator_and_anti_hallucination():
    """Verify code fences stripping, validation, and invalid resource ID stripping"""
    raw_markdown_json = """```json
    {
        "score": 8,
        "strengths": "Clear explanation",
        "improvements": "Discuss virtual dispatch",
        "weak_area": "Polymorphism",
        "better_answer": "Ideal structure incorporates runtime polymorphism.",
        "concepts_expected": ["Inheritance", "Polymorphism"],
        "concepts_covered": ["Inheritance"],
        "concepts_missed": ["Polymorphism"],
        "misconceptions": [],
        "strengths": ["Clear explanation of class hierarchies"],
        "weaknesses": ["Missed runtime polymorphism"],
        "model_answer_summary": "Ideal structure incorporates virtual dispatch.",
        "followup_suggestion": "Explain dynamic method dispatch.",
        "confidence_of_evaluation": 0.9,
        "cited_resource_ids": ["res_py_01", "invented_fake_course_123"]
    }
    ```"""

    allowed_ids = {"res_py_01", "res_py_02"}
    validated, source, err = parse_and_validate(
        raw_markdown_json,
        ANSWER_EVAL_SCHEMA,
        fallback_fn=lambda: {},
        allowed_resource_ids=allowed_ids
    )

    assert err is None
    assert source in ("ai", "llm")
    assert validated["score"] == 8
    # Crucial anti-hallucination assertion:
    assert "invented_fake_course_123" not in validated["cited_resource_ids"]
    assert "res_py_01" in validated["cited_resource_ids"]


# -------------------------------------------------------------
# 6. Canonical Data Integrity Tests
# -------------------------------------------------------------
def test_canonical_data_integrity():
    """Verify all JSON files are well-formed, have no duplicate IDs, and resolve references"""
    careers = data_repo.get_careers()
    skills = data_repo.get_skills()
    resources = data_repo.get_resources()
    projects = data_repo.get_projects()
    certs = data_repo.get_certifications()

    # 1. Careers have valid skills
    for c_id, c in careers.items():
        assert "skills" in c and len(c["skills"]) > 0
        for s in c["skills"]:
            assert s["skill_id"] in skills, f"Unknown skill {s['skill_id']} in career {c_id}"

    # 2. Resources have unique IDs and required fields
    res_ids = set()
    for r in resources:
        assert r["id"] not in res_ids, f"Duplicate resource ID: {r['id']}"
        res_ids.add(r["id"])
        assert "url" in r and r["url"].startswith("http")
        assert r["last_verified"] is None or isinstance(r["last_verified"], str)

    # 3. Certifications have mandatory kind field
    for cert in certs:
        assert cert["kind"] in ("official_certification", "learning_course", "practice_resource")


# -------------------------------------------------------------
# 7. Flask Route Tests (Status 200)
# -------------------------------------------------------------
@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_routes_status_200(client):
    """Verify all primary routes render without 500 errors"""
    routes = [
        "/",
        "/onboarding",
        "/assessment",
        "/roadmap",
        "/resources",
        "/my-resources",
        "/interview/hub",
        "/interview/coding",
        "/resume",
        "/planner",
        "/performance",
        "/projects",
        "/certifications",
        "/advisor",
        "/settings",
        "/search?q=python",
        "/api/status"
    ]
    for r in routes:
        response = client.get(r)
        assert response.status_code in (200, 302), f"Route {r} returned {response.status_code}"


def test_legacy_interview_route_compatibility(client):
    """Ensure legacy route flow still works seamlessly"""
    # 1. Start interview
    resp = client.post("/start-interview", data={
        "student_name": "Arun",
        "job_role": "Python Developer",
        "skills": "Python, SQL",
        "weak_areas": "OOP",
        "prep_time": "2 hours"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Question 1" in resp.data or b"Interview" in resp.data

    # 2. Evaluate answer
    eval_resp = client.post("/evaluate", data={
        "answer": "Encapsulation hides data while abstraction shows essential features."
    })
    assert eval_resp.status_code == 200

    # 3. Reset
    reset_resp = client.get("/reset", follow_redirects=True)
    assert reset_resp.status_code == 200


# -------------------------------------------------------------
# 8. Persona Output Divergence Test
# -------------------------------------------------------------
def test_persona_regression_divergence():
    """Verify 5 candidate personas produce distinct top resource sets and roadmaps"""
    from scripts.seed_demo_students import (
        create_persona_1, create_persona_2, create_persona_3,
        create_persona_4, create_persona_5
    )
    personas = [
        create_persona_1(), create_persona_2(), create_persona_3(),
        create_persona_4(), create_persona_5()
    ]

    recs_per_persona = []
    hours_per_persona = []

    for p in personas:
        recs = [r["id"] for r in recommend_resources(p, limit=3)]
        roadmap = generate_roadmap(p)
        recs_per_persona.append(set(recs))
        hours_per_persona.append(roadmap["total_estimated_hours"])

    # Assert no two personas have 100% identical top 3 recommendations
    for i in range(len(recs_per_persona)):
        for j in range(i + 1, len(recs_per_persona)):
            overlap = len(recs_per_persona[i].intersection(recs_per_persona[j]))
            assert overlap < 3, f"Personas {i+1} and {j+1} produced identical recommendations!"