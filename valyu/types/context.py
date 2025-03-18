from typing import List, Optional, Literal
from pydantic import BaseModel

SearchType = Literal["web", "proprietary", "all"]


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    description: Optional[str] = None
    source: str
    price: float
    length: int
    relevance_score: float
    data_type: Optional[Literal["structured", "unstructured"]] = (
        None  # structured means content is json as str
    )


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
    total_deduction_pcm: float
    total_deduction_dollars: float
    total_characters: int

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)
