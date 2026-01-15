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


class DatasourcesResponse(BaseModel):
  """Response from the datasources list endpoint."""
  success: bool
  error: Optional[str] = None
  datasources: List[Datasource] = []

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
