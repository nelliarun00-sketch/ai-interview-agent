"""
Learning Roadmap Blueprint
--------------------------
Visualizes dynamic phase timeline and re-plans based on candidate skill gaps.
"""

from flask import Blueprint, render_template, redirect, url_for
from core.repositories.session_repo import student_repo
from core.services.roadmap import generate_roadmap
from core.services.mastery import compute_skill_gaps
from routes.auth import login_required

roadmap_bp = Blueprint("roadmap", __name__)


@roadmap_bp.route("/roadmap")
@login_required
def view_roadmap():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    roadmap = generate_roadmap(student)
    gaps = compute_skill_gaps(student)

    return render_template("roadmap.html", student=student, roadmap=roadmap, gaps=gaps)
