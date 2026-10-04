"""
AI-Powered Interview Preparation & Evaluation Agent
---------------------------------------------------
Course / Subject: Fundamentals of Artificial Intelligence (FAI)
Description: An adaptive technical interview system built using Flask and Google Gemini AI.
Architecture: Demonstrates an autonomous AI Agent loop:
              OBSERVE -> ANALYZE -> DECIDE -> ACT -> ADAPT
"""

import os
import json
import re
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -------------------------------------------------------------
# 1. Environment & Configuration Setup
# -------------------------------------------------------------
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Secret key is required for Flask sessions (state management)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fai_interview_agent_secret_key_2026")

# Gemini Model configuration (Defaults to gemini-2.5-flash as recommended)
# You can change this in .env or directly here if needed
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Configure basic logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_gemini_client():
    """
    Initializes and returns the Google GenAI client using GEMINI_API_KEY from .env.
    Returns None if the key is missing or set to the default placeholder.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        logging.warning("GEMINI_API_KEY is not configured in .env. Running in simulation mode.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as err:
        logging.error(f"Failed to initialize Gemini Client: {err}")
        return None


# -------------------------------------------------------------
# 2. AI Decision Logic: Difficulty Adaptation
# -------------------------------------------------------------
def calculate_next_difficulty(current_difficulty: str, score: int) -> str:
    """
    Implements the DECIDE & ADAPT rules:
    - Score 0-4:  Reduce difficulty or keep at easy
    - Score 5-7:  Keep the same difficulty level
    - Score 8-10: Increase difficulty level
    """
    current_difficulty = (current_difficulty or "medium").lower()

    if score <= 4:
        # Decrease difficulty
        if current_difficulty == "hard":
            return "medium"
        return "easy"
    elif score <= 7:
        # Maintain difficulty
        return current_difficulty
    else:
        # Increase difficulty
        if current_difficulty == "easy":
            return "medium"
        return "hard"


# -------------------------------------------------------------
# 3. AI Agent Functions (Prompt Engineering & Execution)
# -------------------------------------------------------------

def generate_question(
    job_role: str,
    skills: str,
    weak_areas: str,
    difficulty: str = "medium",
    question_number: int = 1,
    previous_question: str = None,
    previous_answer: str = None,
    previous_score: int = None,
    identified_weak_area: str = None
) -> str:
    """
    AI AGENT - ACT STEP:
    Generates a targeted, adaptive technical interview question using Gemini AI.
    Adapts based on target role, current skills, weak areas, and previous performance.
    """
    client = get_gemini_client()
    target_weakness = identified_weak_area or weak_areas

    # Construct the adaptive interviewer prompt
    prompt = f"""You are a professional technical interviewer conducting a mock interview for a college student.

CANDIDATE INFORMATION:
- Target Job Role: {job_role}
- Current Technical Skills: {skills}
- Student Weak Area(s): {target_weakness}
- Current Question Number: {question_number} of 5
- Calibrated Difficulty Level: {difficulty}

PREVIOUS INTERVIEW CONTEXT:
- Previous Question: {previous_question if previous_question else 'None (First Question)'}
- Candidate's Previous Answer: {previous_answer if previous_answer else 'N/A'}
- Previous Score: {f'{previous_score}/10' if previous_score is not None else 'N/A'}

INTERVIEW RULES:
1. Generate exactly ONE technical interview question suitable for a college student.
2. The question must test knowledge relevant to the role: "{job_role}" and specifically target the weak area: "{target_weakness}".
3. Match the specified difficulty: "{difficulty}".
4. Do NOT include greetings, instructions, multiple choice options, or answers.
5. Return ONLY the question text.
"""

    if client:
        try:
            logging.info(f"Generating question #{question_number} via Gemini ({GEMINI_MODEL})...")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw_text = response.text.strip()
            # Clean any stray formatting quotes
            clean_question = raw_text.strip('"`\n ')
            if clean_question:
                return clean_question
        except Exception as e:
            logging.error(f"Gemini API error during question generation: {e}")

    # Fallback questions if API key is not yet set or external network is unavailable
    fallback_bank = {
        "oop": [
            "What are the four main principles of Object-Oriented Programming, and how does encapsulation differ from abstraction?",
            "Explain the difference between method overloading and method overriding with a real-world example.",
            "How does inheritance work, and what is the 'Diamond Problem' in multiple inheritance?",
            "What is polymorphism? Explain how runtime polymorphism is achieved in programming.",
            "Explain the concept of Abstract Classes and Interfaces. When would you prefer one over the other?"
        ],
        "dsa": [
            "What is the difference between an Array and a Linked List in terms of memory allocation and lookup time?",
            "Explain the concept of Big-O notation and analyze the time complexity of QuickSort in the average and worst case.",
            "How does a Hash Table resolve collisions? Explain separate chaining versus open addressing.",
            "What is the difference between Breadth-First Search (BFS) and Depth-First Search (DFS)?",
            "Explain how a Stack data structure can be used to check for balanced parentheses in an expression."
        ],
        "python": [
            "What is the difference between a mutable and an immutable data type in Python? Give two examples of each.",
            "How do list comprehensions work in Python, and why are they generally faster than standard for-loops?",
            "Explain what a Python generator is and how the 'yield' keyword differs from 'return'.",
            "What are *args and **kwargs in Python function definitions, and how are they used?",
            "How does Python manage memory, and what is the role of reference counting and garbage collection?"
        ],
        "sql": [
            "What is the difference between INNER JOIN and LEFT OUTER JOIN in SQL?",
            "Explain the difference between WHERE and HAVING clauses in an aggregation query.",
            "What is a primary key versus a unique foreign key in database normalization?",
            "What are database indexes, and what is the trade-off of having too many indexes?",
            "Explain the ACID properties in database transaction management."
        ]
    }

    # Match topic or default to generic technical questions
    topic_key = "python"
    weak_lower = target_weakness.lower()
    if "oop" in weak_lower or "object" in weak_lower:
        topic_key = "oop"
    elif "dsa" in weak_lower or "data structure" in weak_lower or "algorithm" in weak_lower:
        topic_key = "dsa"
    elif "sql" in weak_lower or "database" in weak_lower:
        topic_key = "sql"

    idx = (question_number - 1) % len(fallback_bank[topic_key])
    return fallback_bank[topic_key][idx]


def evaluate_answer(question: str, answer: str, job_role: str, skills: str, difficulty: str) -> dict:
    """
    AI AGENT - OBSERVE & ANALYZE STEP:
    Sends candidate's answer and question to Gemini AI for technical evaluation.
    Requires and safely parses strict JSON output.
    """
    client = get_gemini_client()

    prompt = f"""You are an expert technical interviewer evaluating a student's answer in a mock interview.

INTERVIEW CONTEXT:
- Target Job Role: {job_role}
- Candidate Skills: {skills}
- Question Difficulty: {difficulty}
- Interview Question: {question}
- Candidate's Submitted Answer: {answer}

EVALUATION TASK:
Evaluate the answer rigorously but constructively based on:
1. Technical correctness and concept depth
2. Clarity of communication
3. Missing technical nuances or misconceptions

OUTPUT INSTRUCTIONS:
Return ONLY valid JSON. Do not use Markdown code fences (do NOT include ```json or ```).
The JSON must strictly conform to this schema:
{{
    "score": <integer from 0 to 10>,
    "strengths": "<1-2 clear sentences on what the student explained correctly>",
    "improvements": "<1-2 clear sentences on specific concepts missing or needing improvement>",
    "weak_area": "<concise name of the specific technical concept where student showed weakness>",
    "recommended_topic": "<specific study topic the student should review next>",
    "better_answer": "<a comprehensive, accurate model answer in 3-5 sentences that would earn 10/10>",
    "next_difficulty": "<easy, medium, or hard based on student performance>"
}}
"""

    if client:
        try:
            logging.info("Requesting structured evaluation from Gemini...")
            # Request JSON output directly using SDK configuration
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()
            # Clean potential markdown fences if present
            cleaned_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()

            parsed = json.loads(cleaned_text)

            # Validate and clamp score safely between 0 and 10
            score_val = int(parsed.get("score", 5))
            score_val = max(0, min(10, score_val))

            return {
                "score": score_val,
                "strengths": str(parsed.get("strengths", "Demonstrated basic familiarity with the topic.")),
                "improvements": str(parsed.get("improvements", "Elaborate with more depth and technical examples.")),
                "weak_area": str(parsed.get("weak_area", "Core concepts")),
                "recommended_topic": str(parsed.get("recommended_topic", "Technical fundamentals")),
                "better_answer": str(parsed.get("better_answer", "A comprehensive answer explains definitions, trade-offs, and examples.")),
                "next_difficulty": str(parsed.get("next_difficulty", difficulty)).lower()
            }
        except Exception as e:
            logging.error(f"Error parsing Gemini evaluation response: {e}")

    # Fallback evaluation simulation if API is not active or encounters an error
    words = len(answer.strip().split())
    if words < 8:
        score = 3
        strengths = "Attempted an answer, showing initial engagement with the topic."
        improvements = "The answer was very brief. Include definitions, mechanics, and examples."
        weak_area = "Conceptual depth and completeness"
        rec_topic = "Fundamental technical definitions and explanations"
    elif words < 25:
        score = 6
        strengths = "Understood the basic core idea and answered the direct prompt."
        improvements = "Needs deeper technical detail, real-world examples, and discussion of trade-offs."
        weak_area = "Technical precision and edge cases"
        rec_topic = "In-depth application and code implementation"
    else:
        score = 8
        strengths = "Solid structured explanation with good technical vocabulary."
        improvements = "Could further mention performance considerations or edge cases."
        weak_area = "Advanced optimizations"
        rec_topic = "Advanced architectural best practices"

    next_diff = calculate_next_difficulty(difficulty, score)

    return {
        "score": score,
        "strengths": strengths,
        "improvements": improvements,
        "weak_area": weak_area,
        "recommended_topic": rec_topic,
        "better_answer": f"A comprehensive answer to '{question}' should systematically define the core concept, explain how it operates under the hood, and illustrate its practical relevance in software engineering.",
        "next_difficulty": next_diff
    }


def generate_preparation_plan(
    student_name: str,
    job_role: str,
    skills: str,
    prep_time: str,
    weak_areas: list,
    average_score: float,
    evaluations_summary: list
) -> dict:
    """
    AI AGENT - FINAL ADAPTIVE PLAN:
    Generates a customized 5-day study roadmap based on cumulative interview performance.
    """
    client = get_gemini_client()
    weak_areas_str = ", ".join(weak_areas) if weak_areas else "General technical foundations"

    prompt = f"""You are a college technical career advisor. Build a personalized 5-day study plan for a student.

STUDENT DETAILS:
- Name: {student_name}
- Target Role: {job_role}
- Skills: {skills}
- Daily Study Time Available: {prep_time}
- Interview Average Score: {average_score}/10
- Key Technical Weaknesses Identified: {weak_areas_str}

TASK:
Produce a realistic, day-by-day 5-day preparation roadmap tailored to their daily study time of {prep_time}.
Focus heavily on remediating their identified weak areas.

OUTPUT INSTRUCTIONS:
Return ONLY valid JSON without Markdown code blocks.
Schema:
{{
    "plan": [
        {{"day": "Day 1", "title": "<topic title>", "focus": "<what to review>", "task": "<actionable exercise>"}},
        {{"day": "Day 2", "title": "<topic title>", "focus": "<what to review>", "task": "<actionable exercise>"}},
        {{"day": "Day 3", "title": "<topic title>", "focus": "<what to review>", "task": "<actionable exercise>"}},
        {{"day": "Day 4", "title": "<topic title>", "focus": "<what to review>", "task": "<actionable exercise>"}},
        {{"day": "Day 5", "title": "<topic title>", "focus": "<what to review>", "task": "<actionable exercise>"}}
    ],
    "overall_advice": "<2-3 sentences of encouraging, actionable career advice>"
}}
"""

    if client:
        try:
            logging.info("Generating personalized preparation plan from Gemini...")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            cleaned = re.sub(r"^```(?:json)?\s*", "", response.text.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()
            return json.loads(cleaned)
        except Exception as e:
            logging.error(f"Error generating preparation plan with Gemini: {e}")

    # Fallback plan tailored to common college technical interviews
    focus_topic = weak_areas[0] if weak_areas else "Core Fundamentals"
    return {
        "plan": [
            {
                "day": "Day 1",
                "title": f"Review Basics: {focus_topic}",
                "focus": f"Review definitions, core principles, and conceptual foundations of {focus_topic}.",
                "task": f"Dedicate your {prep_time} to writing notes and explaining 3 key concepts aloud."
            },
            {
                "day": "Day 2",
                "title": "Hands-On Code Practice",
                "focus": "Practical code syntax, error handling, and standard library methods.",
                "task": f"Write and run 5 small code examples covering your weak technical areas."
            },
            {
                "day": "Day 3",
                "title": "Problem Solving & Edge Cases",
                "focus": "Algorithmic thinking, time/space complexity, and common interview traps.",
                "task": "Solve 2-3 standard technical interview problems without checking solutions first."
            },
            {
                "day": "Day 4",
                "title": f"System & Architecture Integration for {job_role}",
                "focus": "How these components integrate in real-world software applications.",
                "task": "Review one open-source repo or project applying these concepts in production."
            },
            {
                "day": "Day 5",
                "title": "Full Mock Technical Interview",
                "focus": "Verbal articulation, pacing, and concise technical explanations.",
                "task": "Take another round of mock interviews with the AI Agent to measure your progress!"
            }
        ],
        "overall_advice": f"Consistent practice for {prep_time} will compound quickly. Focus on explaining the 'why' behind each technology rather than just memorizing syntax."
    }


# -------------------------------------------------------------
# 4. Flask Application Web Routes
# -------------------------------------------------------------

@app.route("/")
def index():
    """Renders the Home Page where the student inputs their profile."""
    return render_template("index.html")


@app.route("/start-interview", methods=["POST"])
def start_interview():
    """
    Initializes the interview session and generates Question 1.
    """
    student_name = request.form.get("student_name", "").strip()
    job_role = request.form.get("job_role", "").strip()
    skills = request.form.get("skills", "").strip()
    weak_areas = request.form.get("weak_areas", "").strip()
    prep_time = request.form.get("prep_time", "").strip()

    # Form validation
    if not student_name or not job_role or not skills:
        flash("Please fill in all required fields to begin the interview.", "warning")
        return redirect(url_for("index"))

    # Reset & initialize session state
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
    session["recommended_topic"] = ""

    # Generate Question 1
    q1 = generate_question(
        job_role=job_role,
        skills=skills,
        weak_areas=weak_areas,
        difficulty="medium",
        question_number=1,
        identified_weak_area=weak_areas
    )
    session["current_question"] = q1
    session.modified = True

    return redirect(url_for("interview"))


@app.route("/interview", methods=["GET"])
def interview():
    """
    Renders the active interview question answering page.
    """
    if "student_name" not in session:
        flash("Please start an interview first.", "warning")
        return redirect(url_for("index"))

    q_num = session.get("question_number", 1)
    total_q = session.get("total_questions", 5)

    if q_num > total_q:
        return redirect(url_for("final_result"))

    progress_percent = int((q_num / total_q) * 100)

    return render_template(
        "interview.html",
        student_name=session.get("student_name"),
        job_role=session.get("job_role"),
        skills=session.get("skills"),
        difficulty=session.get("difficulty", "medium"),
        question_number=q_num,
        total_questions=total_q,
        progress_percent=progress_percent,
        current_question=session.get("current_question"),
        identified_weak_area=session.get("identified_weak_area")
    )


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """
    Processes candidate answer, calls Gemini evaluation, adapts difficulty,
    and displays evaluation feedback.
    """
    if "student_name" not in session:
        flash("Session expired. Please restart the interview.", "warning")
        return redirect(url_for("index"))

    answer = request.form.get("answer", "").strip()
    if not answer:
        flash("Please write an answer before submitting.", "warning")
        return redirect(url_for("interview"))

    current_q = session.get("current_question", "")
    job_role = session.get("job_role", "")
    skills = session.get("skills", "")
    curr_diff = session.get("difficulty", "medium")
    q_num = session.get("question_number", 1)
    total_q = session.get("total_questions", 5)

    # 1. EVALUATION (Gemini AI)
    evaluation = evaluate_answer(
        question=current_q,
        answer=answer,
        job_role=job_role,
        skills=skills,
        difficulty=curr_diff
    )

    score = evaluation.get("score", 5)

    # 2. ADAPTIVE STATE UPDATES (AI Agent DECIDE Step)
    scores = session.get("score_history", [])
    scores.append(score)
    session["score_history"] = scores

    history = session.get("history", [])
    history.append({
        "question_number": q_num,
        "question": current_q,
        "answer": answer,
        "score": score,
        "difficulty": curr_diff,
        "evaluation": evaluation
    })
    session["history"] = history

    # Calculate adapted difficulty for next question
    next_diff = calculate_next_difficulty(curr_diff, score)
    session["difficulty"] = next_diff

    # Update weak area and context for next question
    new_weak_area = evaluation.get("weak_area") or session.get("identified_weak_area")
    session["identified_weak_area"] = new_weak_area
    session["recommended_topic"] = evaluation.get("recommended_topic", "")
    session["previous_question"] = current_q
    session["previous_answer"] = answer
    session.modified = True

    is_last = (q_num >= total_q)

    return render_template(
        "evaluation.html",
        student_name=session.get("student_name"),
        job_role=job_role,
        question_number=q_num,
        total_questions=total_q,
        score=score,
        evaluation=evaluation,
        difficulty=next_diff,
        identified_weak_area=new_weak_area,
        is_last_question=is_last
    )


@app.route("/next-question", methods=["GET", "POST"])
def next_question():
    """
    AI AGENT - ACT STEP:
    Generates the next question targeted at the student's identified weak area,
    calibrated to the new difficulty level, and renders next_question.html.
    """
    if "student_name" not in session:
        flash("Session expired. Please restart the interview.", "warning")
        return redirect(url_for("index"))

    q_num = session.get("question_number", 1)
    total_q = session.get("total_questions", 5)

    # If all 5 questions finished, go to final summary
    if q_num >= total_q:
        return redirect(url_for("final_result"))

    # Increment question number
    q_num += 1
    session["question_number"] = q_num

    # Generate next question with adapted parameters
    next_q = generate_question(
        job_role=session.get("job_role"),
        skills=session.get("skills"),
        weak_areas=session.get("weak_areas"),
        difficulty=session.get("difficulty", "medium"),
        question_number=q_num,
        previous_question=session.get("previous_question"),
        previous_answer=session.get("previous_answer"),
        previous_score=session.get("score_history", [])[-1] if session.get("score_history") else None,
        identified_weak_area=session.get("identified_weak_area")
    )

    session["current_question"] = next_q
    session.modified = True

    progress_percent = int((q_num / total_q) * 100)

    return render_template(
        "next_question.html",
        student_name=session.get("student_name"),
        job_role=session.get("job_role"),
        difficulty=session.get("difficulty", "medium"),
        question_number=q_num,
        total_questions=total_q,
        progress_percent=progress_percent,
        current_question=next_q,
        identified_weak_area=session.get("identified_weak_area")
    )


@app.route("/final-result", methods=["GET"])
def final_result():
    """
    Renders final interview summary, cumulative analytics,
    and the personalized 5-day preparation plan.
    """
    if "student_name" not in session or not session.get("score_history"):
        flash("No completed interview session found. Please start an interview.", "warning")
        return redirect(url_for("index"))

    history = session.get("history", [])
    scores = session.get("score_history", [])
    total_score = sum(scores)
    total_q = len(scores)
    avg_score = round(total_score / total_q, 1) if total_q > 0 else 0

    # Categorize performance
    if avg_score >= 8.0:
        perf_badge = "Excellent"
        perf_msg = "Outstanding technical mastery and clear communication throughout the interview!"
    elif avg_score >= 5.0:
        perf_badge = "Good"
        perf_msg = "Demonstrated solid core technical skills with room for improvement in edge cases."
    else:
        perf_badge = "Needs Improvement"
        perf_msg = "Conceptual foundation needs reinforcement before appearing for actual technical rounds."

    # Extract distinct strengths and weak areas from history
    strong_areas = []
    weak_areas = []
    for item in history:
        ev = item.get("evaluation", {})
        s = ev.get("strengths")
        w = ev.get("weak_area")
        r = ev.get("recommended_topic")
        if s and s not in strong_areas:
            strong_areas.append(s)
        if w and w not in weak_areas:
            weak_areas.append(f"{w} (Review: {r})" if r else w)

    # Generate 5-day preparation plan
    prep_plan = generate_preparation_plan(
        student_name=session.get("student_name"),
        job_role=session.get("job_role"),
        skills=session.get("skills"),
        prep_time=session.get("prep_time", "2 hours per day"),
        weak_areas=weak_areas,
        average_score=avg_score,
        evaluations_summary=history
    )

    return render_template(
        "result.html",
        student_name=session.get("student_name"),
        job_role=session.get("job_role"),
        skills=session.get("skills"),
        prep_time=session.get("prep_time"),
        total_questions=total_q,
        total_possible=total_q * 10,
        total_score=total_score,
        avg_score=avg_score,
        performance_badge=perf_badge,
        performance_message=perf_msg,
        strong_areas=strong_areas[:4],
        weak_areas=weak_areas[:4],
        prep_plan=prep_plan,
        history=history
    )


@app.route("/reset", methods=["GET", "POST"])
def reset():
    """Clears the session and redirects to the home page."""
    session.clear()
    flash("Interview reset successfully. You can begin a new session.", "info")
    return redirect(url_for("index"))


@app.route("/api/status", methods=["GET"])
def api_status():
    """Health check endpoint."""
    has_api_key = bool(os.environ.get("GEMINI_API_KEY", "").strip() and os.environ.get("GEMINI_API_KEY") != "your_api_key_here")
    return jsonify({
        "status": "online",
        "service": "AI-Powered Interview Preparation & Evaluation Agent",
        "gemini_api_configured": has_api_key,
        "gemini_model": GEMINI_MODEL,
        "architecture": "OBSERVE -> ANALYZE -> DECIDE -> ACT -> ADAPT"
    })


# -------------------------------------------------------------
# 5. Main Entrypoint
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
