"""
Projects & Certifications Blueprint
-----------------------------------
Recommends practical portfolio projects and provides honest distinction between
official certifications, learning courses, and practice platforms.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from core.repositories.session_repo import student_repo
from core.services.recommender import recommend_projects, recommend_certifications
from routes.auth import login_required

projects_certs_bp = Blueprint("projects_certs", __name__)


@projects_certs_bp.route("/projects")
@login_required
def view_projects():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    projects = recommend_projects(student)
    return render_template("projects.html", student=student, projects=projects)


@projects_certs_bp.route("/projects/update-status/<project_id>", methods=["POST"])
def update_project_status(project_id):
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    new_status = request.form.get("status", "In Progress")
    student.project_status[project_id] = new_status
    student_repo.save(student)

    flash(f"Project status updated to {new_status}!", "success")
    return redirect(url_for("projects_certs.view_projects"))


@projects_certs_bp.route("/certifications")
def view_certifications():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    certs = recommend_certifications(student)
    return render_template("certifications.html", student=student, certifications=certs)
