from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from valyu.types.rate_limit import RateLimitDetail

ExtractEffort = Literal["normal", "high", "auto"]
ContentsResponseLength = Union[Literal["short", "medium", "large", "max"], int]
# "miss": crawled for this request. "hit": a fresh cached copy. "stale": a cached
# copy older than 5 minutes served while it refreshes (only with max_age omitted).
CacheState = Literal["hit", "miss", "stale"]


def _normalize_result(raw: Any) -> Any:
    """Add default status for backward compat when API omits it."""
    if isinstance(raw, dict) and "status" not in raw:
        raw = dict(raw)
        if "title" in raw and "content" in raw:
            raw["status"] = "success"
        else:
            raw["status"] = "failed"
            raw.setdefault("error", "Unknown error")
    return raw


class ContentsResultSuccess(BaseModel):
    """Successful content extraction result."""

    model_config = ConfigDict(extra="ignore")

    url: str
    status: Literal["success"]
    title: str
    content: Union[str, int, float]
    length: int
    source: str
    source_type: Optional[str] = None
    screenshot_url: Optional[str] = None
    summary: Optional[Union[str, Dict[str, Any]]] = None
    publication_date: Optional[str] = None
    # Optional fields API may still return
    description: Optional[str] = None
    price: Optional[float] = None
    summary_success: Optional[bool] = None
    data_type: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None
    citation: Optional[str] = None
    cache_state: Optional[CacheState] = None
    # ISO 8601 capture time of the page copy; None when there is no page copy
    # to date (for example a paper served from the index).
    crawled_at: Optional[str] = None
    # 404 when the page returned 404 but its body is a real page. None for a
    # normal page.
    http_status: Optional[int] = None
    # Identifier: the URL for web pages, the bare paper id / DOI for papers.
    id: Optional[str] = None
    # Metadata from structured extraction; only when data_type is "structured".
    structured_metadata: Optional[Dict[str, Any]] = None
    # Academic papers served from the processed index.
    doi: Optional[str] = None
    authors: Optional[List[str]] = None
    citation_count: Optional[int] = None


class ContentsResultFailed(BaseModel):
    """Result for a URL that was not extracted.

    ``status`` is ``"failed"``, or ``"not_found"`` when the page returned 404.
    """

    model_config = ConfigDict(extra="ignore")

    url: str
    status: Literal["failed", "not_found"]
    error: str


ContentsResult = Union[ContentsResultSuccess, ContentsResultFailed]


class ContentsJobCreateResponse(BaseModel):
    """Response when creating an async contents job (202 Accepted)."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    job_id: str
    status: Literal["pending"]
    urls_total: int
    poll_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    tx_id: Optional[str] = None


class ContentsJobStatus(BaseModel):
    """Status of an async contents job."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    job_id: str
    status: Literal["pending", "processing", "completed", "partial", "failed"]
    urls_total: int
    urls_processed: int
    urls_failed: int
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    current_batch: Optional[int] = None
    total_batches: Optional[int] = None
    results: Optional[List[ContentsResult]] = None
    actual_cost_dollars: Optional[float] = None
    error: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_results(cls, data: Any) -> Any:
        if isinstance(data, dict) and "results" in data and data["results"]:
            data = dict(data)
            data["results"] = [_normalize_result(r) for r in data["results"]]
        return data


class ContentsResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    tx_id: str
    urls_requested: int
    urls_processed: int
    urls_failed: int
    results: List[ContentsResult]
    total_cost_dollars: float
    total_characters: int
    rate_limit: Optional[RateLimitDetail] = Field(
        default=None,
        description="Structured detail when `error` is caused by HTTP 429 (rate limited). None otherwise.",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_results(cls, data: Any) -> Any:
        if isinstance(data, dict) and "results" in data:
            data = dict(data)
            data["results"] = [_normalize_result(r) for r in data["results"]]
        return data

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)
