"""
Resource Library Validator & Integrity Checker
----------------------------------------------
Validates schema compliance, checks duplicate IDs, confirms required fields,
and optionally verifies URL reachability via HTTP GET/HEAD requests.
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "resources.json")

REQUIRED_FIELDS = [
    "id", "title", "category", "skill_ids", "description",
    "level", "cost", "type", "url", "recommended_for",
    "estimated_time_minutes", "difficulty", "source_type",
    "language", "source", "last_verified", "tags"
]

VALID_COSTS = {"free", "freemium", "paid"}
VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}
VALID_SOURCE_TYPES = {"official", "community", "university", "platform"}


def validate_resources(check_network: bool = False) -> bool:
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found.")
        return False

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        resources = json.load(f)

    seen_ids = set()
    errors = []
    updated = False

    for idx, item in enumerate(resources):
        r_id = item.get("id")
        if not r_id:
            errors.append(f"Resource #{idx} is missing an 'id'.")
            continue

        if r_id in seen_ids:
            errors.append(f"Duplicate resource ID detected: {r_id}")
        seen_ids.add(r_id)

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"Resource '{r_id}' missing required field: '{field}'")

        # Check enum values
        if item.get("cost") not in VALID_COSTS:
            errors.append(f"Resource '{r_id}' invalid cost '{item.get('cost')}'")
        if item.get("level") not in VALID_LEVELS:
            errors.append(f"Resource '{r_id}' invalid level '{item.get('level')}'")
        if item.get("source_type") not in VALID_SOURCE_TYPES:
            errors.append(f"Resource '{r_id}' invalid source_type '{item.get('source_type')}'")

        # Optional network reachability check
        if check_network and item.get("url"):
            try:
                import urllib.request
                req = urllib.request.Request(
                    item["url"],
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status in (200, 301, 302):
                        item["last_verified"] = datetime.now(timezone.utc).isoformat()
                        updated = True
            except Exception as e:
                print(f"Network warning: Could not reach {item['url']}: {e}")

    if updated:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(resources, f, indent=2)
        print("Updated last_verified dates for reachable URLs.")

    if errors:
        print(f"FAILED: Found {len(errors)} validation errors:")
        for err in errors:
            print(f" - {err}")
        return False

    print(f"SUCCESS: Validated {len(resources)} resources. Schema and integrity verified.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate resource schema and URLs")
    parser.add_argument("--check-network", action="store_true", help="Perform live HTTP reachability checks")
    args = parser.parse_args()

    success = validate_resources(check_network=args.check_network)
    sys.exit(0 if success else 1)
