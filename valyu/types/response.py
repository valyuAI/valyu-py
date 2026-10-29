from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field

from valyu.types.rate_limit import RateLimitDetail
from valyu.types.warning import ResponseWarnings

SearchType = Literal["web", "proprietary", "all", "news"]
# Per-request strictness for a historical_cache (point-in-time backtest) search.
#   "off"    - no point-in-time guarantee; serve whatever is freshest.
#   "prefer" - serve an in-window snapshot when one exists, else fall back to a
#              LIVE crawl so the query is never empty (the API default).
#   "only"   - serve ONLY content provably captured at or before end_date; drop a
#              result rather than fall back to live. Use for strict backtests.
HistoricalCacheStrict = Literal["off", "prefer", "only"]
# How included_sources is applied. "advisory" (API default) guides source
# selection; "strict" searches exactly the datasets in included_sources.
ScopePolicy = Literal["advisory", "strict"]
# Wiley HLS coverage: "hls" is licensed Wiley content only; "increased_coverage"
# blends it with open-access biomedical literature.
HlsCoverage = Literal["hls", "increased_coverage"]


class SearchResult(BaseModel):
    title: str
    url: str
    content: Union[str, List[Dict[str, Any]], Dict[str, Any]]
    description: Optional[str] = None
    source: str
    price: float
    length: int
    image_url: Optional[Dict[str, str]] = None
    relevance_score: Optional[float] = None
    data_type: Optional[Literal["structured", "unstructured"]] = None
    source_type: Optional[str] = None
    publication_date: Optional[str] = None
    # When the page was crawled (web results).
    crawl_date: Optional[str] = None
    id: Optional[str] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    citation: Optional[str] = None
    citation_count: Optional[int] = None
    authors: Optional[List[str]] = None
    references: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResultsBySource(BaseModel):
    web: int
    proprietary: int


class SourceScope(BaseModel):
    """Receipt for a ``scope_policy="strict"`` search.

    Shows which datasets were dispatched and which returned rows. It does not
    certify full coverage.
    """

    policy: Optional[str] = None
    allowed_dataset_ids: Optional[List[str]] = None
    selected_dataset_ids: Optional[List[str]] = None
    completed_dataset_ids: Optional[List[str]] = None
    returned_dataset_ids: Optional[List[str]] = None
    omitted_dataset_ids: Optional[List[str]] = None
    selection_basis: Optional[str] = None
    coverage: Optional[str] = None
    exhaustive: Optional[bool] = None
    errors: Optional[List[Dict[str, Any]]] = None


class SearchResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    tx_id: str
    query: str
    results: List[SearchResult]
    results_by_source: ResultsBySource
    total_deduction_dollars: float
    total_characters: int
    rate_limit: Optional[RateLimitDetail] = Field(
        default=None,
        description="Structured detail when `error` is caused by HTTP 429 (rate limited). None otherwise.",
    )
    warnings: ResponseWarnings = None
    # Present only for scope_policy="strict" requests.
    source_scope: Optional[SourceScope] = None

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)
