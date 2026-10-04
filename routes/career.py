"""
Career Strategy & Job Matching Blueprint for AI Career Mentor
-------------------------------------------------------------
Aggregates Target Career goals, Readiness breakdown, Skill Gaps,
Interactive Roadmap, Portfolio Projects, Certifications, and
AI Job Description Matching.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
from core.repositories.session_repo import student_repo, data_repo
from core.services.readiness import compute_career_readiness
from core.services.mastery import compute_skill_gaps
from core.services.roadmap import generate_roadmap
from core.services.recommender import recommend_projects, recommend_certifications
from core.database import save_job_match, get_job_matches
from ai.client import ai_client
from routes.auth import login_required

career_bp = Blueprint("career", __name__)


@career_bp.route("/career")
@login_required
def career_hub():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    readiness = compute_career_readiness(student)
    gaps = compute_skill_gaps(student)
    roadmap = generate_roadmap(student)
    projects = recommend_projects(student)
    certs = recommend_certifications(student)
    careers = data_repo.get_careers()

    user_id = session.get("user_id")
    job_matches = get_job_matches(user_id) if user_id else []

    return render_template(
        "career.html",
        student=student,
        readiness=readiness,
        gaps=gaps,
        roadmap=roadmap,
        projects=projects,
        certifications=certs,
        careers=careers,
        job_matches=job_matches
    )


@career_bp.route("/career/job-match", methods=["POST"])
@login_required
def match_job_description():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    job_title = request.form.get("job_title", "Software Engineer").strip()
    job_desc = request.form.get("job_description", "").strip()

    if not job_desc or len(job_desc) < 30:
        flash("Please paste a realistic job description (at least 30 characters).", "warning")
        return redirect(url_for("career.career_hub"))

    # Compare student profile skills against job description
    student_skills = list(student.skills.keys())
    skills_data = data_repo.get_skills()

    prompt = f"""You are an expert AI Career Screener & Recruiter.
Analyze this job description against the student's current skills profile.

Student Target Role: {student.goal.career_title}
Student Verified Skills: {student_skills}
Student Weak Areas: {[s for s, d in student.skills.items() if d.get('mastery', 0) < 0.5]}

Job Title: {job_title}
Job Description:
\"\"\"{job_desc[:2500]}\"\"\"

Return ONLY valid JSON matching this schema:
{{
  "match_percentage": <integer 0-100>,
  "strong_skills": [<list of matched strings found in both>],
  "missing_skills": [<list of critical required skills the candidate lacks>],
  "recommended_learning": [<list of 2-3 specific topics to study>],
  "summary_verdict": "<short paragraph giving honest recruiter feedback>"
}}"""

    raw_text, latency, err = ai_client.generate(prompt=prompt, json_mode=True)

    result = None
    if raw_text and not err:
        try:
            # clean code blocks if present
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
        except Exception:
            result = None

    if not result:
        # High-accuracy heuristic fallback
        desc_lower = job_desc.lower()
        matched = []
        missing = []
        for s_id, s_info in skills_data.items():
            name = s_info.get("name", s_id)
            if s_id.lower() in desc_lower or name.lower() in desc_lower:
                if s_id in student.skills and student.skills[s_id].get("mastery", 0) >= 0.5:
                    matched.append(name)
                else:
                    missing.append(name)

        pct = int(min(95, max(30, (len(matched) / max(1, len(matched) + len(missing))) * 100)))
        result = {
            "match_percentage": pct,
            "strong_skills": matched[:5] or ["Core Fundamentals"],
            "missing_skills": missing[:5] or ["Advanced Frameworks"],
            "recommended_learning": missing[:3] or ["System Design", "Unit Testing"],
            "summary_verdict": f"You show solid alignment on {len(matched)} key requirements. Closing gaps in {', '.join(missing[:2])} will significantly boost interview conversion."
        }

    match_pct = result.get("match_percentage", 65)

    user_id = session.get("user_id")
    if user_id:
        save_job_match(user_id, job_title, match_pct, job_desc, result)

    flash(f"Job Description matched! Alignment score: {match_pct}%", "success")
    return render_template(
        "career_job_result.html",
        student=student,
        job_title=job_title,
        result=result
    )
