def require_nonempty(fields: dict[str, str]) -> str | None:
    """Return first missing field message or None."""
    for key, value in fields.items():
        if not (value or "").strip():
            return "필수값을 입력하세요"
    return None
