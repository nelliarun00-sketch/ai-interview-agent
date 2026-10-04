"""
Performance & Analytics Blueprint
---------------------------------
Visualizes mastery trajectories, multi-component readiness radar,
and interview historical comparison view.
"""

from flask import Blueprint, render_template, redirect, url_for, request
from core.repositories.session_repo import student_repo
from core.services.readiness import compute_career_readiness
from core.services.mastery import compute_skill_gaps
from routes.auth import login_required

performance_bp = Blueprint("performance", __name__)


@performance_bp.route("/performance")
@login_required
def analytics():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    readiness = compute_career_readiness(student)
    gaps = compute_skill_gaps(student)

    # Historical interview comparison
    inv1_id = request.args.get("inv1")
    inv2_id = request.args.get("inv2")

    comparison = None
    if inv1_id and inv2_id:
        inv1 = next((i for i in student.interviews if i["id"] == inv1_id), None)
        inv2 = next((i for i in student.interviews if i["id"] == inv2_id), None)
        if inv1 and inv2:
            comparison = {
                "inv1": inv1,
                "inv2": inv2,
                "delta": round(inv2["overall_score"] - inv1["overall_score"], 1)
            }

    return render_template(
        "performance.html",
        student=student,
        readiness=readiness,
        gaps=gaps,
        interviews=student.interviews,
        comparison=comparison
    )
