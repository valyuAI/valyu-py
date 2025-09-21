"""
Pydantic schemas for the /answer endpoint (Valyu Answer Lambda).

These models describe the public request/response contract for the endpoint
based on the implemented validation in `query/validator.py` and the response
shape produced by `ai/groq_tool_agent.py`.

Note: The Answer Lambda runs behind API Gateway (not FastAPI), but these
schemas are useful for documentation, typing, and validation in tests/tools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from datetime import date
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator


# --------------------------
# Request Schema
# --------------------------

SUPPORTED_COUNTRY_CODES = {
    "ALL",
    "AR",
    "AU",
    "AT",
    "BE",
    "BR",
    "CA",
    "CL",
    "DK",
    "FI",
    "FR",
    "DE",
    "HK",
    "IN",
    "ID",
    "IT",
    "JP",
    "KR",
    "MY",
    "MX",
    "NL",
    "NZ",
    "NO",
    "CN",
    "PL",
    "PT",
    "PH",
    "RU",
    "SA",
    "ZA",
    "ES",
    "SE",
    "CH",
    "TW",
    "TR",
    "GB",
    "US",
}


_DOMAIN_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)
_URL_RE = re.compile(
    r"^https?://[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*(:[0-9]{1,5})?(/.*)?$"
)


class AnswerRequest(BaseModel):
    """Request body schema for POST /answer.

    This mirrors validation behavior in `query/validator.py`.
    """

    model_config = ConfigDict(extra="forbid")

    # AI-specific
    structured_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema object. When provided, the response 'contents' is structured to this schema.",
    )
    system_instructions: Optional[str] = Field(
        default=None,
        description="Custom system-level instructions (<= 2000 chars).",
        max_length=2000,
    )

    # Search parameters
    query: str = Field(description="Search query text.")
    search_type: Literal["all", "web", "proprietary"] = Field(
        default="all", description="Search scope selector."
    )
    data_max_price: float = Field(
        default=30.0,
        gt=0,
        description="Maximum spend (USD) for data retrieval. Separate from AI costs.",
    )
    fast_mode: bool = Field(
        default=False,
        description="Enable fast mode for faster but shorter results. Good for general purpose queries.",
    )
    country_code: Optional[str] = Field(
        default=None, description="2-letter ISO code or 'ALL'."
    )
    included_sources: List[str] = Field(
        default_factory=list,
        description="Domains or URLs to include (e.g., 'example.com' or 'https://example.com').",
    )
    excluded_sources: List[str] = Field(
        default_factory=list,
        description="Domains or URLs to exclude (e.g., 'example.com' or 'https://example.com').",
    )
    start_date: Optional[date] = Field(
        default=None, description="Start date filter (YYYY-MM-DD)."
    )
    end_date: Optional[date] = Field(
        default=None, description="End date filter (YYYY-MM-DD)."
    )

    @field_validator("system_instructions")
    @classmethod
    def _non_empty_when_present(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        s = v.strip()
        if not s:
            raise ValueError("system_instructions cannot be empty when provided")
        return s

    @field_validator("country_code")
    @classmethod
    def _validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_up = v.strip().upper()
        if v_up not in SUPPORTED_COUNTRY_CODES:
            raise ValueError(
                "Invalid country_code. Must be a supported 2-letter ISO code or 'ALL'."
            )
        return v_up

    @staticmethod
    def _validate_domain_or_url_list(values: List[str], field_name: str) -> List[str]:
        cleaned: List[str] = []
        for i, raw in enumerate(values or []):
            if not isinstance(raw, str):
                raise ValueError(f"{field_name}[{i}] must be a string")
            s = raw.strip()
            if not s:
                continue
            if not (_DOMAIN_RE.match(s) or _URL_RE.match(s)):
                raise ValueError(
                    f"{field_name}[{i}] must be a valid domain (e.g., 'example.com') or URL (e.g., 'https://example.com')"
                )
            cleaned.append(s)
        return cleaned

    @field_validator("included_sources")
    @classmethod
    def _validate_included_sources(cls, v: List[str]) -> List[str]:
        return cls._validate_domain_or_url_list(v, "included_sources")

    @field_validator("excluded_sources")
    @classmethod
    def _validate_excluded_sources(cls, v: List[str]) -> List[str]:
        return cls._validate_domain_or_url_list(v, "excluded_sources")

    @field_validator("end_date")
    @classmethod
    def _validate_date_order(
        cls, end: Optional[date], info
    ) -> Optional[date]:  # type: ignore[override]
        # Pydantic v2 passes ValidationInfo via 'info'; we need both values present
        start: Optional[date] = info.data.get("start_date")  # type: ignore[attr-defined]
        if start and end and start > end:
            raise ValueError("start_date must be before end_date")
        return end


# --------------------------
# Response Schema
# --------------------------


class SearchMetadata(BaseModel):
    tx_ids: List[str] = Field(
        default_factory=list,
        description="List of transaction ids for the search operations.",
    )
    number_of_results: int = Field(
        default=0, description="Number of search results returned."
    )
    total_characters: int = Field(
        default=0, description="Total characters across fetched content."
    )


class AIUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class CostBreakdown(BaseModel):
    total_deduction_dollars: float = Field(
        description="Total combined cost in dollars."
    )
    search_deduction_dollars: float = Field(
        description="Cost of data retrieval in dollars."
    )
    ai_deduction_dollars: float = Field(description="AI processing cost in dollars.")


class SearchResult(BaseModel):
    title: str
    url: str
    content: Union[str, List[Dict[str, Any]]]
    description: Optional[str] = None
    source: str
    price: float
    length: int
    image_url: Optional[Dict[str, str]] = None
    relevance_score: float
    data_type: Optional[Literal["structured", "unstructured"]] = None


class AnswerSuccessResponse(BaseModel):
    success: Literal[True] = True
    ai_tx_id: str
    original_query: str
    contents: Union[str, Dict[str, Any]]
    data_type: Literal["structured", "unstructured"]
    search_results: List[SearchResult] = Field(default_factory=list)
    search_metadata: SearchMetadata
    ai_usage: AIUsage
    cost: CostBreakdown

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


class AnswerErrorResponse(BaseModel):
    success: Literal[False] = False
    error: str

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


# Public union type for convenience
AnswerResponse = Union[AnswerSuccessResponse, AnswerErrorResponse]


__all__ = [
    "AnswerRequest",
    "SearchMetadata",
    "AIUsage",
    "CostBreakdown",
    "AnswerSuccessResponse",
    "AnswerErrorResponse",
    "AnswerResponse",
    "SUPPORTED_COUNTRY_CODES",
]
