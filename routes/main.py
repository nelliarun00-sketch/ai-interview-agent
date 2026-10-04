"""
Main Blueprint: Dashboard, Search, Advisor, Settings, Trace & Data Export
------------------------------------------------------------------------
Mission control center aggregating readiness scores, daily plan,
skill gaps, notifications, and AI career advisor chat.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, Response, flash
import json
from core.repositories.session_repo import student_repo, data_repo
from core.services.readiness import compute_career_readiness
from core.services.mastery import compute_skill_gaps
from core.services.recommender import recommend_resources
from core.services.planner import generate_daily_plan
from core.services.roadmap import compute_career_switch_diff
from ai.trace import ai_trace
from ai.client import ai_client
from ai.validator import parse_and_validate
from ai.schemas import ADVISOR_CHAT_SCHEMA

main_bp = Blueprint("main", __name__)


from routes.auth import login_required

@main_bp.route("/")
def index():
    from flask import session
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))

    student = student_repo.get("current")
    careers = data_repo.get_careers()
    readiness = compute_career_readiness(student) if student else None
    daily_plan = generate_daily_plan(student) if student else None
    gaps = compute_skill_gaps(student) if student else []
    top_resources = recommend_resources(student, limit=3) if student else []

    return render_template(
        "index.html",
        student=student,
        careers=careers,
        readiness=readiness,
        daily_plan=daily_plan,
        gaps=gaps[:5],
        top_resources=top_resources
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    readiness = compute_career_readiness(student)
    gaps = compute_skill_gaps(student)
    top_resources = recommend_resources(student, limit=3)
    daily_plan = generate_daily_plan(student)

    # Calculate exact 3 summary stats
    tech_score = int(round(readiness["components"]["technical"]["score"]))
    if tech_score == 0 and student.skills:
        tech_score = int(round(sum(s.get("mastery", 0) for s in student.skills.values()) / max(1, len(student.skills)) * 100))

    interviews_count = len(student.interviews)
    learning_score = int(round(readiness["components"]["learning_progress"]["score"]))
    if learning_score == 0 and student.resources:
        comp = sum(1 for r in student.resources.values() if r.get("status") == "completed")
        learning_score = int(round((comp / max(1, len(student.resources))) * 100))

    primary_gap_name = gaps[0]["name"] if gaps else "Data Structures & Algorithms"
    top_rec = top_resources[0] if top_resources else None

    # Clean today's 4 action tasks
    completed_task_ids = set((student.plan or {}).get("completed_task_ids", []))
    dashboard_tasks = [
        {"id": "task_oop", "title": f"Review {student.profile.self_rated_skills[0] if student.profile.self_rated_skills else 'OOP'} Fundamentals", "completed": "task_oop" in completed_task_ids},
        {"id": "task_dsa", "title": f"Solve 3 {primary_gap_name} Practice Problems", "completed": "task_dsa" in completed_task_ids or "task_1" in completed_task_ids},
        {"id": "task_sql", "title": "Practice SQL Query Optimization", "completed": "task_sql" in completed_task_ids or "task_2" in completed_task_ids},
        {"id": "task_mock", "title": f"Take 1 Adaptive {student.goal.career_title} Mock Interview", "completed": "task_mock" in completed_task_ids}
    ]

    return render_template(
        "dashboard.html",
        student=student,
        readiness=readiness,
        tech_score=tech_score,
        interviews_count=interviews_count,
        learning_score=learning_score,
        primary_gap_name=primary_gap_name,
        top_rec=top_rec,
        dashboard_tasks=dashboard_tasks,
        daily_plan=daily_plan
    )


@main_bp.route("/search")
def search():
    query = request.args.get("q", "").strip().lower()
    student = student_repo.get("current")

    if not query:
        return render_template("search.html", query="", results={}, student=student)

    resources = data_repo.get_resources()
    skills = data_repo.get_skills()
    careers = data_repo.get_careers()
    projects = data_repo.get_projects()

    matched_resources = [r for r in resources if query in r["title"].lower() or query in r["category"].lower() or any(query in t.lower() for t in r.get("tags", []))]
    matched_skills = [s for s in skills.values() if query in s["name"].lower() or query in s.get("description", "").lower()]
    matched_careers = [c for c in careers.values() if query in c["name"].lower() or query in c.get("description", "").lower()]
    matched_projects = [p for p in projects if query in p["title"].lower() or query in p.get("expected_output", "").lower()]

    results = {
        "resources": matched_resources[:6],
        "skills": matched_skills[:6],
        "careers": matched_careers[:4],
        "projects": matched_projects[:4]
    }

    return render_template("search.html", query=query, results=results, student=student)


@main_bp.route("/advisor")
def advisor():
    student = student_repo.get("current")
    return render_template("advisor.html", student=student)


@main_bp.route("/advisor/chat", methods=["POST"])
def advisor_chat():
    student = student_repo.get("current")
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply_markdown": "How can I help guide your technical career today?"}), 400

    profile_summary = f"{student.profile.name if student else 'Student'}, targeting {student.goal.career_title if student else 'Software Engineer'}."
    gaps = compute_skill_gaps(student) if student else []
    gap_summary = ", ".join([f"{g['name']} (gap: {int(g['gap']*100)}%)" for g in gaps[:3]]) or "None detected yet."

    allowed_resources = data_repo.get_resources()
    allowed_ids = {r["id"] for r in allowed_resources}

    prompt = f"""You are an inspiring, pragmatic AI Career Advisor for college students.
Candidate Context: {profile_summary}
Primary Skill Gaps: {gap_summary}
Candidate Question: {user_msg}
Candidate Resource IDs you may cite: {list(allowed_ids)[:15]}

Return ONLY valid JSON matching schema with reply_markdown."""

    def fallback_advisor():
        return {
            "reply_markdown": f"Focusing on **{gaps[0]['name'] if gaps else 'Core Fundamentals'}** will yield the highest immediate interview impact. Would you like me to schedule a 1-hour study block or start a mock interview?",
            "recommended_action": "start_mock",
            "action_payload": {},
            "cited_resource_ids": []
        }

    raw_text, latency, err = ai_client.generate(prompt=prompt, json_mode=True)
    validated, source, val_err = parse_and_validate(raw_text, ADVISOR_CHAT_SCHEMA, fallback_advisor, allowed_resource_ids=allowed_ids)

    ai_trace.record(
        operation="advisor_chat",
        prompt_version="advisor_chat.v1",
        inputs={"user_message": user_msg[:50]},
        raw_output=raw_text or "",
        validated_output=validated,
        latency_ms=latency,
        source=source,
        error=err or val_err
    )

    return jsonify(validated)


@main_bp.route("/trace")
def trace_panel():
    traces = ai_trace.list_traces()
    return jsonify({"traces": traces, "count": len(traces)})


@main_bp.route("/settings", methods=["GET", "POST"])
def settings():
    student = student_repo.get("current")
    careers = data_repo.get_careers()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_profile" and student:
            student.profile.name = request.form.get("name", student.profile.name)
            student.profile.hours_per_day = float(request.form.get("hours_per_day", student.profile.hours_per_day))
            student.profile.experience_level = request.form.get("experience_level", student.profile.experience_level)

            new_career_id = request.form.get("career_id")
            if new_career_id and new_career_id != student.goal.career_id:
                diff = compute_career_switch_diff(student.goal.career_id, new_career_id, student)
                student.goal.career_id = new_career_id
                student.goal.career_title = careers.get(new_career_id, {}).get("name", new_career_id)
                flash(f"Career updated to {student.goal.career_title}! {diff['carried_over_count']} skills carry over, {diff['new_gaps_count']} new gaps identified.", "info")

            student_repo.save(student)
            flash("Settings updated successfully.", "success")
            return redirect(url_for("main.settings"))

    return render_template("settings.html", student=student, careers=careers)


@main_bp.route("/export-data")
def export_data():
    student = student_repo.get("current")
    if not student:
        return jsonify({"error": "No student state found"}), 404
    data_str = json.dumps(student.to_dict(), indent=2)
    return Response(
        data_str,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=my_career_os_data.json"}
    )
