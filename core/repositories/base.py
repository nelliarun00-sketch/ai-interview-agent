"""
Abstract Repository Interfaces
------------------------------
Defines strict contracts for data access.
Enables swapping Flask-Session for SQLite / PostgreSQL without modifying business services.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from core.models import StudentState


class StudentRepository(ABC):
    @abstractmethod
    def get(self, student_id: str) -> Optional[StudentState]:
        """Fetch student state by UUID."""
        pass

    @abstractmethod
    def save(self, student: StudentState) -> None:
        """Persist updated student state."""
        pass

    @abstractmethod
    def reset(self, student_id: str) -> StudentState:
        """Clear data and reinitialize empty student state."""
        pass


class DataRepository(ABC):
    @abstractmethod
    def get_careers(self) -> Dict[str, Any]:
        """Load career definitions."""
        pass

    @abstractmethod
    def get_skills(self) -> Dict[str, Any]:
        """Load skills knowledge graph."""
        pass

    @abstractmethod
    def get_resources(self) -> List[Dict[str, Any]]:
        """Load verified learning resources."""
        pass

    @abstractmethod
    def get_projects(self) -> List[Dict[str, Any]]:
        """Load project recommendations."""
        pass

    @abstractmethod
    def get_certifications(self) -> List[Dict[str, Any]]:
        """Load certifications & course references."""
        pass

    @abstractmethod
    def get_question_bank(self) -> Dict[str, Any]:
        """Load seed interview questions."""
        pass

    @abstractmethod
    def get_rubrics(self) -> Dict[str, Any]:
        """Load assessment and evaluation rubrics."""
        pass
