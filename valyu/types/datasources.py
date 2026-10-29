from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel


class DatasourcePricing(BaseModel):
    """Pricing information for a datasource."""
    cpm: float  # Cost per million tokens


class DatasourceCoverage(BaseModel):
    """Coverage information for a datasource."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Datasource(BaseModel):
    """A single datasource available in Valyu."""
    id: str
    name: str
    description: str
    category: str
    type: Optional[str] = None
    modality: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    source: Optional[str] = None
    example_queries: Optional[List[str]] = None
    pricing: Optional[DatasourcePricing] = None
    response_schema: Optional[Dict[str, Any]] = None
    update_frequency: Optional[str] = None
    size: Optional[int] = None
    coverage: Optional[DatasourceCoverage] = None
    # Cheapest plan that includes this dataset ({"id", "name", "price"}); None
    # when the dataset is licensed separately.
    required_plan: Optional[Dict[str, Any]] = None
    # Products the dataset can be used in: "search", "answer", "deepresearch".
    access_modes: Optional[List[str]] = None
    geography: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    # Data provider information ({"provider", "license"}).
    data_source: Optional[Dict[str, Any]] = None


class DatasourcesResponse(BaseModel):
    """Response from the datasources list endpoint."""
    success: bool
    error: Optional[str] = None
    datasources: List[Datasource] = []
    total_count: Optional[int] = None

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


class DatasourceSearchResult(Datasource):
    """A datasource ranked by ``datasources_search()``."""
    relevance_score: Optional[float] = None


class DatasourceSearchResponse(BaseModel):
    """Response from the semantic datasource search endpoint."""
    success: bool
    error: Optional[str] = None
    query: Optional[str] = None
    # "semantic" (embedding ranking) or "lexical" (full-text fallback).
    search_mode: Optional[str] = None
    total_count: Optional[int] = None
    results: List[DatasourceSearchResult] = []

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


class DatasourceCategory(BaseModel):
    """A category of datasources."""
    id: str
    name: str
    description: Optional[str] = None
    dataset_count: int


class DatasourceCategoriesResponse(BaseModel):
    """Response from the datasources categories endpoint."""
    success: bool
    error: Optional[str] = None
    categories: List[DatasourceCategory] = []

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)


# Valid category values
DatasourceCategoryType = Literal[
    "research",
    "healthcare",
    "markets",
    "company",
    "economic",
    "predictions",
    "transportation",
    "legal",
    "politics",
    "patents",
]
