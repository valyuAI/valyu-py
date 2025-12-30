from pydantic import BaseModel, Field
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

    data: str = Field(..., description="Data URL (base64 encoded)")
    filename: str = Field(..., description="Original filename")
    media_type: str = Field(..., description="MIME type")
    context: Optional[str] = Field(None, description="Context about the file")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    url: str = Field(..., description="MCP server URL")
    name: Optional[str] = Field(None, description="Server name")
    tool_prefix: Optional[str] = Field(None, description="Custom tool prefix")
    auth: Optional[Dict[str, Any]] = Field(None, description="Authentication config")
    allowed_tools: Optional[List[str]] = Field(
        None, description="Allowed tools"
    )


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
    description: Optional[str] = Field(None, description="Deliverable content description")
    url: str = Field(..., description="Token-signed authenticated URL to download the file")
    s3_key: str = Field(..., description="S3 storage key")
    row_count: Optional[int] = Field(None, description="Number of rows (for CSV/XLSX)")
    column_count: Optional[int] = Field(None, description="Number of columns (for CSV/XLSX)")
    error: Optional[str] = Field(None, description="Error message if status is failed")
    created_at: int = Field(..., description="Unix timestamp of creation")


class SearchConfig(BaseModel):
    """Search configuration."""

    search_type: Optional[Literal["all", "web", "proprietary"]] = None
    included_sources: Optional[List[str]] = None


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
    model: Optional[DeepResearchMode] = None
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, bool]]] = None
    public: Optional[bool] = None
    webhook_secret: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class DeepResearchStatusResponse(BaseModel):
    """Response from getting task status."""

    success: bool
    deepresearch_id: Optional[str] = None
    status: Optional[DeepResearchStatus] = None
    query: Optional[str] = None
    mode: Optional[DeepResearchMode] = None
    output_formats: Optional[List[Union[Literal["markdown", "pdf"], Dict[str, Any]]]] = None
    created_at: Optional[int] = None
    public: Optional[bool] = None

    # Optional fields based on status
    progress: Optional[Progress] = None
    messages: Optional[List[Any]] = None
    completed_at: Optional[int] = None
    output: Optional[Union[str, Dict[str, Any], Any]] = None
    output_type: Optional[Literal["markdown", "json"]] = None
    pdf_url: Optional[str] = None
    images: Optional[List[ImageMetadata]] = None
    deliverables: Optional[List[DeliverableResult]] = None
    sources: Optional[List[DeepResearchSource]] = None
    usage: Optional[Usage] = None
    error: Optional[str] = None


class DeepResearchTaskListItem(BaseModel):
    """Minimal task info for list view."""

    deepresearch_id: str
    query: str
    status: DeepResearchStatus
    created_at: int
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
