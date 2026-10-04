"""
Adaptive Mock Interview Suite Blueprint
---------------------------------------
Delivers Technical, Coding Review, HR, and Behavioral interview modes.
Preserves complete legacy route backwards compatibility.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from core.repositories.session_repo import student_repo, data_repo
from core.models import StudentState, InterviewSession, InterviewTurn
from core.services.interview import start_interview_session, select_next_interview_topic, generate_interview_question
from core.services.evaluator import evaluate_technical_answer, evaluate_coding_answer
from core.services.gamification import check_and_unlock_achievements
from core.services.notifications import add_notification
from core.services.planner import generate_daily_plan
from config import config
from routes.auth import login_required

interview_bp = Blueprint("interview", __name__)


# -------------------------------------------------------------
# 1. Multi-Mode Interview Hub
# -------------------------------------------------------------
@interview_bp.route("/interview/hub")
@login_required
def hub():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))
    return render_template("interview/hub.html", student=student)


@interview_bp.route("/interview/start-mode", methods=["POST"])
@login_required
def start_mode():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    mode = request.form.get("mode", "technical")
    difficulty = request.form.get("difficulty", "medium")

    if mode == "coding":
        return redirect(url_for("interview.coding_room"))

    # Initialize session
    inv_session = start_interview_session(student, mode=mode, difficulty=difficulty)
    topic = select_next_interview_topic(student, inv_session.turns)
    q_data = generate_interview_question(student, inv_session, topic)

    q_text = (
        q_data.get("question")
        or q_data.get("question_text")
        or f"Explain the core technical principles and real-world trade-offs of {topic}."
    )

    session["active_interview"] = {
        "id": inv_session.id,
        "mode": mode,
        "role": student.goal.career_title,
        "difficulty": difficulty,
        "turns": [],
        "current_question": q_text,
        "current_topic": topic,
        "current_q_num": 1,
        "total_q": 5
    }

    return redirect(url_for("interview.active_room"))


@interview_bp.route("/interview/room")
@login_required
def active_room():
    student = student_repo.get("current")
    inv = session.get("active_interview")
    if not student or not inv:
        return redirect(url_for("interview.interview_page"))

    progress_pct = int((inv["current_q_num"] / inv["total_q"]) * 100)

    return render_template(
        "interview/room.html",
        student=student,
        inv=inv,
        progress_pct=progress_pct
    )


@interview_bp.route("/interview/submit-turn", methods=["POST"])
@login_required
def submit_turn():
    student = student_repo.get("current")
    inv = session.get("active_interview")
    if not student or not inv:
        return redirect(url_for("interview.interview_page"))

    answer = request.form.get("answer", "").strip()
    if not answer:
        flash("Please provide an answer before submitting.", "warning")
        return redirect(url_for("interview.active_room"))

    q_text = inv["current_question"]
    topic = inv["current_topic"]
    difficulty = inv["difficulty"]

    # Evaluate
    evaluation = evaluate_technical_answer(
        question=q_text,
        answer=answer,
        job_role=inv["role"],
        difficulty=difficulty,
        topic=topic,
        student=student
    )

    score = evaluation.get("score", 5)

    # Record turn
    turn_record = {
        "question_number": inv["current_q_num"],
        "question": q_text,
        "topic": topic,
        "answer": answer,
        "score": score,
        "difficulty": difficulty,
        "evaluation": evaluation
    }
    inv["turns"].append(turn_record)

    # Difficulty calibration
    if score <= 4:
        next_diff = "easy" if difficulty == "medium" else ("medium" if difficulty == "hard" else "easy")
    elif score >= 8:
        next_diff = "medium" if difficulty == "easy" else "hard"
    else:
        next_diff = difficulty
    inv["difficulty"] = next_diff

    is_last = (inv["current_q_num"] >= inv["total_q"])

    # If completed, persist to student history
    if is_last:
        avg_score = sum(t["score"] for t in inv["turns"]) / len(inv["turns"])
        student.interviews.insert(0, {
            "id": inv["id"],
            "mode": inv["mode"],
            "role": inv["role"],
            "overall_score": round(avg_score, 1),
            "turns": inv["turns"]
        })
        check_and_unlock_achievements(student)
        add_notification(student, "Mock Interview Completed", f"Scored {round(avg_score, 1)}/10 in {inv['mode'].title()} Interview.", "success")
        student_repo.save(student)

    session["active_interview"] = inv

    return render_template(
        "interview/turn_eval.html",
        student=student,
        inv=inv,
        evaluation=evaluation,
        score=score,
        is_last=is_last
    )


@interview_bp.route("/interview/next-turn")
@login_required
def next_turn():
    student = student_repo.get("current")
    inv = session.get("active_interview")
    if not student or not inv:
        return redirect(url_for("interview.interview_page"))

    if inv["current_q_num"] >= inv["total_q"]:
        return redirect(url_for("interview.summary_report"))

    inv["current_q_num"] += 1
    dummy_session = InterviewSession(
        mode=inv["mode"],
        role=inv["role"],
        difficulty=inv["difficulty"],
        turns=inv["turns"]
    )
    topic = select_next_interview_topic(student, inv["turns"])
    q_data = generate_interview_question(student, dummy_session, topic)

    q_text = (
        q_data.get("question")
        or q_data.get("question_text")
        or f"Explain the core technical principles and real-world trade-offs of {topic}."
    )

    inv["current_question"] = q_text
    inv["current_topic"] = topic
    session["active_interview"] = inv

    return redirect(url_for("interview.active_room"))


@interview_bp.route("/interview/summary")
@login_required
def summary_report():
    student = student_repo.get("current")
    inv = session.get("active_interview")
    if not student or not inv or not inv.get("turns"):
        return redirect(url_for("interview.interview_page"))

    scores = [t["score"] for t in inv["turns"]]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    return render_template(
        "interview/summary.html",
        student=student,
        inv=inv,
        avg_score=avg_score,
        scores=scores
    )


# -------------------------------------------------------------
# 2. Honest AI Code Review Room
# -------------------------------------------------------------
@interview_bp.route("/interview/coding")
@login_required
def coding_room():
    student = student_repo.get("current")
    if not student:
        return redirect(url_for("onboarding.onboard"))

    seed_questions = data_repo.get_question_bank().get("interview_seed", {}).get("coding", [])
    problem = seed_questions[0] if seed_questions else {
        "title": "Two Sum",
        "difficulty": "easy",
        "problem": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}],
        "constraints": "2 <= nums.length <= 10^4",
        "hints": ["Use a hash map."]
    }

    return render_template("interview/coding.html", student=student, problem=problem)


@interview_bp.route("/interview/coding/review", methods=["POST"])
@login_required
def coding_review():
    student = student_repo.get("current")
    problem_text = request.form.get("problem", "")
    language = request.form.get("language", "python")
    code = request.form.get("code", "").strip()

    review = evaluate_coding_answer(problem=problem_text, language=language, code=code)
    return jsonify(review)


# -------------------------------------------------------------
# 3. Complete Legacy Route Compatibility (Preserves Working Tests & Flow)
# -------------------------------------------------------------
@interview_bp.route("/interview")
def interview_page():
    # If legacy session active, show legacy interview template
    student_name = session.get("student_name")
    if student_name and "current_question" in session:
        q_num = session.get("question_number", 1)
        total_q = session.get("total_questions", 5)
        progress_pct = int((q_num / total_q) * 100)
        return render_template(
            "interview.html",
            student_name=student_name,
            job_role=session.get("job_role", "Software Engineer"),
            skills=session.get("skills", "Python"),
            difficulty=session.get("difficulty", "medium"),
            question_number=q_num,
            total_questions=total_q,
            progress_percent=progress_pct,
            current_question=session.get("current_question"),
            identified_weak_area=session.get("identified_weak_area")
        )

    # Otherwise redirect to modern Hub
    return redirect(url_for("interview.hub"))


@interview_bp.route("/start-interview", methods=["POST"])
def legacy_start_interview():
    student_name = request.form.get("student_name", "Arun").strip()
    job_role = request.form.get("job_role", "Python Developer").strip()
    skills = request.form.get("skills", "Python, C++, SQL").strip()
    weak_areas = request.form.get("weak_areas", "OOP, DSA").strip()
    prep_time = request.form.get("prep_time", "2 hours per day").strip()

    session.clear()
    session["student_name"] = student_name
    session["job_role"] = job_role
    session["skills"] = skills
    session["weak_areas"] = weak_areas
    session["prep_time"] = prep_time
    session["question_number"] = 1
    session["total_questions"] = 5
    session["difficulty"] = "medium"
    session["score_history"] = []
    session["history"] = []
    session["identified_weak_area"] = weak_areas
    session["current_question"] = "What are the four main principles of Object-Oriented Programming, and how does encapsulation differ from abstraction?"

    # Ensure StudentState in repository is also initialized
    student = student_repo.get("current") or StudentState()
    student.profile.name = student_name
    student.goal.career_title = job_role
    student_repo.save(student)

    return redirect(url_for("interview.interview_page"))


@interview_bp.route("/evaluate", methods=["POST"])
def legacy_evaluate():
    answer = request.form.get("answer", "").strip()
    student = student_repo.get("current") or StudentState()

    curr_q = session.get("current_question", "What is OOP?")
    role = session.get("job_role", "Software Engineer")
    diff = session.get("difficulty", "medium")
    q_num = session.get("question_number", 1)
    total_q = session.get("total_questions", 5)

    evaluation = evaluate_technical_answer(
        question=curr_q,
        answer=answer,
        job_role=role,
        difficulty=diff,
        topic=session.get("identified_weak_area", "OOP"),
        student=student
    )

    score = evaluation.get("score", 6)
    scores = session.get("score_history", [])
    scores.append(score)
    session["score_history"] = scores

    history = session.get("history", [])
    history.append({
        "question_number": q_num,
        "question": curr_q,
        "answer": answer,
        "score": score,
        "difficulty": diff,
        "evaluation": evaluation
    })
    session["history"] = history

    next_diff = "hard" if score >= 8 else ("easy" if score <= 4 else diff)
    session["difficulty"] = next_diff
    is_last = (q_num >= total_q)

    return render_template(
        "evaluation.html",
        student_name=session.get("student_name", "Student"),
        job_role=role,
        question_number=q_num,
        total_questions=total_q,
        score=score,
        evaluation=evaluation,
        difficulty=next_diff,
        identified_weak_area=evaluation.get("weak_area", "OOP"),
        is_last_question=is_last
    )


@interview_bp.route("/next-question")
def legacy_next_question():
    q_num = session.get("question_number", 1) + 1
    session["question_number"] = q_num
    session["current_question"] = f"Explain the practical mechanics of inheritance and polymorphism with an example. (Question {q_num})"

    return render_template(
        "next_question.html",
        student_name=session.get("student_name", "Student"),
        job_role=session.get("job_role", "Python Developer"),
        difficulty=session.get("difficulty", "medium"),
        question_number=q_num,
        total_questions=session.get("total_questions", 5),
        progress_percent=int((q_num / 5) * 100),
        current_question=session["current_question"],
        identified_weak_area=session.get("identified_weak_area", "OOP")
    )


@interview_bp.route("/final-result")
def legacy_final_result():
    scores = session.get("score_history", [7])
    total_score = sum(scores)
    avg_score = round(total_score / len(scores), 1)

    prep_plan = generate_daily_plan(student_repo.get("current") or StudentState())
    plan_dict = {
        "plan": [
            {"day": t["day"], "title": t["title"], "focus": t["focus"], "task": t["task"]}
            for t in prep_plan["tasks"]
        ],
        "overall_advice": prep_plan["overall_advice"]
    }

    return render_template(
        "result.html",
        student_name=session.get("student_name", "Arun"),
        job_role=session.get("job_role", "Python Developer"),
        skills=session.get("skills", "Python, C++, SQL"),
        prep_time=session.get("prep_time", "2 hours per day"),
        total_questions=len(scores),
        total_possible=len(scores) * 10,
        total_score=total_score,
        avg_score=avg_score,
        performance_badge="Good" if avg_score >= 5 else "Needs Improvement",
        performance_message="Solid core understanding with room for deeper system nuances.",
        strong_areas=["Object-Oriented Programming basics"],
        weak_areas=["Advanced Inheritance & Concurrency"],
        prep_plan=plan_dict,
        history=session.get("history", [])
    )


@interview_bp.route("/reset")
def legacy_reset():
    session.clear()
    student = student_repo.reset("current")
    flash("Session reset successfully.", "info")
    return redirect(url_for("main.index"))


@interview_bp.route("/api/status")
def legacy_api_status():
    return jsonify({
        "status": "online",
        "service": "AI Career Operating System & Interview Platform",
        "gemini_model": config.GEMINI_MODEL,
        "gemini_configured": bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_api_key_here"),
        "architecture": "OBSERVE -> ANALYZE -> PLAN -> RECOMMEND -> TEACH -> TEST -> EVALUATE -> ADAPT"
    })
