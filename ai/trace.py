"""
AI Explainability & Trace Recorder
----------------------------------
Records every decision, prompt version, input parameters, raw response,
validation status, and latency.
Powers the live "AI Trace" inspector panel for professors and evaluators.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid

class AITraceRecorder:
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._traces: List[Dict[str, Any]] = []

    def record(
        self,
        operation: str,
        prompt_version: str,
        inputs: Dict[str, Any],
        raw_output: str,
        validated_output: Any,
        latency_ms: float,
        source: str = "ai",
        error: str = None
    ) -> str:
        trace_id = str(uuid.uuid4())[:8]
        record = {
            "id": trace_id,
            "operation": operation,
            "prompt_version": prompt_version,
            "inputs": inputs,
            "raw_output": raw_output,
            "validated_output": validated_output,
            "latency_ms": round(latency_ms, 2),
            "source": source,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._traces.insert(0, record)
        if len(self._traces) > self.max_history:
            self._traces = self._traces[:self.max_history]
        return trace_id

    def list_traces(self) -> List[Dict[str, Any]]:
        return self._traces

    def clear(self) -> None:
        self._traces.clear()

ai_trace = AITraceRecorder()
