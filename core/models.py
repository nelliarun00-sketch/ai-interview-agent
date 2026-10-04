"""
Domain Data Models (State Space & Knowledge Tracking)
-----------------------------------------------------
Defines pure dataclasses mapping directly to future DB tables.
All student state and educational entities are strictly typed.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid


@dataclass
class Profile:
    name: str = "Student"
    education: str = "B.Tech"
    specialization: str = "Computer Science"
    graduation_status: str = "Pre-final Year"
    experience_level: str = "Beginner"  # Beginner, Intermediate, Advanced
    hours_per_day: float = 2.0
    target_company: Optional[str] = None
    prep_type: str = "Campus Placements"  # Internships, Placements, Off-campus, Higher Studies
    preferred_learning_style: str = "Practice & Video"  # Video, Reading, Practice
    self_rated_skills: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return cls()
        return cls(
            name=data.get("name", "Student"),
            education=data.get("education", "B.Tech"),
            specialization=data.get("specialization", "Computer Science"),
            graduation_status=data.get("graduation_status", "Pre-final Year"),
            experience_level=data.get("experience_level", "Beginner"),
            hours_per_day=float(data.get("hours_per_day", 2.0)),
            target_company=data.get("target_company"),
            prep_type=data.get("prep_type", "Campus Placements"),
            preferred_learning_style=data.get("preferred_learning_style", "Practice & Video"),
            self_rated_skills=data.get("self_rated_skills", [])
        )


@dataclass
class Goal:
    career_id: str = "software_engineer"
    career_title: str = "Software Engineer"
    career_group: str = "Software Engineering"
    secondary_career_ids: List[str] = field(default_factory=list)
    target_date: Optional[str] = None
    is_custom: bool = False
    custom_role_description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return cls()
        return cls(
            career_id=data.get("career_id", "software_engineer"),
            career_title=data.get("career_title", "Software Engineer"),
            career_group=data.get("career_group", "Software Engineering"),
            secondary_career_ids=data.get("secondary_career_ids", []),
            target_date=data.get("target_date"),
            is_custom=data.get("is_custom", False),
            custom_role_description=data.get("custom_role_description")
        )


@dataclass
class SkillMastery:
    skill_id: str
    name: str
    mastery: float = 0.0      # 0.0 to 1.0 (estimated probability of knowledge)
    confidence: float = 0.1   # 0.0 to 1.0 (statistical confidence based on evidence)
    attempts: int = 0
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trend: str = "stable"     # improving, stable, declining
    recent_scores: List[float] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            skill_id=data.get("skill_id", ""),
            name=data.get("name", ""),
            mastery=float(data.get("mastery", 0.0)),
            confidence=float(data.get("confidence", 0.1)),
            attempts=int(data.get("attempts", 0)),
            last_seen=data.get("last_seen", datetime.now(timezone.utc).isoformat()),
            trend=data.get("trend", "stable"),
            recent_scores=data.get("recent_scores", [])
        )


@dataclass
class ResourceProgress:
    resource_id: str
    status: str = "not_started"  # not_started, in_progress, completed
    percent: int = 0
    minutes_spent: int = 0
    bookmarked: bool = False
    notes: str = ""
    last_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            resource_id=data.get("resource_id", ""),
            status=data.get("status", "not_started"),
            percent=int(data.get("percent", 0)),
            minutes_spent=int(data.get("minutes_spent", 0)),
            bookmarked=bool(data.get("bookmarked", False)),
            notes=data.get("notes", ""),
            last_accessed=data.get("last_accessed", datetime.now(timezone.utc).isoformat())
        )


@dataclass
class InterviewTurn:
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    question_id: Optional[str] = None
    topic: str = "general"
    question: str = ""
    answer: str = ""
    score: int = 0                  # 0 to 10
    difficulty: str = "medium"
    concepts_expected: List[str] = field(default_factory=list)
    concepts_covered: List[str] = field(default_factory=list)
    concepts_missed: List[str] = field(default_factory=list)
    misconceptions: List[str] = field(default_factory=list)
    strengths: str = ""
    improvements: str = ""
    weak_area: str = ""
    recommended_topic: str = ""
    better_answer: str = ""
    followup_suggestion: Optional[str] = None
    confidence_of_evaluation: float = 0.9
    source: str = "ai"              # ai or fallback


@dataclass
class InterviewSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    mode: str = "technical"         # technical, hr, behavioral, coding, system_design
    role: str = "Software Engineer"
    difficulty: str = "medium"
    turns: List[Dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    status: str = "in_progress"     # in_progress, completed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    feedback_summary: Optional[Dict[str, Any]] = None


@dataclass
class PlanTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    day: str = "Day 1"
    title: str = ""
    focus: str = ""
    task: str = ""
    task_type: str = "practice"    # learn, practice, test, review
    skill_id: Optional[str] = None
    time_minutes: int = 60
    completed: bool = False
    due_date: Optional[str] = None


@dataclass
class Plan:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_hours_per_day: float = 2.0
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    overall_advice: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Achievement:
    id: str
    title: str
    description: str
    icon: str
    unlocked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    message: str = ""
    type: str = "info"  # info, alert, success, adaptive
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read: bool = False


@dataclass
class StudentState:
    """
    The Central State Space Vector:
    Represents the full student trajectory across all features.
    """
    student_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    profile: Profile = field(default_factory=Profile)
    goal: Goal = field(default_factory=Goal)
    skills: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    interviews: List[Dict[str, Any]] = field(default_factory=list)
    plan: Optional[Dict[str, Any]] = None
    achievements: List[Dict[str, Any]] = field(default_factory=list)
    notifications: List[Dict[str, Any]] = field(default_factory=list)
    resume_analysis: Optional[Dict[str, Any]] = None
    project_status: Dict[str, str] = field(default_factory=dict) # project_id -> status
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return cls()
        return cls(
            student_id=data.get("student_id", str(uuid.uuid4())),
            profile=Profile.from_dict(data.get("profile", {})),
            goal=Goal.from_dict(data.get("goal", {})),
            skills=data.get("skills", {}),
            resources=data.get("resources", {}),
            interviews=data.get("interviews", []),
            plan=data.get("plan"),
            achievements=data.get("achievements", []),
            notifications=data.get("notifications", []),
            resume_analysis=data.get("resume_analysis"),
            project_status=data.get("project_status", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat())
        )
