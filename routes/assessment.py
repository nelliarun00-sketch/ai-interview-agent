"""
Diagnostic Assessment Blueprint
--------------------------------
Delivers career-specific diagnostics, scores MCQs deterministically,
and updates knowledge-tracing mastery.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories.session_repo import student_repo
from core.services.assessment import get_diagnostic_questions_for_goal, evaluate_diagnostic_submission
from core.services.gamification import check_and_unlock_achievements
from core.services.notifications import add_notification
from routes.auth import login_required

assessment_bp = Blueprint("assessment", __name__)


@assessment_bp.route("/assessment")
@login_required
def diagnostic():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    questions = get_diagnostic_questions_for_goal(student.goal.career_id)
    return render_template("diagnostic.html", student=student, questions=questions)


@assessment_bp.route("/assessment/submit", methods=["POST"])
@login_required
def submit_diagnostic():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    results = evaluate_diagnostic_submission(student, request.form)

    # Award achievement & notification
    check_and_unlock_achievements(student)
    add_notification(
        student,
        "Diagnostic Completed",
        f"Calibrated proficiency at {results['estimated_level']} level with {results['score_percentage']}% accuracy.",
        type_="success"
    )

    student_repo.save(student)
    flash(f"Assessment complete! Calibrated at {results['estimated_level']} level.", "success")
    return render_template("diagnostic_results.html", student=student, results=results)
