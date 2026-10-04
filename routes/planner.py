"""
Daily Plan & Scheduler Blueprint
--------------------------------
Displays prioritized study blocks, Pomodoro sessions, and checkable tasks.
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from core.repositories.session_repo import student_repo
from core.services.planner import generate_daily_plan
from routes.auth import login_required

planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/planner")
@login_required
def view_plan():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    plan = generate_daily_plan(student)
    return render_template("planner.html", student=student, plan=plan)


@planner_bp.route("/planner/toggle-task/<task_id>", methods=["POST"])
def toggle_task(task_id):
    student = student_repo.get("current")
    if not student:
        return jsonify({"error": "Unauthorized"}), 401

    # Record completed tasks in student state
    completed = request.form.get("completed") == "true"
    if not student.plan:
        student.plan = {"completed_task_ids": []}
    comp_list = student.plan.get("completed_task_ids", [])

    if completed and task_id not in comp_list:
        comp_list.append(task_id)
    elif not completed and task_id in comp_list:
        comp_list.remove(task_id)

    student.plan["completed_task_ids"] = comp_list
    student_repo.save(student)

    return jsonify({"success": True, "completed_tasks": comp_list})
