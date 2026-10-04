"""
Automated Test Suite for Authentication, Multi-Student Isolation, and Saved Persistence
----------------------------------------------------------------------------------------
Tests:
1. User registration with password hashing (passwords never stored plaintext)
2. Authentication (login / logout / invalid credentials)
3. Multi-student profile & state isolation (Arun vs Rahul vs Ananya)
4. Data persistence across logout and login
5. Protected route enforcement
6. Profile customization and database synchronization
7. Job Description Matcher execution
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app import create_app
from core.database import (
    init_db, create_user, authenticate_user, get_user_by_email,
    get_student_state_by_user_id, save_student_state_by_user_id
)
from core.models import StudentState, Profile, Goal


@pytest.fixture
def app_instance():
    app = create_app()
    app.config["TESTING"] = False  # Enforce real route redirects for security testing
    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_password_hashing():
    """Verify passwords are never stored in plain text."""
    init_db()
    user = get_user_by_email("arun@example.com")
    assert user is not None
    # Verify user dict has no plaintext password
    assert "password" not in user
    # Verify password authentication works via secure hash check
    auth_success = authenticate_user("arun@example.com", "password123")
    assert auth_success is not None
    assert auth_success["email"] == "arun@example.com"
    # Verify wrong password fails
    auth_fail = authenticate_user("arun@example.com", "wrong_password")
    assert auth_fail is None


def test_protected_routes_redirect_unauthenticated(client):
    """Verify unauthenticated requests to protected endpoints redirect to /login."""
    protected_urls = ["/dashboard", "/progress", "/profile", "/career", "/resume"]
    for url in protected_urls:
        res = client.get(url, follow_redirects=False)
        assert res.status_code == 302, f"Expected redirect on {url}"
        assert "/login" in res.headers["Location"]


def test_multi_student_isolation(client):
    """
    Verify Student A (Arun) and Student B (Rahul) see their own distinct data
    and never see each other's profiles, skills, or interviews.
    """
    # 1. Log in as Arun
    login_arun = client.post("/login", data={"email": "arun@example.com", "password": "password123"}, follow_redirects=True)
    assert login_arun.status_code == 200

    dash_arun = client.get("/dashboard")
    assert b"Arun" in dash_arun.data
    assert b"Rahul" not in dash_arun.data

    prog_arun = client.get("/progress")
    assert b"12 Sessions" in prog_arun.data  # Arun's interviews count
    assert b"Python" in prog_arun.data

    client.get("/logout")

    # 2. Log in as Rahul
    login_rahul = client.post("/login", data={"email": "rahul@example.com", "password": "password123"}, follow_redirects=True)
    assert login_rahul.status_code == 200

    dash_rahul = client.get("/dashboard")
    assert b"Rahul" in dash_rahul.data
    assert b"Arun" not in dash_rahul.data

    prog_rahul = client.get("/progress")
    assert b"4 Sessions" in prog_rahul.data  # Rahul's interviews count
    assert b"12 Sessions" not in prog_rahul.data

    client.get("/logout")

    # 3. Log in as Ananya
    login_ananya = client.post("/login", data={"email": "ananya@example.com", "password": "password123"}, follow_redirects=True)
    assert login_ananya.status_code == 200

    dash_ananya = client.get("/dashboard")
    assert b"Ananya" in dash_ananya.data

    prog_ananya = client.get("/progress")
    assert b"8 Sessions" in prog_ananya.data

    client.get("/logout")


def test_saved_progress_persistence(client):
    """Verify that student progress is saved to SQLite and persists across logout and login."""
    # 1. Log in as Arun
    client.post("/login", data={"email": "arun@example.com", "password": "password123"}, follow_redirects=True)

    # 2. Update resource progress
    res_update = client.post("/resources/progress/res_py_01", data={"status": "completed"}, follow_redirects=True)
    assert res_update.status_code == 200

    # 3. Update profile study hours
    prof_update = client.post("/profile", data={
        "action": "update_profile",
        "name": "Arun Kumar Updated",
        "education": "B.Tech Honours",
        "specialization": "Computer Science & Engineering",
        "graduation_status": "Final Year",
        "career_id": "software_engineer",
        "hours_per_day": "3.5",
        "experience_level": "Intermediate",
        "weak_areas": "DSA, Concurrency"
    }, follow_redirects=True)
    assert prof_update.status_code == 200

    # 4. Log out
    client.get("/logout")

    # 5. Log back in as Arun
    client.post("/login", data={"email": "arun@example.com", "password": "password123"}, follow_redirects=True)

    # 6. Verify updated profile is persisted
    prof_view = client.get("/profile")
    assert b"Arun Kumar Updated" in prof_view.data
    assert b"B.Tech Honours" in prof_view.data

    # Revert back name
    client.post("/profile", data={
        "action": "update_profile",
        "name": "Arun Kumar",
        "education": "B.Tech",
        "specialization": "Computer Science & Engineering",
        "graduation_status": "Final Year",
        "career_id": "software_engineer",
        "hours_per_day": "2.0",
        "experience_level": "Intermediate",
        "weak_areas": "DSA, System Design"
    })
    client.get("/logout")


def test_new_student_signup_and_onboarding(client):
    """Verify new student can register, onboard, and get an independent profile."""
    import uuid
    test_email = f"dev_{uuid.uuid4().hex[:6]}@example.com"
    # 1. Signup
    signup_resp = client.post("/signup", data={
        "full_name": "Dev Sharma",
        "email": test_email,
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert signup_resp.status_code == 200
    assert b"FIRST-TIME PROFILE SETUP" in signup_resp.data or b"Calibrate" in signup_resp.data

    # 2. Complete onboarding wizard
    onboard_resp = client.post("/onboarding", data={
        "name": "Dev Sharma",
        "education": "MCA",
        "specialization": "Software Engineering",
        "graduation_status": "Pre-final Year",
        "prep_type": "Campus Placements",
        "career_id": "fullstack_developer",
        "skills_raw": "JavaScript, Python, SQL",
        "weak_areas": "React, REST APIs",
        "hours_per_day": "2.0",
        "experience_level": "Beginner"
    }, follow_redirects=True)
    assert onboard_resp.status_code == 200
    assert b"Dev" in onboard_resp.data

    # 3. Check dashboard
    dash = client.get("/dashboard")
    assert b"Dev" in dash.data
    assert b"Full-Stack Developer" in dash.data

    client.get("/logout")


def test_job_description_matcher(client):
    """Verify Job Description Matcher route analyzes requirements against student skills."""
    client.post("/login", data={"email": "arun@example.com", "password": "password123"}, follow_redirects=True)

    jd_text = """
    We are looking for a Software Engineer proficient in Python, SQL, and Object-Oriented Programming.
    Candidates should understand Data Structures and Algorithms, REST APIs, and System Design.
    """
    match_resp = client.post("/career/job-match", data={
        "job_title": "Python Backend Engineer",
        "job_description": jd_text
    }, follow_redirects=True)

    assert match_resp.status_code == 200
    assert b"Job Match Analysis" in match_resp.data
    assert b"Python" in match_resp.data
    client.get("/logout")
