"""
Shared error-message formatting for Valyu API responses.
"""

from typing import Any, Dict


def error_message(data: Dict[str, Any], status_code: int) -> str:
    """
    Build a human-readable error string from an API error body.

    Validation failures carry an `errors` array naming each offending field, so
    fold those into the message. Without them a caller only sees a summary like
    "2 validation errors", which says nothing about which parameter was wrong or
    what the API expected instead.

    Args:
        data: Parsed JSON error body
        status_code: HTTP status code, used when the body carries no message

    Returns:
        The error message, suffixed with per-field detail when available
    """
    if not isinstance(data, dict):
        return f"HTTP Error: {status_code}"

    summary = data.get("message") or data.get("error") or f"HTTP Error: {status_code}"

    details = []
    for item in data.get("errors") or []:
        if isinstance(item, dict):
            detail = item.get("message") or item.get("code")
            key = item.get("key")
            if detail and key and key not in str(detail):
                detail = f"{key}: {detail}"
        else:
            detail = item
        if detail:
            details.append(str(detail))

    if not details:
        return str(summary)

    return f"{summary}: {'; '.join(details)}"
