"""
Student Profile & Settings Blueprint for AI Career Mentor
---------------------------------------------------------
Delivers individual student profile management, education/career updates,
security/password changes, and account statistics.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from core.repositories.session_repo import student_repo, data_repo
from core.database import get_user_by_id, update_user_password, authenticate_user
from core.services.roadmap import compute_career_switch_diff
from routes.auth import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def view_profile():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    user_id = session.get("user_id")
    user = get_user_by_id(user_id) if user_id else None
    careers = data_repo.get_careers()

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "update_profile":
            student.profile.name = request.form.get("name", student.profile.name).strip()
            student.profile.education = request.form.get("education", student.profile.education).strip()
            student.profile.specialization = request.form.get("specialization", student.profile.specialization).strip()
            student.profile.graduation_status = request.form.get("graduation_status", student.profile.graduation_status).strip()
            student.profile.hours_per_day = float(request.form.get("hours_per_day", student.profile.hours_per_day))
            student.profile.experience_level = request.form.get("experience_level", student.profile.experience_level).strip()

            new_career_id = request.form.get("career_id")
            if new_career_id and new_career_id != student.goal.career_id:
                diff = compute_career_switch_diff(student.goal.career_id, new_career_id, student)
                student.goal.career_id = new_career_id
                student.goal.career_title = careers.get(new_career_id, {}).get("name", new_career_id)
                student.goal.career_group = careers.get(new_career_id, {}).get("group", "Software Engineering")
                flash(f"Career updated to {student.goal.career_title}! {diff['carried_over_count']} skills carry over.", "info")

            # Update weak areas
            weak_text = request.form.get("weak_areas", "").strip()
            if weak_text:
                student.profile.self_rated_skills = [w.strip() for w in weak_text.split(",") if w.strip()]

            student_repo.save(student)
            flash("Student profile updated successfully!", "success")
            return redirect(url_for("profile.view_profile"))

        elif action == "change_password":
            current_pass = request.form.get("current_password", "")
            new_pass = request.form.get("new_password", "")
            confirm_pass = request.form.get("confirm_password", "")

            if user and not authenticate_user(user["email"], current_pass):
                flash("Current password is incorrect.", "danger")
            elif new_pass != confirm_pass:
                flash("New passwords do not match.", "warning")
            elif len(new_pass) < 6:
                flash("Password must be at least 6 characters long.", "warning")
            else:
                if user_id:
                    update_user_password(user_id, new_pass)
                flash("Password updated successfully!", "success")
            return redirect(url_for("profile.view_profile"))

    # Compute quick stats
    interviews_count = len(student.interviews)
    resources_count = len([r for r in student.resources.values() if r.get("status") == "completed"])
    bookmarks_count = len([r for r in student.resources.values() if r.get("bookmarked")])

    return render_template(
        "profile.html",
        student=student,
        user=user,
        careers=careers,
        interviews_count=interviews_count,
        resources_count=resources_count,
        bookmarks_count=bookmarks_count
    )
