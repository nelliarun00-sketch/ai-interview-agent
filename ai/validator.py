"""
AI Output Validator & Anti-Hallucination Filter
-----------------------------------------------
Extracts, parses, and validates structured JSON from LLM responses.
Enforces schema requirements and discards fabricated resource IDs.
"""

import json
import re
import logging
from typing import Dict, Any, Tuple, Optional, Set, Callable

logger = logging.getLogger("ai_validator")


def clean_json_string(raw_text: str) -> str:
    """Strips markdown code fences, comments, and control characters."""
    if not raw_text:
        return ""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def validate_schema(data: dict, schema: dict) -> Tuple[bool, Optional[str]]:
    """Lightweight schema validator checking required fields and types."""
    if not isinstance(data, dict):
        return False, "Output must be a JSON object"

    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            return False, f"Missing required property: {field}"

    props = schema.get("properties", {})
    for key, spec in props.items():
        if key in data and data[key] is not None:
            expected_type = spec.get("type")
            val = data[key]
            if expected_type == "integer" and not isinstance(val, int):
                # Try soft coercion
                try:
                    data[key] = int(val)
                except (ValueError, TypeError):
                    return False, f"Property '{key}' must be an integer"
            elif expected_type == "number" and not isinstance(val, (int, float)):
                try:
                    data[key] = float(val)
                except (ValueError, TypeError):
                    return False, f"Property '{key}' must be a number"
            elif expected_type == "array" and not isinstance(val, list):
                return False, f"Property '{key}' must be a list"
            elif expected_type == "string" and not isinstance(val, str):
                data[key] = str(val)

            # Clamp integer ranges if specified
            if "minimum" in spec and isinstance(data[key], (int, float)):
                data[key] = max(spec["minimum"], data[key])
            if "maximum" in spec and isinstance(data[key], (int, float)):
                data[key] = min(spec["maximum"], data[key])

    return True, None


def sanitize_resource_ids(cited_ids: list, allowed_ids: Set[str]) -> list:
    """Anti-hallucination filter: drops any resource_id not present in canonical library."""
    if not cited_ids:
        return []
    return [r_id for r_id in cited_ids if isinstance(r_id, str) and r_id in allowed_ids]


def parse_and_validate(
    raw_text: Optional[str],
    schema: dict,
    fallback_fn: Callable[[], dict],
    allowed_resource_ids: Optional[Set[str]] = None
) -> Tuple[dict, str, Optional[str]]:
    """
    Parses raw LLM text, validates against schema, applies anti-hallucination filters,
    or falls back to a deterministic generator.
    Returns: (validated_data, source ['ai'|'fallback'], error_message)
    """
    if not raw_text:
        return fallback_fn(), "fallback", "Empty response from AI"

    cleaned = clean_json_string(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        logger.warning(f"JSON decode failed on AI output: {err}. Using deterministic fallback.")
        return fallback_fn(), "fallback", f"JSON Parse Error: {str(err)}"

    valid, err_msg = validate_schema(data, schema)
    if not valid:
        logger.warning(f"Schema validation error: {err_msg}. Using fallback.")
        return fallback_fn(), "fallback", f"Schema Error: {err_msg}"

    # Filter any cited resource IDs
    if allowed_resource_ids is not None:
        if "cited_resource_ids" in data:
            data["cited_resource_ids"] = sanitize_resource_ids(data["cited_resource_ids"], allowed_resource_ids)
        if "recommended_resource_ids" in data:
            data["recommended_resource_ids"] = sanitize_resource_ids(data["recommended_resource_ids"], allowed_resource_ids)

    return data, "ai", None
