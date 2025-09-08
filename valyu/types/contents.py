from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel

ExtractEffort = Literal["normal", "high", "auto"]
ContentsResponseLength = Union[Literal["short", "medium", "large", "max"], int]


class ContentsResult(BaseModel):
    url: str
    title: str
    content: Union[str, int, float]
    length: int
    source: str
    summary: Optional[Union[str, Dict[str, Any]]] = None
    summary_success: Optional[bool] = None
    data_type: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None
    citation: Optional[str] = None


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

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)
