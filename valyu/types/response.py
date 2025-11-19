from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel

SearchType = Literal["web", "proprietary", "all", "news"]


class SearchResult(BaseModel):
    title: str
    url: str
    content: Union[str, List[Dict[str, Any]]]
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
