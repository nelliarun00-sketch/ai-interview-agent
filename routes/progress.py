"""
Progress & Analytics Blueprint for AI Career Mentor
---------------------------------------------------
Answers: "How am I improving?"
Visualizes Career Readiness, Skill Mastery bars with status colors,
Interview score trend chart, and dynamic AI Progress Insights.
"""

from flask import Blueprint, render_template, redirect, url_for, session
from core.repositories.session_repo import student_repo, data_repo
from core.services.readiness import compute_career_readiness
from core.services.mastery import compute_skill_gaps
from routes.auth import login_required

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/progress")
@login_required
def progress_page():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    readiness = compute_career_readiness(student)
    gaps = compute_skill_gaps(student)

    # 1. Skill breakdown with status classes
    skills_list = []
    for s_id, s_data in student.skills.items():
        pct = int(round(s_data.get("mastery", 0.0) * 100))
        if pct >= 70:
            status = "Strong"
            status_color = "success"  # Green
        elif pct >= 50:
            status = "Medium"
            status_color = "warning"  # Amber
        else:
            status = "Needs Improvement" if pct >= 30 else "Weak"
            status_color = "error"    # Rose/Red

        skills_list.append({
            "id": s_id,
            "name": s_data.get("name", s_id.upper()),
            "percent": pct,
            "status": status,
            "status_color": status_color,
            "attempts": s_data.get("attempts", 0),
            "trend": s_data.get("trend", "stable")
        })
    skills_list.sort(key=lambda x: x["percent"], reverse=True)

    # 2. Interview Progress Stats & Score History
    interviews = student.interviews
    completed_interviews = len(interviews)
    scores = [float(inv.get("overall_score", 0.0)) for inv in interviews]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    best_score = round(max(scores), 1) if scores else 0.0

    questions_answered = 0
    for inv in interviews:
        questions_answered += len(inv.get("turns", []))
    if questions_answered == 0 and completed_interviews > 0:
        questions_answered = completed_interviews * 5

    # Reverse scores chronologically for chart display (oldest to newest, max 10 points)
    chart_scores = list(reversed(scores[:10])) if scores else []

    # 3. Learning Progress
    all_resources = {r["id"]: r for r in data_repo.get_resources()}
    completed_resources_count = sum(1 for p in student.resources.values() if p.get("status") == "completed")
    in_progress_resources_count = sum(1 for p in student.resources.values() if p.get("status") == "in_progress")
    total_tracked_resources = len(student.resources)
    learning_pct = int(round((completed_resources_count / max(1, total_tracked_resources)) * 100)) if total_tracked_resources else 0

    # 4. Generate AI Progress Insight from real student data
    strongest = skills_list[0]["name"] if skills_list else "Fundamentals"
    weakest = skills_list[-1]["name"] if skills_list and skills_list[-1]["percent"] < 60 else (gaps[0]["name"] if gaps else "System Design")
    
    first_score = chart_scores[0] if chart_scores else 6.0
    last_score = chart_scores[-1] if chart_scores else avg_score
    delta = round(last_score - first_score, 1)

    if delta > 0:
        score_insight = f"Your interview score improved from {first_score} to {last_score} (+{delta} pts)."
    else:
        score_insight = f"Your interview performance is averaging {avg_score} / 10."

    ai_insight = {
        "score_summary": score_insight,
        "strongest_skill": strongest,
        "weakest_skill": weakest,
        "recommended_step": f"Complete practice problems in {weakest} and take an adaptive technical interview to solidify retention."
    }

    return render_template(
        "progress.html",
        student=student,
        readiness=readiness,
        skills_list=skills_list,
        completed_interviews=completed_interviews,
        avg_score=avg_score,
        best_score=best_score,
        questions_answered=questions_answered,
        chart_scores=chart_scores,
        completed_resources_count=completed_resources_count,
        in_progress_resources_count=in_progress_resources_count,
        learning_pct=learning_pct,
        ai_insight=ai_insight
    )
