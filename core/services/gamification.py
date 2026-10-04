"""
Gamification & Real Achievement Engine
--------------------------------------
Unlocks achievements based strictly on verified student events and milestones.
NO FAKE ACHIEVEMENTS - Every unlock traces to actual stored activity.
"""

from typing import List, Dict, Any
from core.models import StudentState

ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "ach_diag",
        "title": "Knowledge Calibrated",
        "description": "Completed initial adaptive diagnostic assessment.",
        "icon": "🎯",
        "condition": lambda s: len(s.skills) > 0 and any(sk.get("attempts", 0) > 0 for sk in s.skills.values())
    },
    {
        "id": "ach_first_interview",
        "title": "First Mock Completed",
        "description": "Finished your first adaptive mock interview session.",
        "icon": "🎙️",
        "condition": lambda s: len(s.interviews) >= 1
    },
    {
        "id": "ach_five_interviews",
        "title": "Interview Veteran",
        "description": "Completed 5 mock interview sessions.",
        "icon": "🏆",
        "condition": lambda s: len(s.interviews) >= 5
    },
    {
        "id": "ach_resume_screen",
        "title": "ATS Ready",
        "description": "Screened resume and generated project questions.",
        "icon": "📄",
        "condition": lambda s: s.resume_analysis is not None
    },
    {
        "id": "ach_resource_master",
        "title": "Continuous Learner",
        "description": "Completed your first verified curriculum resource.",
        "icon": "📚",
        "condition": lambda s: any(r.get("status") == "completed" for r in s.resources.values())
    }
]


def check_and_unlock_achievements(student: StudentState) -> List[Dict[str, Any]]:
    """
    Evaluates student state against achievement conditions and unlocks new badges.
    """
    unlocked_ids = {a["id"] for a in student.achievements}
    newly_unlocked = []

    for item in ACHIEVEMENT_DEFINITIONS:
        a_id = item["id"]
        if a_id not in unlocked_ids:
            if item["condition"](student):
                badge = {
                    "id": a_id,
                    "title": item["title"],
                    "description": item["description"],
                    "icon": item["icon"]
                }
                student.achievements.append(badge)
                newly_unlocked.append(badge)

    return newly_unlocked
