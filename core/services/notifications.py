"""
Notification Dispatcher Service
-------------------------------
Dispatches structured alerts, spaced retrieval reminders, and adaptive notices.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List
from core.models import StudentState


def add_notification(
    student: StudentState,
    title: str,
    message: str,
    type_: str = "info"
) -> Dict[str, Any]:
    """Adds a real notification to student state feed."""
    notif = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "message": message,
        "type": type_, # info, alert, success, adaptive
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False
    }
    student.notifications.insert(0, notif)
    # Cap notification log
    if len(student.notifications) > 25:
        student.notifications = student.notifications[:25]
    return notif
