"""
Session & JSON File Repository Implementation
---------------------------------------------
Implements the repository contracts using Flask Session for student state
and local JSON files for curriculum knowledge graphs and resource banks.
"""

import json
import os
from typing import Optional, Dict, Any, List
from flask import session
from core.models import StudentState
from core.repositories.base import StudentRepository, DataRepository

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


class SessionStudentRepository(StudentRepository):
    """
    Persistent student repository with SQLite user-level isolation
    and Flask session fallback for backward compatibility & testing.
    """
    def get(self, student_id: str = "current") -> Optional[StudentState]:
        try:
            user_id = session.get("user_id")
            if user_id:
                from core.database import get_student_state_by_user_id
                db_student = get_student_state_by_user_id(user_id)
                if db_student:
                    return db_student
        except RuntimeError:
            # Outside request context (e.g. CLI or background)
            pass

        data = session.get("student_state") if self._has_session() else None
        if not data:
            return None
        return StudentState.from_dict(data)

    def save(self, student: StudentState) -> None:
        try:
            user_id = session.get("user_id")
            if user_id:
                from core.database import save_student_state_by_user_id
                save_student_state_by_user_id(user_id, student)
        except RuntimeError:
            pass

        if self._has_session():
            session["student_state"] = student.to_dict()
            session["student_id"] = student.student_id
            session.modified = True

    def reset(self, student_id: str = "current") -> StudentState:
        new_student = StudentState()
        try:
            user_id = session.get("user_id")
            if user_id:
                from core.database import save_student_state_by_user_id, get_user_by_id
                u = get_user_by_id(user_id)
                if u:
                    new_student.profile.name = u["full_name"]
                save_student_state_by_user_id(user_id, new_student)
        except RuntimeError:
            pass

        if self._has_session():
            session["student_state"] = new_student.to_dict()
            session["student_id"] = new_student.student_id
            session.modified = True
        return new_student

    def _has_session(self) -> bool:
        try:
            return bool(session is not None)
        except RuntimeError:
            return False


class JsonDataRepository(DataRepository):
    """
    In-memory cached repository reading canonical JSON files in data/
    """
    _cache: Dict[str, Any] = {}

    def _load_json(self, filename: str, default: Any) -> Any:
        if filename in self._cache:
            return self._cache[filename]
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            return default
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default

    def get_careers(self) -> Dict[str, Any]:
        return self._load_json("careers.json", {})

    def get_skills(self) -> Dict[str, Any]:
        return self._load_json("skills.json", {})

    def get_resources(self) -> List[Dict[str, Any]]:
        return self._load_json("resources.json", [])

    def get_projects(self) -> List[Dict[str, Any]]:
        return self._load_json("projects.json", [])

    def get_certifications(self) -> List[Dict[str, Any]]:
        return self._load_json("certifications.json", [])

    def get_question_bank(self) -> Dict[str, Any]:
        return self._load_json("question_bank.json", {})

    def get_rubrics(self) -> Dict[str, Any]:
        return self._load_json("rubrics.json", {})

    def clear_cache(self):
        self._cache.clear()


# Global singletons
student_repo = SessionStudentRepository()
data_repo = JsonDataRepository()
