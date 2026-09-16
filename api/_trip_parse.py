import json
import re


def strip_code_fence(text: str) -> str:
    s = (text or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*\n?", "", s, count=1, flags=re.IGNORECASE)
        s = re.sub(r"\n?```\s*$", "", s, count=1)
    return s.strip()


def parse_primary_json(text: str) -> dict:
    raw = strip_code_fence(text)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("primary must be an object")
    required = ("recommended_site", "nearby_area", "reason", "learning_goals", "field_missions")
    for key in required:
        if key not in data:
            raise ValueError(f"missing {key}")
    if not isinstance(data["learning_goals"], list) or not isinstance(data["field_missions"], list):
        raise ValueError("learning_goals and field_missions must be lists")
    return {
        "recommended_site": str(data["recommended_site"]).strip(),
        "nearby_area": str(data["nearby_area"]).strip(),
        "reason": str(data["reason"]).strip(),
        "learning_goals": [str(x).strip() for x in data["learning_goals"]],
        "field_missions": [str(x).strip() for x in data["field_missions"]],
    }
