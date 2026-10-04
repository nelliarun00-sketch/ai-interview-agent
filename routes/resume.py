"""
Resume Intelligence Blueprint
-----------------------------
Handles resume upload (PDF/DOCX/TXT), server-side parsing with pypdf/docx,
ATS checklist scoring, and project probing interview questions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core.repositories.session_repo import student_repo
from core.services.resume import extract_text_from_file, analyze_resume
from core.services.gamification import check_and_unlock_achievements
from core.services.notifications import add_notification

from routes.auth import login_required

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/resume")
@login_required
def resume_home():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))
    return render_template("resume.html", student=student, analysis=student.resume_analysis)


@resume_bp.route("/resume/upload", methods=["POST"])
@login_required
def upload_resume():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    file = request.files.get("resume_file")
    if not file or not file.filename:
        flash("Please select a valid PDF, DOCX, or TXT file to upload.", "warning")
        return redirect(url_for("resume.resume_home"))

    try:
        text = extract_text_from_file(file)
        if len(text) < 50:
            flash("Could not extract readable text from the uploaded file.", "warning")
            return redirect(url_for("resume.resume_home"))

        analysis = analyze_resume(text, student)
        check_and_unlock_achievements(student)
        add_notification(
            student,
            "Resume Screened",
            f"ATS Compatibility Score: {analysis['ats_score']}/100.",
            type_="success"
        )
        student_repo.save(student)

        flash("Resume analyzed successfully!", "success")
    except Exception as e:
        flash(f"Error parsing resume: {str(e)}", "warning")

    return redirect(url_for("resume.resume_home"))
