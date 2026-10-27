"""
Non-fatal notices the API attaches to search, answer and DeepResearch
responses, for example datasets that were skipped because the plan doesn't
include them::

    {
        "type": "datasets_not_in_plan",
        "message": "Your Pay-as-you-go plan doesn't include ...",
        "detail": {"upgrade_url": "https://platform.valyu.ai/user/account/billing?tab=plan"}
    }

``type`` is an open set: new values can appear at any time. Older responses
send plain strings instead; each becomes ``ResponseWarning(type="warning",
message=<string>)``. A malformed entry is dropped rather than failing the
response.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, BeforeValidator, ValidationError
from typing_extensions import Annotated


class ResponseWarning(BaseModel):
    """A non-fatal notice about the request."""

    type: str
    message: str
    detail: Optional[Dict[str, Any]] = None


def _parse_warnings(value: Any) -> Optional[List[ResponseWarning]]:
    if not isinstance(value, list):
        return None
    warnings = []
    for item in value:
        if isinstance(item, str):
            item = {"type": "warning", "message": item}
        try:
            warnings.append(ResponseWarning.model_validate(item))
        except ValidationError:
            continue
    return warnings


ResponseWarnings = Annotated[
    Optional[List[ResponseWarning]], BeforeValidator(_parse_warnings)
]
