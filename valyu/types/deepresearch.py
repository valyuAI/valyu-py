from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List, Literal, Union, Dict, Any, Callable
from enum import Enum


class DeepResearchMode(str, Enum):
    """Research mode options."""

    FAST = "fast"
    STANDARD = "standard"
    LITE = "lite"  # Deprecated: use STANDARD instead (kept for backward compatibility)
    HEAVY = "heavy"


class DeepResearchStatus(str, Enum):
    """Task status options."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileAttachment(BaseModel):
    """File attachment for research."""

    model_config = ConfigDict(populate_by_name=True)

    data: str = Field(..., description="Data URL (base64 encoded)")
    filename: str = Field(..., description="Original filename")
    media_type: str = Field(..., description="MIME type", alias="mediaType")
    context: Optional[str] = Field(None, description="Context about the file")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    url: str = Field(..., description="MCP server URL")
    name: Optional[str] = Field(None, description="Server name")
    tool_prefix: Optional[str] = Field(None, description="Custom tool prefix")
    auth: Optional[Dict[str, Any]] = Field(None, description="Authentication config")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tools")


class Deliverable(BaseModel):
    """Deliverable file configuration."""

    type: Literal["csv", "xlsx", "pptx", "docx", "pdf"] = Field(
        ..., description="File type"
    )
    description: str = Field(
        ..., max_length=500, description="What data to extract or content to generate"
    )
    columns: Optional[List[str]] = Field(
        None, description="Suggested column names (for CSV/XLSX)"
    )
    include_headers: Optional[bool] = Field(
        True, description="Include column headers (for CSV/XLSX)"
    )
    sheet_name: Optional[str] = Field(None, description="Sheet name (for XLSX only)")
    slides: Optional[int] = Field(None, description="Number of slides (for PPTX only)")
    template: Optional[str] = Field(None, description="Template name to use")


class DeliverableResult(BaseModel):
    """Deliverable generation result."""

    id: str = Field(..., description="Unique deliverable ID")
    request: str = Field(..., description="Original request description")
    type: Literal["csv", "xlsx", "pptx", "docx", "pdf", "unknown"] = Field(
        ..., description="Deliverable file type"
    )
    status: Literal["completed", "failed"] = Field(..., description="Generation status")
    title: str = Field(..., description="Generated filename/title")
    description: Optional[str] = Field(
        None, description="Deliverable content description"
    )
    url: str = Field(
        ..., description="Token-signed authenticated URL to download the file"
    )
    s3_key: str = Field(..., description="S3 storage key")
    row_count: Optional[int] = Field(None, description="Number of rows (for CSV/XLSX)")
    column_count: Optional[int] = Field(
        None, description="Number of columns (for CSV/XLSX)"
    )
    error: Optional[str] = Field(None, description="Error message if status is failed")
    created_at: int = Field(..., description="Unix timestamp of creation")


class SearchConfig(BaseModel):
    """Search configuration for Deep Research tasks and batches.

    Controls which data sources are queried, what content is included/excluded,
    and how results are filtered by date or category.

    Attributes:
        search_type: Controls which backend search systems are queried.
            - "all" (default): Searches both web and proprietary data sources
            - "web": Searches only web sources (general web search, news, articles)
            - "proprietary": Searches only proprietary/internal data sources
        included_sources: Restricts search to only the specified source types.
            Available types: "web", "academic", "finance", "patent",
            "transportation", "politics", "legal"
        excluded_sources: Excludes specific source types from search results.
            Uses the same source type values as included_sources.
            Cannot be used simultaneously with included_sources.
        start_date: Filters results to content published on or after this date.
            Format: ISO date (YYYY-MM-DD), e.g., "2024-01-01"
        end_date: Filters results to content published on or before this date.
            Format: ISO date (YYYY-MM-DD), e.g., "2024-12-31"
        category: Filters results by a specific category.
            Category values are source-dependent.
    """

    search_type: Optional[Literal["all", "web", "proprietary"]] = Field(
        None, description="Search scope: 'all', 'web', or 'proprietary'"
    )
    included_sources: Optional[List[str]] = Field(
        None,
        description="Source types to include: 'web', 'academic', 'finance', 'patent', 'transportation', 'politics', 'legal'",
    )
    excluded_sources: Optional[List[str]] = Field(
        None, description="Source types to exclude from search"
    )
    start_date: Optional[str] = Field(
        None, description="Start date filter in ISO format (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, description="End date filter in ISO format (YYYY-MM-DD)"
    )
    category: Optional[str] = Field(None, description="Category filter for results")


class Progress(BaseModel):
    """Task progress information."""

    current_step: int
    total_steps: int


class ChartDataPoint(BaseModel):
    """Chart data point."""

    x: Union[str, int, float]
    y: Union[int, float]


class ChartDataSeries(BaseModel):
    """Chart data series."""

    name: str
    data: List[ChartDataPoint]


class ImageMetadata(BaseModel):
    """Image metadata."""

    image_id: str
    image_type: Literal["chart", "ai_generated"]
    deepresearch_id: str
    title: str
    description: Optional[str] = None
    image_url: str
    s3_key: str
    created_at: int
    chart_type: Optional[Literal["line", "bar", "area"]] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    data_series: Optional[List[ChartDataSeries]] = None


class DeepResearchSource(BaseModel):
    """Source information."""

    title: str
    url: str
    snippet: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    org_id: Optional[str] = None
    price: Optional[float] = None
    id: Optional[str] = None
    doc_id: Optional[int] = None
    doi: Optional[str] = None
    category: Optional[str] = None
    source_id: Optional[int] = None
    word_count: Optional[int] = None


class Usage(BaseModel):
    """Usage and cost information."""

    search_cost: float
    contents_cost: float
    ai_cost: float
    compute_cost: float
    total_cost: float


class DeepResearchCreateResponse(BaseModel):
    """Response from creating a deep research task."""

    success: bool
    deepresearch_id: Optional[str] = None
    status: Optional[DeepResearchStatus] = None
    mode: Optional[DeepResearchMode] = None
    model: Optional[DeepResearchMode] = None
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, bool]]] = None
    public: Optional[bool] = None
    webhook_secret: Optional[str] = None
    message: Optional[str] = None
    brand_collection_id: Optional[str] = None
    error: Optional[str] = None


class DeepResearchStatusResponse(BaseModel):
    """Response from getting task status."""

    success: bool
    deepresearch_id: Optional[str] = None
    status: Optional[DeepResearchStatus] = None
    query: Optional[str] = None
    mode: Optional[DeepResearchMode] = None
    output_formats: Optional[
        List[Union[Literal["markdown", "pdf", "toon"], Dict[str, Any]]]
    ] = None
    created_at: Optional[str] = None
    public: Optional[bool] = None

    # Optional fields based on status
    progress: Optional[Progress] = None
    messages: Optional[List[Any]] = None
    completed_at: Optional[str] = None
    output: Optional[Union[str, Dict[str, Any], Any]] = None
    output_type: Optional[Literal["markdown", "json", "toon"]] = None
    pdf_url: Optional[str] = None
    images: Optional[List[ImageMetadata]] = None
    deliverables: Optional[List[DeliverableResult]] = None
    sources: Optional[List[DeepResearchSource]] = None
    cost: Optional[float] = None
    batch_id: Optional[str] = None
    batch_task_id: Optional[str] = None
    error: Optional[str] = None


class DeepResearchTaskListItem(BaseModel):
    """Minimal task info for list view."""

    deepresearch_id: str
    query: str
    status: DeepResearchStatus
    created_at: str
    public: Optional[bool] = None


class DeepResearchListResponse(BaseModel):
    """Response from listing tasks."""

    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class DeepResearchUpdateResponse(BaseModel):
    """Response from updating a task."""

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None


class DeepResearchCancelResponse(BaseModel):
    """Response from cancelling a task."""

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None


class DeepResearchDeleteResponse(BaseModel):
    """Response from deleting a task."""

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None


class DeepResearchTogglePublicResponse(BaseModel):
    """Response from toggling public flag."""

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    public: Optional[bool] = None
    error: Optional[str] = None


# =============================================================================
# Batch Types
# =============================================================================


class BatchStatus(str, Enum):
    """Batch status options."""

    OPEN = "open"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    CANCELLED = "cancelled"


class BatchCounts(BaseModel):
    """Task counts within a batch."""

    total: int = Field(..., description="Total number of tasks")
    queued: int = Field(..., description="Number of queued tasks")
    running: int = Field(..., description="Number of running tasks")
    completed: int = Field(..., description="Number of completed tasks")
    failed: int = Field(..., description="Number of failed tasks")
    cancelled: int = Field(..., description="Number of cancelled tasks")


class BatchUsage(BaseModel):
    """Aggregated usage for a batch."""

    search_cost: float = Field(..., description="Total search cost")
    contents_cost: float = Field(..., description="Total contents cost")
    ai_cost: float = Field(..., description="Total AI cost")
    total_cost: float = Field(..., description="Total cost")


class BatchTaskInput(BaseModel):
    """Input for a batch task."""

    id: Optional[str] = Field(None, description="User-provided task ID")
    query: Optional[str] = Field(
        None, description="Research query or task description (preferred)"
    )
    input: Optional[str] = Field(
        None,
        description="Research query or task description (deprecated, use query instead)",
    )
    strategy: Optional[str] = Field(None, description="Natural language strategy")
    urls: Optional[List[str]] = Field(None, description="URLs to extract and analyze")
    metadata: Optional[Dict[str, Union[str, int, bool]]] = Field(
        None, description="Custom metadata"
    )

    @model_validator(mode="after")
    def ensure_query_or_input(self):
        """Ensure at least one of query or input is provided, and sync them."""
        # If input is provided but query is not, copy input to query
        if self.input and not self.query:
            self.query = self.input
        # If query is provided but input is not, copy query to input for backward compatibility
        elif self.query and not self.input:
            self.input = self.query
        # Ensure at least one is provided
        if not self.query and not self.input:
            raise ValueError("Either 'query' or 'input' must be provided")
        return self

    def model_dump(self, **kwargs):
        """Override model_dump to prefer query when sending to API."""
        data = super().model_dump(**kwargs)
        # Ensure query is set for API calls
        if (
            "input" in data
            and data["input"]
            and ("query" not in data or not data["query"])
        ):
            data["query"] = data["input"]
        return data

    def dict(self, **kwargs):
        """Backward compatibility alias for model_dump."""
        return self.model_dump(**kwargs)


class DeepResearchBatch(BaseModel):
    """Batch of deep research tasks."""

    batch_id: str = Field(..., description="Unique batch ID")
    organisation_id: Optional[str] = Field(None, description="Organization ID")
    api_key_id: Optional[str] = Field(None, description="API key ID")
    credit_id: Optional[str] = Field(None, description="Credit ID")
    status: BatchStatus = Field(..., description="Current batch status")
    mode: DeepResearchMode = Field(
        ..., description="Research mode (preferred field name)"
    )
    name: Optional[str] = Field(None, description="Batch name")
    output_formats: Optional[
        List[Union[Literal["markdown", "pdf"], Dict[str, Any]]]
    ] = Field(None, description="Default output formats")
    search_params: Optional[Dict[str, Any]] = Field(
        None, description="Default search parameters"
    )
    counts: BatchCounts = Field(..., description="Task counts")
    cost: float = Field(..., description="Total cost (replaces usage object)")
    webhook_url: Optional[str] = Field(
        None, description="Webhook URL for notifications"
    )
    webhook_secret: Optional[str] = Field(None, description="Webhook secret")
    created_at: str = Field(
        ...,
        description="Creation timestamp (ISO 8601 string, e.g., '2025-01-15T10:30:00.000Z')",
    )
    completed_at: Optional[str] = Field(
        None,
        description="Completion timestamp (ISO 8601 string, e.g., '2025-01-15T10:35:00.000Z')",
    )
    metadata: Optional[Dict[str, Union[str, int, bool]]] = Field(
        None, description="Custom metadata"
    )

    # Backward compatibility fields
    model: Optional[DeepResearchMode] = Field(
        None, description="Research mode (backward compatibility - use 'mode' instead)"
    )
    usage: Optional[BatchUsage] = Field(
        None,
        description="Aggregated usage (backward compatibility - use 'cost' instead)",
    )
    updated_at: Optional[str] = Field(
        None,
        description="Last update timestamp (backward compatibility - field removed from API, ISO 8601 string)",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_mode_and_model(cls, data):
        """Sync mode and model fields for backward compatibility."""
        if isinstance(data, dict):
            # If model is provided but mode is not, copy model to mode
            if "model" in data and "mode" not in data:
                data["mode"] = data["model"]
            # If mode is provided but model is not, copy mode to model for backward compatibility
            elif "mode" in data and "model" not in data:
                data["model"] = data["mode"]
            # Handle usage -> cost migration
            if "usage" in data and "cost" not in data:
                usage_obj = data.get("usage")
                if isinstance(usage_obj, dict) and "total_cost" in usage_obj:
                    data["cost"] = usage_obj["total_cost"]
                elif isinstance(usage_obj, BatchUsage):
                    data["cost"] = usage_obj.total_cost
            # Handle cost -> usage backward compatibility (for code that accesses usage.total_cost)
            if "cost" in data and "usage" not in data:
                cost_value = data.get("cost")
                if cost_value is not None:
                    # Create a usage object from cost for backward compatibility
                    data["usage"] = {
                        "search_cost": 0.0,
                        "contents_cost": 0.0,
                        "ai_cost": 0.0,
                        "total_cost": float(cost_value),
                    }
        return data


class BatchCreateResponse(BaseModel):
    """Response from creating a batch."""

    success: bool
    batch_id: Optional[str] = None
    status: Optional[BatchStatus] = None
    mode: Optional[DeepResearchMode] = None
    name: Optional[str] = None
    output_formats: Optional[
        List[Union[Literal["markdown", "pdf", "toon"], Dict[str, Any]]]
    ] = None
    search_params: Optional[Dict[str, Any]] = None
    counts: Optional[BatchCounts] = None
    cost: Optional[float] = None
    created_at: Optional[str] = None
    webhook_secret: Optional[str] = None
    message: Optional[str] = None
    brand_collection_id: Optional[str] = None
    error: Optional[str] = None

    # Backward compatibility fields - populated by validator
    model: Optional[DeepResearchMode] = Field(
        None, description="Research mode (backward compatibility - use 'mode' instead)"
    )

    @model_validator(mode="before")
    @classmethod
    def sync_mode_and_model(cls, data):
        """Sync mode and model fields for backward compatibility."""
        if isinstance(data, dict):
            # If model is provided but mode is not, copy model to mode
            if "model" in data and "mode" not in data:
                data["mode"] = data["model"]
            # If mode is provided but model is not, copy mode to model for backward compatibility
            elif "mode" in data and "model" not in data:
                data["model"] = data["mode"]
        return data


class BatchTaskCreated(BaseModel):
    """Task created in batch."""

    task_id: Optional[str] = None
    deepresearch_id: str
    status: str


class BatchAddTasksResponse(BaseModel):
    """Response from adding tasks to a batch."""

    success: bool
    batch_id: Optional[str] = None
    added: Optional[int] = None
    tasks: Optional[List[BatchTaskCreated]] = None
    task_ids: Optional[List[str]] = None  # Kept for backward compatibility
    counts: Optional[BatchCounts] = None
    message: Optional[str] = None
    error: Optional[str] = None


class BatchStatusResponse(BaseModel):
    """Response from getting batch status."""

    success: bool
    batch: Optional[DeepResearchBatch] = None
    error: Optional[str] = None


class BatchTaskListItem(BaseModel):
    """Minimal task info in batch list."""

    deepresearch_id: str
    task_id: Optional[str] = None
    query: str
    status: DeepResearchStatus
    created_at: str
    completed_at: Optional[str] = None


class BatchPagination(BaseModel):
    """Pagination information for batch task lists."""

    count: int
    last_key: Optional[str] = None
    has_more: bool


class BatchTasksListResponse(BaseModel):
    """Response from listing tasks in a batch."""

    success: bool
    batch_id: Optional[str] = None
    tasks: Optional[List[BatchTaskListItem]] = None
    pagination: Optional[BatchPagination] = None
    error: Optional[str] = None


class BatchCancelResponse(BaseModel):
    """Response from cancelling a batch."""

    success: bool
    batch_id: Optional[str] = None
    status: Optional[BatchStatus] = None
    cancelled_count: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class BatchListResponse(BaseModel):
    """Response from listing batches."""

    success: bool
    batches: Optional[List[DeepResearchBatch]] = None
    error: Optional[str] = None
