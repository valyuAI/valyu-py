from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel

SearchType = Literal["web", "proprietary", "all", "news"]
# Per-request strictness for a historical_cache (point-in-time backtest) search.
#   "off"    - no point-in-time guarantee; serve whatever is freshest.
#   "prefer" - serve an in-window snapshot when one exists, else fall back to a
#              LIVE crawl so the query is never empty (the API default).
#   "only"   - serve ONLY content provably captured at or before end_date; drop a
#              result rather than fall back to live. Use for strict backtests.
HistoricalCacheStrict = Literal["off", "prefer", "only"]


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


class SearchResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    tx_id: str
    query: str
    results: List[SearchResult]
    results_by_source: ResultsBySource
    total_deduction_dollars: float
    total_characters: int

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)
