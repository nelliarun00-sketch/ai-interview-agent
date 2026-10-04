"""
Resource Library & Bookmarks Blueprint
--------------------------------------
Delivers multi-factor filtered resource library, progress tracking, and bookmarks.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from core.repositories.session_repo import student_repo, data_repo
from core.services.recommender import recommend_resources
from routes.auth import login_required

resources_bp = Blueprint("resources", __name__)


@resources_bp.route("/resources")
@login_required
def library():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()
    cost = request.args.get("cost", "").strip()
    search = request.args.get("search", "").strip().lower()

    all_resources = recommend_resources(student, limit=50)

    # Filter
    filtered = []
    for r in all_resources:
        if category and r.get("category") != category:
            continue
        if level and r.get("level") != level:
            continue
        if cost and r.get("cost") != cost:
            continue
        if search and (search not in r.get("title", "").lower() and search not in r.get("description", "").lower()):
            continue
        filtered.append(r)

    # Extract distinct categories
    categories = sorted(list({r.get("category") for r in data_repo.get_resources() if r.get("category")}))

    return render_template(
        "resources.html",
        student=student,
        resources=filtered,
        categories=categories,
        selected_category=category,
        selected_level=level,
        selected_cost=cost,
        search_query=search
    )


@resources_bp.route("/resources/bookmark/<resource_id>", methods=["POST"])
def toggle_bookmark(resource_id):
    student = student_repo.get("current")
    if not student:
        return jsonify({"error": "Unauthorized"}), 401

    entry = student.resources.get(resource_id, {"status": "not_started", "bookmarked": False})
    entry["bookmarked"] = not entry.get("bookmarked", False)
    student.resources[resource_id] = entry
    student_repo.save(student)

    return jsonify({"success": True, "bookmarked": entry["bookmarked"]})


@resources_bp.route("/resources/progress/<resource_id>", methods=["POST"])
def update_progress(resource_id):
    student = student_repo.get("current")
    if not student:
        return jsonify({"error": "Unauthorized"}), 401

    status = request.form.get("status", "completed")
    entry = student.resources.get(resource_id, {"bookmarked": False})
    entry["status"] = status
    entry["percent"] = 100 if status == "completed" else 50
    student.resources[resource_id] = entry
    student_repo.save(student)

    flash("Resource progress updated!", "success")
    return redirect(request.referrer or url_for("resources.library"))


@resources_bp.route("/my-resources")
@login_required
def my_resources():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    all_resources = {r["id"]: r for r in data_repo.get_resources()}
    bookmarked = []
    in_progress = []
    completed = []

    for r_id, p in student.resources.items():
        if r_id in all_resources:
            item = dict(all_resources[r_id])
            item["status"] = p.get("status")
            item["percent"] = p.get("percent", 0)
            if p.get("bookmarked"):
                bookmarked.append(item)
            if p.get("status") == "in_progress":
                in_progress.append(item)
            elif p.get("status") == "completed":
                completed.append(item)

    return render_template(
        "my_resources.html",
        student=student,
        bookmarked=bookmarked,
        in_progress=in_progress,
        completed=completed
    )
