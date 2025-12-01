"""
Pydantic schemas for the /answer endpoint (Valyu Answer API).

These models describe the public request/response contract for the endpoint.
Supports both streaming (SSE) and non-streaming modes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union, Generator
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
    search_type: Literal["all", "web", "proprietary", "news"] = Field(
        default="all", description="Search scope selector."
    )
    data_max_price: float = Field(
        default=1.0,
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
        description="Domains, URLs, dataset identifiers, or presets to include.",
    )
    excluded_sources: List[str] = Field(
        default_factory=list,
        description="Domains, URLs, or dataset identifiers to exclude.",
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
        start: Optional[date] = info.data.get("start_date")
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
    contents_deduction_dollars: float = Field(
        default=0.0, description="Cost of content extraction in dollars."
    )


class ExtractionMetadata(BaseModel):
    """Metadata about content extraction, only populated when contents_api tool was used."""

    urls_requested: int = Field(default=0, description="Number of URLs requested for extraction.")
    urls_processed: int = Field(default=0, description="Number of URLs successfully processed.")
    urls_failed: int = Field(default=0, description="Number of URLs that failed extraction.")
    total_characters: int = Field(default=0, description="Total characters extracted.")
    response_length: Optional[str] = Field(default=None, description="Response length setting used.")
    extract_effort: Optional[str] = Field(default=None, description="Extraction effort level used.")


class SearchResult(BaseModel):
    """Search result from the Answer API.

    Note: `content` can be a string for text content, or a list/dict for structured
    data (e.g., stock prices, financial data).
    """
    title: str
    url: str
    content: Union[str, List[Dict[str, Any]], Dict[str, Any]]
    description: Optional[str] = None
    source: str
    source_type: Optional[str] = Field(
        default=None, description="Type of source: 'website', 'data', 'forum'"
    )
    data_type: Optional[Literal["structured", "unstructured"]] = None
    date: Optional[str] = Field(
        default=None, description="Publication date in YYYY-MM-DD format"
    )
    length: int
    image_url: Optional[Dict[str, str]] = None
    relevance_score: Optional[float] = None


class AnswerSuccessResponse(BaseModel):
    success: Literal[True] = True
    tx_id: str = Field(description="The AI transaction ID for this request.")
    original_query: str
    contents: Union[str, Dict[str, Any]]
    data_type: Literal["structured", "unstructured"]
    search_results: List[SearchResult] = Field(default_factory=list)
    search_metadata: SearchMetadata
    ai_usage: AIUsage
    cost: CostBreakdown
    extraction_metadata: Optional[ExtractionMetadata] = Field(
        default=None,
        description="Metadata about content extraction, only populated when contents_api tool was used.",
    )

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


class AnswerErrorResponse(BaseModel):
    success: Literal[False] = False
    error: str

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


# Public union type for convenience
AnswerResponse = Union[AnswerSuccessResponse, AnswerErrorResponse]


# --------------------------
# Streaming Types
# --------------------------


class AnswerStreamChunk(BaseModel):
    """A chunk from the streaming response."""

    type: Literal["search_results", "content", "metadata", "done", "error"]

    # For type="search_results"
    search_results: Optional[List[SearchResult]] = None

    # For type="content"
    content: Optional[str] = None
    finish_reason: Optional[str] = None

    # For type="metadata" (final metadata after streaming completes)
    tx_id: Optional[str] = None
    original_query: Optional[str] = None
    data_type: Optional[Literal["structured", "unstructured"]] = None
    search_metadata: Optional[SearchMetadata] = None
    ai_usage: Optional[AIUsage] = None
    cost: Optional[CostBreakdown] = None
    extraction_metadata: Optional[ExtractionMetadata] = None

    # For type="error"
    error: Optional[str] = None


# Type alias for streaming generator
AnswerStreamGenerator = Generator[AnswerStreamChunk, None, None]


__all__ = [
    "AnswerRequest",
    "SearchMetadata",
    "AIUsage",
    "CostBreakdown",
    "ExtractionMetadata",
    "SearchResult",
    "AnswerSuccessResponse",
    "AnswerErrorResponse",
    "AnswerResponse",
    "AnswerStreamChunk",
    "AnswerStreamGenerator",
    "SUPPORTED_COUNTRY_CODES",
]
