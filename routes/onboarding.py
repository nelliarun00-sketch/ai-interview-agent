"""
Onboarding Blueprint
--------------------
Handles candidate profile setup and initial goal calibration.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories.session_repo import student_repo, data_repo
from core.services.onboarding import create_initial_student, map_custom_career

onboarding_bp = Blueprint("onboarding", __name__)


@onboarding_bp.route("/onboarding", methods=["GET", "POST"])
def onboard():
    careers = data_repo.get_careers()

    if request.method == "POST":
        student = create_initial_student(request.form)

        # Handle custom career mapping if selected
        if student.goal.is_custom and student.goal.custom_role_description:
            mapping = map_custom_career(student.goal.custom_role_description)
            student.goal.career_title = mapping.get("career_title", student.goal.custom_role_description)
            student.goal.career_group = mapping.get("group", "Custom Career")

        student_repo.save(student)
        flash(f"Welcome, {student.profile.name}! Your AI Career Plan is configured for {student.goal.career_title}.", "success")
        return redirect(url_for("main.dashboard"))

    student = student_repo.get("current")
    return render_template("onboarding.html", careers=careers, student=student)
