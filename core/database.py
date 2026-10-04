"""
Database Engine & Persistence Layer for AI Career Mentor
--------------------------------------------------------
SQLite-backed multi-student database with complete entity isolation,
password hashing, and relational schema mapping.
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "career_mentor.db")
)



def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # 2. Student State JSON Blob Table (for instant round-trip with StudentState)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_states (
                user_id INTEGER PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 3. Student Profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                user_id INTEGER PRIMARY KEY,
                education TEXT,
                specialization TEXT,
                graduation_status TEXT,
                target_role TEXT,
                target_industry TEXT,
                target_company TEXT,
                prep_type TEXT,
                prep_time TEXT,
                hours_per_day REAL DEFAULT 2.0,
                experience_level TEXT DEFAULT 'Beginner',
                weak_areas TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 4. Student Skills (Knowledge Tracing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                name TEXT NOT NULL,
                mastery REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.1,
                attempts INTEGER DEFAULT 0,
                trend TEXT DEFAULT 'stable',
                last_seen TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, skill_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 5. Interview History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                role TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                overall_score REAL NOT NULL,
                turns_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 6. Learning Progress & Bookmarks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                status TEXT DEFAULT 'not_started',
                percent INTEGER DEFAULT 0,
                minutes_spent INTEGER DEFAULT 0,
                bookmarked INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, resource_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 7. Resumes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT,
                ats_score INTEGER DEFAULT 0,
                analysis_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 8. Job Description Matches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                job_title TEXT,
                match_percent INTEGER DEFAULT 0,
                job_description TEXT,
                analysis_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 9. Daily Tasks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id TEXT NOT NULL,
                day TEXT,
                title TEXT,
                focus TEXT,
                task TEXT,
                task_type TEXT,
                skill_id TEXT,
                time_minutes INTEGER DEFAULT 30,
                completed INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, task_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        conn.commit()

    # Seed demo users if empty
    seed_demo_accounts()


# -------------------------------------------------------------
# User Authentication Helpers
# -------------------------------------------------------------
def create_user(email: str, password: str, full_name: str) -> Optional[Dict[str, Any]]:
    email = email.strip().lower()
    full_name = full_name.strip()
    if not email or not password or not full_name:
        return None

    password_hash = generate_password_hash(password)
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
                (email, password_hash, full_name, now)
            )
            user_id = cursor.lastrowid
            conn.commit()

        # Initialize default StudentState for new user
        from core.models import StudentState, Profile, Goal
        student = StudentState(
            student_id=f"usr_{user_id}",
            profile=Profile(
                name=full_name,
                education="B.Tech",
                specialization="Computer Science",
                graduation_status="Pre-final Year",
                experience_level="Beginner",
                hours_per_day=2.0
            ),
            goal=Goal(
                career_id="software_engineer",
                career_title="Software Development Engineer (SDE / SWE)",
                career_group="Software Engineering"
            )
        )
        save_student_state_by_user_id(user_id, student)

        return {"id": user_id, "email": email, "full_name": full_name}
    except sqlite3.IntegrityError:
        return None  # Email already exists


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, full_name, created_at FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row and check_password_hash(row["password_hash"], password):
            return {
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "created_at": row["created_at"]
            }
    return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, created_at FROM users WHERE email = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_user_password(user_id: int, new_password: str) -> bool:
    password_hash = generate_password_hash(new_password)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


# -------------------------------------------------------------
# Student State & Multi-Student Isolation
# -------------------------------------------------------------
def get_student_state_by_user_id(user_id: int):
    from core.models import StudentState
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT state_json FROM student_states WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row["state_json"]:
            try:
                data = json.loads(row["state_json"])
                return StudentState.from_dict(data)
            except Exception as e:
                print(f"Error parsing state JSON for user {user_id}: {e}")

    # Fallback: create fresh state if user exists
    user = get_user_by_id(user_id)
    if user:
        from core.models import StudentState, Profile, Goal
        student = StudentState(
            student_id=f"usr_{user_id}",
            profile=Profile(name=user["full_name"]),
            goal=Goal(career_id="software_engineer", career_title="Software Development Engineer (SDE / SWE)")
        )
        save_student_state_by_user_id(user_id, student)
        return student

    return None


def save_student_state_by_user_id(user_id: int, student) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state_dict = student.to_dict()
    state_json = json.dumps(state_dict)

    with get_db() as conn:
        cursor = conn.cursor()
        # 1. Update State Blob
        cursor.execute("""
            INSERT INTO student_states (user_id, state_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
        """, (user_id, state_json, now))

        # 2. Sync Profile Table
        p = student.profile
        g = student.goal
        cursor.execute("""
            INSERT INTO student_profiles (
                user_id, education, specialization, graduation_status,
                target_role, target_industry, target_company,
                prep_type, prep_time, hours_per_day, experience_level,
                weak_areas, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                education = excluded.education,
                specialization = excluded.specialization,
                graduation_status = excluded.graduation_status,
                target_role = excluded.target_role,
                target_industry = excluded.target_industry,
                target_company = excluded.target_company,
                prep_type = excluded.prep_type,
                prep_time = excluded.prep_time,
                hours_per_day = excluded.hours_per_day,
                experience_level = excluded.experience_level,
                weak_areas = excluded.weak_areas,
                updated_at = excluded.updated_at
        """, (
            user_id, p.education, p.specialization, p.graduation_status,
            g.career_title, g.career_group, p.target_company,
            p.prep_type, f"{p.hours_per_day} hours/day", p.hours_per_day,
            p.experience_level, ", ".join(p.self_rated_skills), now
        ))

        # 3. Sync Skills Table
        for s_id, s_data in student.skills.items():
            cursor.execute("""
                INSERT INTO student_skills (
                    user_id, skill_id, name, mastery, confidence, attempts, trend, last_seen, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, skill_id) DO UPDATE SET
                    mastery = excluded.mastery,
                    confidence = excluded.confidence,
                    attempts = excluded.attempts,
                    trend = excluded.trend,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at
            """, (
                user_id, s_id, s_data.get("name", s_id),
                float(s_data.get("mastery", 0.0)), float(s_data.get("confidence", 0.1)),
                int(s_data.get("attempts", 0)), s_data.get("trend", "stable"),
                s_data.get("last_seen", now), now
            ))

        # 4. Sync Interviews Table
        for inv in student.interviews:
            inv_id = str(inv.get("id", ""))
            if inv_id:
                cursor.execute("""
                    INSERT OR REPLACE INTO interviews (
                        id, user_id, mode, role, difficulty, overall_score, turns_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inv_id, user_id, inv.get("mode", "technical"),
                    inv.get("role", g.career_title), inv.get("difficulty", "medium"),
                    float(inv.get("overall_score", 0.0)),
                    json.dumps(inv.get("turns", [])),
                    inv.get("created_at", now)
                ))

        # 5. Sync Learning Progress Table
        for r_id, r_prog in student.resources.items():
            cursor.execute("""
                INSERT INTO learning_progress (
                    user_id, resource_id, status, percent, minutes_spent, bookmarked, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, resource_id) DO UPDATE SET
                    status = excluded.status,
                    percent = excluded.percent,
                    minutes_spent = excluded.minutes_spent,
                    bookmarked = excluded.bookmarked,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (
                user_id, r_id, r_prog.get("status", "not_started"),
                int(r_prog.get("percent", 0)), int(r_prog.get("minutes_spent", 0)),
                1 if r_prog.get("bookmarked") else 0,
                r_prog.get("notes", ""), now
            ))

        conn.commit()


def save_job_match(user_id: int, job_title: str, match_percent: int, job_description: str, analysis: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO job_matches (user_id, job_title, match_percent, job_description, analysis_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, job_title, match_percent, job_description, json.dumps(analysis), now))
        conn.commit()


def get_job_matches(user_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_matches WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
        rows = cursor.fetchall()
        matches = []
        for r in rows:
            m = dict(r)
            m["analysis"] = json.loads(m["analysis_json"]) if m.get("analysis_json") else {}
            matches.append(m)
        return matches


# -------------------------------------------------------------
# Demo Accounts Seeder
# -------------------------------------------------------------
def seed_demo_accounts():
    """
    Seeds the 3 canonical demo student accounts:
    1. Arun (arun@example.com) -> Python Developer / SDE (72% Readiness)
    2. Rahul (rahul@example.com) -> Data Analyst / Data Scientist (61% Readiness)
    3. Ananya (ananya@example.com) -> AI/ML Engineer (80% Readiness)
    """
    from core.models import StudentState, Profile, Goal

    demo_users = [
        {
            "email": "arun@example.com",
            "password": "password123",
            "full_name": "Arun Kumar",
            "education": "B.Tech",
            "specialization": "Computer Science & Engineering",
            "grad": "Final Year",
            "hours": 2.0,
            "role": "Software Development Engineer (SDE / SWE)",
            "career_id": "software_engineer",
            "group": "Software Engineering",
            "skills": {
                "python": {"name": "Python", "mastery": 0.88, "confidence": 0.9, "attempts": 12, "trend": "improving"},
                "cpp": {"name": "C++", "mastery": 0.75, "confidence": 0.8, "attempts": 8, "trend": "stable"},
                "oop": {"name": "Object-Oriented Programming", "mastery": 0.76, "confidence": 0.8, "attempts": 7, "trend": "improving"},
                "sql": {"name": "SQL & Relational Databases", "mastery": 0.68, "confidence": 0.7, "attempts": 6, "trend": "stable"},
                "dsa": {"name": "Data Structures & Algorithms", "mastery": 0.48, "confidence": 0.6, "attempts": 9, "trend": "improving"},
                "system_design": {"name": "System Design Fundamentals", "mastery": 0.35, "confidence": 0.5, "attempts": 4, "trend": "stable"}
            },
            "interviews_count": 12,
            "avg_score": 7.8,
            "best_score": 9.2,
            "questions_answered": 47,
            "resources": {
                "res_py_01": {"status": "completed", "percent": 100, "bookmarked": True},
                "res_py_02": {"status": "completed", "percent": 100, "bookmarked": False},
                "res_dsa_01": {"status": "in_progress", "percent": 60, "bookmarked": True},
                "res_dsa_02": {"status": "in_progress", "percent": 40, "bookmarked": True},
                "res_oop_01": {"status": "completed", "percent": 100, "bookmarked": False},
                "res_sql_01": {"status": "in_progress", "percent": 70, "bookmarked": True}
            }
        },
        {
            "email": "rahul@example.com",
            "password": "password123",
            "full_name": "Rahul Verma",
            "education": "BCA / MCA",
            "specialization": "Data Science & Analytics",
            "grad": "Pre-final Year",
            "hours": 1.5,
            "role": "Data Scientist",
            "career_id": "data_scientist",
            "group": "Data & Analytics",
            "skills": {
                "python": {"name": "Python", "mastery": 0.65, "confidence": 0.7, "attempts": 6, "trend": "stable"},
                "sql": {"name": "SQL & Relational Databases", "mastery": 0.78, "confidence": 0.8, "attempts": 8, "trend": "improving"},
                "applied_statistics": {"name": "Applied Statistics & Probability", "mastery": 0.50, "confidence": 0.5, "attempts": 4, "trend": "declining"},
                "dsa": {"name": "Data Structures & Algorithms", "mastery": 0.40, "confidence": 0.4, "attempts": 3, "trend": "stable"},
                "data_analysis": {"name": "Data Analysis & Pandas", "mastery": 0.72, "confidence": 0.7, "attempts": 7, "trend": "improving"}
            },
            "interviews_count": 4,
            "avg_score": 6.8,
            "best_score": 7.5,
            "questions_answered": 18,
            "resources": {
                "res_sql_01": {"status": "completed", "percent": 100, "bookmarked": True},
                "res_py_01": {"status": "completed", "percent": 100, "bookmarked": False},
                "res_ds_01": {"status": "in_progress", "percent": 50, "bookmarked": True}
            }
        },
        {
            "email": "ananya@example.com",
            "password": "password123",
            "full_name": "Ananya Sen",
            "education": "M.Tech",
            "specialization": "Artificial Intelligence",
            "grad": "Final Year",
            "hours": 3.0,
            "role": "Machine Learning & AI Engineer",
            "career_id": "ml_engineer",
            "group": "Artificial Intelligence & ML",
            "skills": {
                "python": {"name": "Python", "mastery": 0.85, "confidence": 0.9, "attempts": 10, "trend": "improving"},
                "classical_ml": {"name": "Classical Machine Learning", "mastery": 0.78, "confidence": 0.8, "attempts": 8, "trend": "improving"},
                "deep_learning": {"name": "Deep Learning & Neural Networks", "mastery": 0.60, "confidence": 0.6, "attempts": 5, "trend": "stable"},
                "applied_statistics": {"name": "Applied Statistics & Probability", "mastery": 0.70, "confidence": 0.7, "attempts": 6, "trend": "improving"},
                "model_deployment": {"name": "Model Deployment & MLOps", "mastery": 0.45, "confidence": 0.4, "attempts": 3, "trend": "stable"}
            },
            "interviews_count": 8,
            "avg_score": 8.2,
            "best_score": 9.5,
            "questions_answered": 36,
            "resources": {
                "res_ml_01": {"status": "completed", "percent": 100, "bookmarked": True},
                "res_py_01": {"status": "completed", "percent": 100, "bookmarked": False},
                "res_ml_02": {"status": "in_progress", "percent": 65, "bookmarked": True}
            }
        }
    ]

    for d in demo_users:
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (d["email"].strip().lower(),))
                if cursor.fetchone():
                    continue

                now = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    "INSERT INTO users (email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
                    (d["email"], generate_password_hash(d["password"]), d["full_name"], now)
                )
                user_id = cursor.lastrowid
                conn.commit()

            # Build mock interviews
            interviews = []
            for i in range(d["interviews_count"]):
                step_score = round(min(10.0, d["avg_score"] - 1.5 + (i * 0.3)), 1)
                interviews.append({
                    "id": f"inv_{user_id}_{i+1}",
                    "mode": "technical",
                    "role": d["role"],
                    "difficulty": "medium" if i < 6 else "hard",
                    "overall_score": step_score,
                    "created_at": now,
                    "turns": [
                        {
                            "question_number": 1,
                            "question": f"Key question on {d['role']} principles?",
                            "answer": "Clear explanation with examples.",
                            "score": int(step_score),
                            "difficulty": "medium",
                            "evaluation": {
                                "score": int(step_score),
                                "strengths": "Clear terminology and structured logic.",
                                "improvements": "Mention edge cases and complexity tradeoffs."
                            }
                        }
                    ]
                })

            # Create and populate StudentState
            student = StudentState(
                student_id=f"usr_{user_id}",
                profile=Profile(
                    name=d["full_name"],
                    education=d["education"],
                    specialization=d["specialization"],
                    graduation_status=d["grad"],
                    experience_level="Intermediate" if d["avg_score"] > 7.0 else "Beginner",
                    hours_per_day=d["hours"],
                    self_rated_skills=list(d["skills"].keys())
                ),
                goal=Goal(
                    career_id=d["career_id"],
                    career_title=d["role"],
                    career_group=d["group"]
                ),
                skills=d["skills"],
                resources=d["resources"],
                interviews=interviews,
                plan={
                    "completed_task_ids": ["task_1", "task_2"]
                }
            )

            save_student_state_by_user_id(user_id, student)
            print(f"Seeded demo student account: {d['email']} (ID: {user_id})")
        except sqlite3.IntegrityError:
            # Concurrently seeded by another worker process
            continue

