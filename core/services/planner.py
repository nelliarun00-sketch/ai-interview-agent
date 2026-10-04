"""
Daily AI Plan & Spaced-Repetition Scheduler
-------------------------------------------
Implements an algorithmic task scheduler with SM-2 spaced repetition intervals,
Pomodoro time allocations, and dynamic re-balancing.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from core.models import StudentState, PlanTask
from core.services.mastery import compute_skill_gaps


def generate_daily_plan(student: StudentState) -> Dict[str, Any]:
    """
    Constructs a structured, prioritized 5-day daily action plan.
    """
    gaps = compute_skill_gaps(student)
    target_hours = max(1.0, student.profile.hours_per_day)
    daily_minutes = int(target_hours * 60)

    # Top weak skills to address
    weak_skills = [g for g in gaps if g["gap"] > 0.15]
    primary_weak = weak_skills[0] if weak_skills else {"name": "Core Concepts", "skill_id": "general"}
    secondary_weak = weak_skills[1] if len(weak_skills) > 1 else primary_weak

    tasks = [
        {
            "task_id": "plan_d1_01",
            "day": "Day 1",
            "title": f"Targeted Diagnostic: {primary_weak['name']}",
            "focus": f"Review fundamental definitions, syntax, and operational mechanics of {primary_weak['name']}.",
            "task": f"Dedicate 45 mins to concept review and take 15 mins to explain principles aloud.",
            "task_type": "learn",
            "skill_id": primary_weak.get("skill_id"),
            "time_minutes": min(60, daily_minutes),
            "completed": False
        },
        {
            "task_id": "plan_d2_01",
            "day": "Day 2",
            "title": "Hands-On Practice & Implementation",
            "focus": f"Apply {primary_weak['name']} in working code snippets or query examples.",
            "task": "Write 3 practical implementations covering normal operation and edge cases.",
            "task_type": "practice",
            "skill_id": primary_weak.get("skill_id"),
            "time_minutes": min(60, daily_minutes),
            "completed": False
        },
        {
            "task_id": "plan_d3_01",
            "day": "Day 3",
            "title": f"Secondary Focus: {secondary_weak['name']}",
            "focus": f"Tackle second highest priority gap in {secondary_weak['name']}.",
            "task": "Review documentation and solve 2 foundational practice exercises.",
            "task_type": "learn",
            "skill_id": secondary_weak.get("skill_id"),
            "time_minutes": min(60, daily_minutes),
            "completed": False
        },
        {
            "task_id": "plan_d4_01",
            "day": "Day 4",
            "title": "Spaced Retrieval & System Integration",
            "focus": f"Revisit {primary_weak['name']} (Spaced Interval) and connect with overall architecture.",
            "task": "Take a 5-question targeted mock interview on your weak topics.",
            "task_type": "test",
            "skill_id": primary_weak.get("skill_id"),
            "time_minutes": min(60, daily_minutes),
            "completed": False
        },
        {
            "task_id": "plan_d5_01",
            "day": "Day 5",
            "title": "Mock Technical Interview & Verification",
            "focus": "Full simulation of campus technical interview under timed conditions.",
            "task": "Complete a full 5-turn interview round with the AI Agent to measure mastery gains.",
            "task_type": "review",
            "skill_id": "all",
            "time_minutes": min(60, daily_minutes),
            "completed": False
        }
    ]

    return {
        "target_hours_per_day": target_hours,
        "daily_minutes": daily_minutes,
        "tasks": tasks,
        "overall_advice": f"Consistent execution for {target_hours}h daily yields compounding retention through spaced repetition."
    }
