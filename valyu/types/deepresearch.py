from pydantic import BaseModel, BeforeValidator, Field, model_validator, ConfigDict
from typing import Optional, List, Literal, Union, Dict, Any, Callable
from typing_extensions import Annotated
from enum import Enum

from valyu.types.rate_limit import RateLimitDetail
from valyu.types.warning import ResponseWarnings
from valyu.types.workflows import WorkflowRunInfo


class AlertEmailConfig(BaseModel):
    """Alert email configuration with optional custom URL."""

    email: str = Field(..., description="Email address to send alerts to")
    custom_url: Optional[str] = Field(
        default=None, description="Custom URL with {id} placeholder, replaced with task ID"
    )


class DeepResearchMode(str, Enum):
    """Research mode options."""

    INSTANT = "instant"
    FAST = "fast"
    STANDARD = "standard"
    LITE = "lite"  # Deprecated: use STANDARD instead (kept for backward compatibility)
    HEAVY = "heavy"
    MAX = "max"


class DeepResearchStatus(str, Enum):
    """Task status options."""

    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _open_enum(enum_cls: Any) -> Callable[[Any], Any]:
    """
    Validator for an enum field in an API response that tolerates values added
    after this SDK release. A known value parses to the enum member as usual;
    an unknown string is kept as a plain string instead of failing the whole
    response.
    """

    def parse(value):
        try:
            return enum_cls(value)
        except (ValueError, TypeError):
            return value

    return parse


_OpenMode = Annotated[Union[DeepResearchMode, str], BeforeValidator(_open_enum(DeepResearchMode))]
_OpenStatus = Annotated[Union[DeepResearchStatus, str], BeforeValidator(_open_enum(DeepResearchStatus))]


def _mode_from_research_mode(data):
    """Fill ``mode`` from ``research_mode`` when the response only carries the latter."""
    if (
        isinstance(data, dict)
        and data.get("mode") is None
        and data.get("research_mode") is not None
    ):
        data = {**data, "mode": data["research_mode"]}
    return data


class FileAttachment(BaseModel):
    """File attachment for research."""

    model_config = ConfigDict(populate_by_name=True)

    data: str = Field(..., description="Data URL (base64 encoded)")
    filename: str = Field(..., description="Original filename")
    media_type: str = Field(..., description="MIME type", alias="mediaType")
    context: Optional[str] = Field(
        default=None,
        description="Context about the file (max 50,000 characters; 100,000 combined across all files)",
    )


class CoverArt(BaseModel):
    """
    Cover art for one report, replacing the brand kit's cover art on the report
    PDF and PDF deliverable. Works without a brand kit.

    Send exactly one of ``data`` or ``url``. Pictures must be PNG or JPEG, at most
    2 MB, and 800 px or more on the short side. A picture that cannot be used
    never fails the task: the kit's cover art (or the standard cover) is used and
    the response ``warnings`` include ``cover_art_not_used``.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: Optional[Literal["image", "pattern"]] = Field(
        default=None,
        description='"image" (photo or illustration, default) or "pattern" (brand graphic, shown more quietly)',
    )
    data: Optional[str] = Field(
        default=None, description="Base64 string or data URL of the picture (PNG or JPEG)"
    )
    url: Optional[str] = Field(
        default=None, description="Public https URL of the picture, fetched when the report is rendered"
    )
    filename: Optional[str] = Field(default=None, description="File name (optional)")
    media_type: Optional[str] = Field(
        default=None, description='"image/png" or "image/jpeg" (optional)', alias="mediaType"
    )


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    url: str = Field(..., description="MCP server URL")
    name: Optional[str] = Field(default=None, description="Server name")
    tool_prefix: Optional[str] = Field(default=None, description="Custom tool prefix")
    auth: Optional[Dict[str, Any]] = Field(default=None, description="Authentication config")
    allowed_tools: Optional[List[str]] = Field(default=None, description="Allowed tools")


class Deliverable(BaseModel):
    """Deliverable file configuration."""

    type: Literal["csv", "xlsx", "pptx", "docx", "pdf"] = Field(
        ..., description="File type"
    )
    description: str = Field(
        ..., max_length=500, description="What data to extract or content to generate"
    )
    columns: Optional[List[str]] = Field(
        default=None, description="Suggested column names (for CSV/XLSX)"
    )
    include_headers: Optional[bool] = Field(
        True, description="Include column headers (for CSV/XLSX)"
    )
    sheet_name: Optional[str] = Field(default=None, description="Sheet name (for XLSX only)")
    slides: Optional[int] = Field(default=None, description="Number of slides (for PPTX only)")
    template: Optional[str] = Field(default=None, description="Template name to use")


def _drop_keys(*names):
    """A before-validator that removes internal keys a response may carry, so they are not
    kept as extra fields on a model that allows extras."""

    def drop(cls, data):
        if isinstance(data, dict) and any(n in data for n in names):
            data = {k: v for k, v in data.items() if k not in names}
        return data

    return model_validator(mode="before")(classmethod(drop))


class DeliverableResult(BaseModel):
    """Deliverable generation result."""

    model_config = ConfigDict(extra="allow")

    _strip_internal = _drop_keys("s3_key")

    id: str = Field(..., description="Unique deliverable ID")
    request: str = Field(..., description="Original request description")
    type: Union[Literal["csv", "xlsx", "pptx", "docx", "pdf", "unknown"], str] = Field(
        ..., description="Deliverable file type"
    )
    status: Union[Literal["completed", "failed", "pending"], str] = Field(
        ...,
        description=(
            "Generation status. 'pending' means the deliverable is still being produced "
            "(the task is still running): url, row_count and column_count are not "
            "yet available."
        ),
    )
    title: str = Field(..., description="Generated filename/title")
    description: Optional[str] = Field(
        default=None, description="Deliverable content description"
    )
    url: Optional[str] = Field(
        default=None, description="Token-signed authenticated URL to download the file (absent while pending)"
    )
    row_count: Optional[int] = Field(default=None, description="Number of rows (for CSV/XLSX)")
    column_count: Optional[int] = Field(
        default=None, description="Number of columns (for CSV/XLSX)"
    )
    error: Optional[str] = Field(default=None, description="Error message if status is failed")
    created_at: Optional[int] = Field(default=None, description="Unix timestamp of creation (absent while pending)")
    # Additional fields, beside the ones above.
    filename: Optional[str] = None
    bytes: Optional[int] = None
    attempts: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None


class SearchConfig(BaseModel):
    """Search configuration for Deep Research tasks and batches.

    Controls which data sources are queried, what content is included/excluded,
    and how results are filtered by date, category, or country.

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
        start_date: Inclusive lower bound on content date. Accepts a bare date
            (YYYY-MM-DD, day granularity, e.g. "2026-01-01") or a full ISO-8601
            datetime (YYYY-MM-DDTHH:MM[:SS[.sss]][Z|±HH:MM], e.g.
            "2026-01-01T00:00:00Z"; a space separator is also accepted). A value
            with any time component requires historical_cache=True and is
            otherwise rejected with HTTP 400 — use a bare date for standard search.
        end_date: Inclusive upper bound on content date. Same formats and
            historical_cache=True requirement for sub-day timestamps as start_date.
        historical_cache: When True and a date range (start_date and/or end_date)
            is set, searches return the newest cached snapshot inside the range
            instead of the latest crawl — a leak-safe "as-of" backtest (snapshot
            metadata only on a hit; the URL is dropped on a miss). Also gates
            sub-day precision: required to pass any timestamped start_date/end_date
            (a time component without it is rejected with HTTP 400). No-op without
            a date range. User-set only and locked for the whole research run —
            the agent cannot toggle it mid-research.
        category: Filters results by a specific category.
            Category values are source-dependent.
        country_code: ISO country code for location-filtered searches.
            E.g., "US", "GB", "DE". Only applies to web search results.
    """

    search_type: Optional[Literal["all", "web", "proprietary"]] = Field(
        default=None, description="Search scope: 'all', 'web', or 'proprietary'"
    )
    included_sources: Optional[List[str]] = Field(
        default=None,
        description="Source types to include: 'web', 'academic', 'finance', 'patent', 'transportation', 'politics', 'legal'",
    )
    excluded_sources: Optional[List[str]] = Field(
        default=None, description="Source types to exclude from search"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Inclusive start bound. Bare date (YYYY-MM-DD) or full ISO-8601 datetime; a datetime with any time component requires historical_cache=True, else HTTP 400.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Inclusive end bound. Bare date (YYYY-MM-DD) or full ISO-8601 datetime; a datetime with any time component requires historical_cache=True, else HTTP 400.",
    )
    historical_cache: Optional[bool] = Field(
        default=None,
        description="When True and a date range is set, return the newest cached snapshot inside the range (leak-safe as-of backtest) instead of the latest crawl. Also required to pass any sub-day timestamp on start_date/end_date. No-op without a date range. User-set only.",
    )
    category: Optional[str] = Field(default=None, description="Category filter for results")
    country_code: Optional[str] = Field(
        default=None, description="ISO country code for location-filtered searches (e.g., 'US', 'GB')"
    )
    source_biases: Optional[Dict[str, int]] = Field(
        default=None,
        description="Bias values for specific sources (-5 to +5) to influence ranking without hard filtering",
    )


class Progress(BaseModel):
    """Task progress information."""

    current_step: int
    total_steps: int


class ChartDataPoint(BaseModel):
    """Chart data point."""

    x: Union[str, int, float]
    y: Union[int, float]
    y2: Optional[Union[int, float]] = None
    z: Optional[Union[int, float]] = None
    values: Optional[List[Union[int, float]]] = None


class ChartDataSeries(BaseModel):
    """Chart data series."""

    name: str
    data: List[ChartDataPoint]
    line_style: Optional[Literal["solid", "dashed", "dotted"]] = None


class ToolConfig(BaseModel):
    """Per-tool configuration with optional call limit."""

    enabled: Optional[bool] = Field(True, description="Enable or disable the tool")
    max_calls: Optional[int] = Field(default=None, description="Max invocations per task. Capped at system default if exceeded.")


class UltrasearchConfig(BaseModel):
    """Ultrasearch options. Pass as ``tools.ultrasearch`` in Heavy or Max mode."""

    model_config = ConfigDict(extra="allow")

    max_usd: float = Field(
        ...,
        gt=0,
        allow_inf_nan=False,
        description="Maximum spend for Ultrasearch on this task, in USD. Must be greater than 0.",
    )


class DeepResearchTools(BaseModel):
    """Tools configuration for deep research tasks.

    Each tool accepts either a boolean (shorthand) or a ToolConfig object
    with `enabled` and optional `max_calls` fields.

    System defaults for max_calls:
        - browser_use: 5
        - screenshots: 15
        - code_execution: 10

    max_calls can only be lowered, not raised above the system default.
    Setting max_calls: 0 effectively disables the tool.
    """

    model_config = ConfigDict(extra="allow")

    code_execution: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Enable code execution in sandboxed environment")
    screenshots: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Enable visual screenshot capture of web pages")
    browser_use: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Enable autonomous browser sessions")
    charts: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Enable chart/graph generation embedded in the final report (free, unlimited)")
    # Newer tool names, returned on reads beside the older names above (a response can carry
    # both). `read` and `analyse` replace `urls`/`code_execution`; `browse` replaces
    # `browser_use`; `screenshot` replaces `screenshots`.
    x_search: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Enable X (Twitter) search")
    read: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Newer name for reading supplied or found URLs")
    analyse: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Newer name for code_execution")
    browse: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Newer name for browser_use")
    screenshot: Optional[Union[bool, ToolConfig]] = Field(default=None, description="Newer name for screenshots")
    ultrasearch: Optional[Union[bool, "UltrasearchConfig"]] = Field(
        default=None,
        description=(
            "Enable Ultrasearch (Heavy and Max modes only). True uses the default spend cap; "
            "an UltrasearchConfig sets max_usd. False or None leaves it off."
        ),
    )


class ImageMetadata(BaseModel):
    """Image metadata."""

    model_config = ConfigDict(extra="allow")

    image_id: str
    # "attachment": an uploaded or url-supplied image, listed alongside charts and screenshots.
    # A trailing plain `str` keeps this forward-compatible with an image kind introduced later.
    image_type: Union[Literal["chart", "ai_generated", "screenshot", "attachment"], str]
    title: str
    description: Optional[str] = None
    image_url: str
    created_at: Optional[int] = None  # absent on an image attachment entry
    # Screenshot-only fields
    source_url: Optional[str] = None
    captured_at: Optional[int] = None
    chart_type: Optional[
        Union[
            Literal[
                "line",
                "bar",
                "area",
                "pie",
                "doughnut",
                "radar",
                "scatter",
                "horizontalBar",
                "heatmap",
                "boxplot",
                "stackedBar",
                "stackedArea",
                "histogram",
                "waterfall",
                "timeline",
                "bubble",
                # Newer chart kinds (a response can carry one instead of the 16 older types above).
                "stacked",
                "slope",
            ],
            str,
        ]
    ] = None
    # The newer chart kind, kept beside `chart_type` even when `chart_type` holds the value
    # mapped onto one of the 16 older types above (e.g. "stacked" -> "stackedBar", "slope" ->
    # "line"). Absent on a chart created before this field existed.
    chart_kind: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    data_series: Optional[List[ChartDataSeries]] = None


class SourceLocation(BaseModel):
    """One position in a source that the report cited, in first-cited order.

    `piece` and `page` locate the cited passage within a long upload (a document piece, a PDF
    page); `excerpt` is the verbatim text the report cited there. Any of the three may be absent
    depending on the source kind. Unknown keys are kept rather than rejected, since this shape may
    grow server-side ahead of an SDK release.
    """

    model_config = ConfigDict(extra="allow")

    piece: Optional[str] = None
    page: Optional[int] = None
    excerpt: Optional[str] = None


class DeepResearchSource(BaseModel):
    """Source information."""

    model_config = ConfigDict(extra="allow")

    _strip_internal = _drop_keys("org_id", "doc_id", "source_id")

    title: str
    url: str
    snippet: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    price: Optional[float] = None
    id: Optional[str] = None
    doi: Optional[str] = None
    category: Optional[str] = None
    word_count: Optional[int] = None
    fragment: Optional[str] = None
    # Dates and tier.
    crawl_date: Optional[str] = None
    updated_date: Optional[str] = None
    tier: Optional[int] = None
    tier_label: Optional[str] = None
    # The positions in this source that the report actually cited (first-cited order).
    # absent on a task created before this field existed, or when the source has none.
    locations: Optional[List[SourceLocation]] = None


class Usage(BaseModel):
    """Usage and cost information."""

    search_cost: float
    contents_cost: float
    ai_cost: float
    compute_cost: float
    total_cost: float


class CostDetailLine(BaseModel):
    """One line of `cost_detail`'s itemized bill (a tool charge or a dataset charge)."""

    model_config = ConfigDict(extra="allow")

    item: Optional[str] = None
    label: Optional[str] = None
    pricing: Optional[str] = None
    unit: Optional[str] = None
    units: Optional[float] = None
    free_units: Optional[float] = None
    billed_units: Optional[float] = None
    unit_price_usd: Optional[float] = None
    usd: Optional[float] = None
    # Kept for callers written against an earlier draft of this shape.
    amount: Optional[float] = None


class DeepResearchCostDetail(BaseModel):
    """Itemized bill: the base price, each tool and dataset charged, and the total.

    A response can send this beside the numbers-only `cost_breakdown`, or as `cost_breakdown`
    itself. Read it with `DeepResearchStatusResponse.effective_cost_detail()`.
    """

    model_config = ConfigDict(extra="allow")

    task: Optional[float] = None
    base_usd: Optional[float] = None
    tools: Optional[List[CostDetailLine]] = None
    datasets: Optional[List[CostDetailLine]] = None
    total_usd: Optional[float] = None


class DeepResearchCostBreakdown(BaseModel):
    """Itemized cost breakdown for a deep research task.

    A response can send this as numbers only (`task`, `screenshots`, ...), with a richer bill
    beside it under `cost_detail`. It can also send the richer bill directly as `cost_breakdown`.
    In that case `datasets` and `tools` here are line-item lists, and `base_usd`, `tools` and
    `total_usd` can be set with no separate `cost_detail`. Prefer `cost_detail` when it is set;
    otherwise read this model's `base_usd`, `tools` and `total_usd`
    (see `DeepResearchStatusResponse.effective_cost_detail()`).
    """

    model_config = ConfigDict(extra="allow")

    task: float = Field(..., description="Base task price for the selected mode")
    screenshots: Optional[float] = Field(default=None, description="Screenshot surcharges ($0.05, 8 credits, per successful capture)")
    code_execution: Optional[float] = Field(default=None, description="Code execution surcharges ($0.10, 16 credits, per successful run)")
    deliverables: Optional[float] = Field(default=None, description="Deliverable surcharges ($0.10, 16 credits, per deliverable after the first)")
    datasets: Optional[Union[float, List[CostDetailLine]]] = Field(default=None, description="Premium dataset surcharges: a summed number or a line-item list")
    x_search: Optional[float] = Field(default=None, description="X search surcharges, summed")
    browse: Optional[float] = Field(default=None, description="Browser-use / browse surcharges, summed")
    other_tools: Optional[float] = Field(default=None, description="Any other tool surcharge not broken out above")
    # Present when this is the itemized bill rather than the numbers-only one.
    base_usd: Optional[float] = None
    tools: Optional[List[CostDetailLine]] = None
    total_usd: Optional[float] = None


class HitlConfig(BaseModel):
    """Human-in-the-loop configuration for deep research tasks.

    Enable checkpoints that pause execution at key decision points,
    allowing users to review and guide the research process.
    """

    planning_questions: Optional[bool] = Field(
        default=None, description="Pause before research to ask clarifying questions"
    )
    plan_review: Optional[bool] = Field(
        default=None, description="Pause after planning for user to review the research plan"
    )
    source_review: Optional[bool] = Field(
        default=None, description="Pause after research for user to filter sources by domain"
    )
    outline_review: Optional[bool] = Field(
        default=None, description="Pause after source review for user to review the report outline"
    )


class InteractionType(str, Enum):
    """HITL checkpoint types."""

    PLANNING_QUESTIONS = "planning_questions"
    PLAN_REVIEW = "plan_review"
    SOURCE_REVIEW = "source_review"
    OUTLINE_REVIEW = "outline_review"


_OpenInteractionType = Annotated[Union[InteractionType, str], BeforeValidator(_open_enum(InteractionType))]


class Interaction(BaseModel):
    """HITL interaction payload returned when a task is awaiting input."""

    interaction_id: str = Field(..., description="Unique ID for this interaction (use when responding)")
    type: _OpenInteractionType = Field(..., description="Type of checkpoint")
    data: Dict[str, Any] = Field(..., description="Checkpoint-specific data")
    created_at: int = Field(..., description="Unix timestamp (ms) when checkpoint fired")
    timeout_ms: int = Field(..., description="Timeout duration in milliseconds")
    expected_response: Optional[Dict[str, Any]] = Field(
        default=None, description="Schema hint for the expected response shape"
    )


class InteractionHistoryEntry(BaseModel):
    """Record of a completed HITL checkpoint."""

    interaction_id: str
    type: _OpenInteractionType
    created_at: int = Field(..., description="When the checkpoint fired (ms)")
    responded_at: Optional[int] = Field(default=None, description="When the user responded (ms)")
    auto_continued: bool = Field(..., description="True if timed out, false if user responded")
    response: Optional[Dict[str, Any]] = Field(default=None, description="The user's response (absent if timed out)")


class StructuredSection(BaseModel):
    """One node of a `structured_report`'s section tree.

    `heading` is `None` for the lead: the text between the report's title and its first heading.
    The tree round-trips to the report body; `markdown` is the section's own text up to its first
    sub-heading, with citations in the public `[[n]](url)` form; `citations` lists the `[[n]]`
    numbers that text cites, in order of first use.
    """

    heading: Optional[str] = None
    level: int
    markdown: str
    citations: List[int] = Field(default_factory=list)
    children: Optional[List["StructuredSection"]] = None


StructuredSection.model_rebuild()


class StructuredTable(BaseModel):
    """One table extracted into a `structured_report`."""

    model_config = ConfigDict(extra="allow")

    id: str
    caption: Optional[str] = None
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    citations: List[int] = Field(default_factory=list)


class StructuredChart(BaseModel):
    """One chart referenced from a `structured_report`."""

    model_config = ConfigDict(extra="allow")

    title: str
    image_url: str
    data_table_ref: Optional[str] = None


class StructuredSourceRef(BaseModel):
    """One source entry of a `structured_report`, numbered as the report cites it."""

    model_config = ConfigDict(extra="allow")

    n: int
    title: str
    url: Optional[str] = None


class StructuredReport(BaseModel):
    """`output_formats: ["structured_report"]`'s typed JSON tree: the report parsed
    deterministically into sections, tables, charts and sources, with no model rewriting any text.
    """

    model_config = ConfigDict(extra="allow")

    title: Optional[str] = None
    summary: Optional[str] = None
    sections: List[StructuredSection] = Field(default_factory=list)
    tables: List[StructuredTable] = Field(default_factory=list)
    charts: List[StructuredChart] = Field(default_factory=list)
    sources: List[StructuredSourceRef] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DeepResearchCreateResponse(BaseModel):
    """Response from creating a deep research task."""

    model_config = ConfigDict(extra="allow")

    success: bool
    deepresearch_id: Optional[str] = None
    status: Optional[_OpenStatus] = None
    mode: Optional[_OpenMode] = None
    model: Optional[_OpenMode] = None
    research_mode: Optional[str] = Field(
        default=None,
        description="Research mode as sent by the API. mode is filled from it when the response has no mode.",
    )
    output_formats: Optional[List[Union[str, Dict[str, Any]]]] = None
    research_output_formats: Optional[List[Union[str, Dict[str, Any]]]] = None
    query: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, bool]]] = None
    public: Optional[bool] = None
    webhook_secret: Optional[str] = None
    message: Optional[str] = None
    brand_collection_id: Optional[str] = None
    workflow: Optional[WorkflowRunInfo] = None
    warnings: ResponseWarnings = None
    error: Optional[str] = None
    rate_limit: Optional[RateLimitDetail] = Field(
        default=None,
        description="Structured detail when `error` is caused by HTTP 429 (rate limited). None otherwise.",
    )

    ignored_fields: Optional[List[str]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def fill_mode_from_research_mode(cls, data):
        return _mode_from_research_mode(data)


class DeepResearchStatusResponse(BaseModel):
    """Response from getting task status."""

    model_config = ConfigDict(extra="allow")

    success: bool
    deepresearch_id: Optional[str] = None
    status: Optional[_OpenStatus] = None
    query: Optional[str] = None
    mode: Optional[_OpenMode] = None
    research_mode: Optional[str] = Field(
        default=None,
        description="Research mode as sent by the API. mode is filled from it when the response has no mode.",
    )
    output_formats: Optional[
        List[Union[Literal["markdown", "pdf", "toon"], str, Dict[str, Any]]]
    ] = None
    research_output_formats: Optional[List[Union[str, Dict[str, Any]]]] = None
    created_at: Optional[str] = None
    public: Optional[bool] = None

    # Optional fields based on status
    progress: Optional[Progress] = None
    messages: Optional[List[Any]] = None
    completed_at: Optional[str] = None
    output: Optional[Union[str, Dict[str, Any], Any]] = None
    output_type: Optional[Union[Literal["markdown", "json", "toon"], str]] = None
    # The markdown rendering beside a structured/json `output` (e.g. when `output_formats`
    # includes `structured_report`, which answers `output_type: "json"` with `output` the typed
    # tree below; `markdown` carries the equivalent report text).
    markdown: Optional[str] = None
    structured_report: Optional[StructuredReport] = Field(
        default=None, description="The typed JSON tree for output_formats: ['structured_report']"
    )
    title: Optional[str] = None
    total_word_count: Optional[int] = None
    pdf_url: Optional[str] = None
    images: Optional[List[ImageMetadata]] = None
    deliverables: Optional[List[DeliverableResult]] = None
    sources: Optional[List[DeepResearchSource]] = None
    cost: Optional[float] = None
    cost_breakdown: Optional[DeepResearchCostBreakdown] = Field(default=None, description="Itemized cost breakdown (task, screenshots, code_execution, deliverables)")
    cost_detail: Optional[DeepResearchCostDetail] = Field(
        default=None, description="Itemized bill (base_usd, labelled tool/dataset lines, total_usd), beside cost_breakdown"
    )
    tools: Optional[DeepResearchTools] = Field(default=None, description="Resolved tools configuration")
    batch_id: Optional[str] = None
    batch_task_id: Optional[str] = None
    harness: Optional[str] = Field(default=None, description="The task's harness id (e.g. 'default', 'people', 'forecasting')")
    ignored_fields: Optional[List[str]] = Field(default=None, description="Top-level request fields the server ignored")

    # HITL fields
    hitl_config: Optional[Dict[str, Any]] = Field(default=None, description="HITL configuration (mirrors request hitl param)")
    interaction: Optional[Interaction] = Field(default=None, description="Current HITL checkpoint (present when awaiting_input or paused)")
    hitl_history: Optional[List[InteractionHistoryEntry]] = Field(default=None, description="History of completed HITL checkpoints")

    warnings: ResponseWarnings = None
    error: Optional[str] = None
    error_message: Optional[str] = Field(default=None, description="User-facing sentence for `error_code` (present only for user-visible codes)")
    error_code: Optional[str] = Field(default=None, description="Catalogue error code, e.g. 'research.no_evidence'")
    unreachable: Optional[bool] = Field(
        default=None,
        description=(
            "True when success=False because the status endpoint could not be "
            "reached after retries (transient gateway/network failure). This is "
            "retryable and distinct from a failed task — the report may still be "
            "available."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def fill_mode_from_research_mode(cls, data):
        return _mode_from_research_mode(data)

    def effective_cost_detail(self) -> Optional["DeepResearchCostDetail"]:
        """The itemized bill, wherever it was sent: the separate `cost_detail` field, or
        `cost_breakdown` itself when that field already holds the itemized bill
        (`base_usd`/`tools`/`total_usd` set, with no separate `cost_detail`)."""
        if self.cost_detail is not None:
            return self.cost_detail
        cb = self.cost_breakdown
        if cb is None or cb.base_usd is None:
            return None
        tools = cb.tools
        datasets = cb.datasets if isinstance(cb.datasets, list) else None
        return DeepResearchCostDetail(task=cb.task, base_usd=cb.base_usd, tools=tools, datasets=datasets, total_usd=cb.total_usd)


class DeepResearchTaskListItem(BaseModel):
    """Minimal task info for list view."""

    model_config = ConfigDict(extra="allow")

    deepresearch_id: str
    query: str
    status: _OpenStatus
    created_at: str
    title: Optional[str] = None
    public: Optional[bool] = None


class DeepResearchListResponse(BaseModel):
    """Response from listing tasks."""

    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class DeepResearchUpdateResponse(BaseModel):
    """Response from updating a task."""

    model_config = ConfigDict(extra="allow")

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class DeepResearchCancelResponse(BaseModel):
    """Response from cancelling a task."""

    model_config = ConfigDict(extra="allow")

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class DeepResearchRespondResponse(BaseModel):
    """Response from responding to a HITL checkpoint."""

    model_config = ConfigDict(extra="allow")

    success: bool
    status: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class DeepResearchDeleteResponse(BaseModel):
    """Response from deleting a task."""

    model_config = ConfigDict(extra="allow")

    success: bool
    message: Optional[str] = None
    deepresearch_id: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


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


_OpenBatchStatus = Annotated[Union[BatchStatus, str], BeforeValidator(_open_enum(BatchStatus))]


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

    id: Optional[str] = Field(default=None, description="User-provided task ID")
    query: Optional[str] = Field(
        default=None, description="Research query or task description (preferred)"
    )
    input: Optional[str] = Field(
        default=None,
        description="Research query or task description (deprecated, use query instead)",
    )
    strategy: Optional[str] = Field(
        default=None, description="Natural language strategy (deprecated, use research_strategy)"
    )
    research_strategy: Optional[str] = Field(
        default=None, description="Natural language strategy to guide the research phase"
    )
    report_format: Optional[str] = Field(
        default=None,
        description="Natural language instructions for output format (highest priority, overrides defaults)",
    )
    urls: Optional[List[str]] = Field(default=None, description="URLs to extract and analyze")
    metadata: Optional[Dict[str, Union[str, int, bool]]] = Field(
        default=None, description="Custom metadata"
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

    model_config = ConfigDict(extra="allow")

    _strip_internal = _drop_keys("organisation_id", "api_key_id", "credit_id")

    batch_id: str = Field(..., description="Unique batch ID")
    status: _OpenBatchStatus = Field(..., description="Current batch status")
    mode: _OpenMode = Field(
        ..., description="Research mode (preferred field name)"
    )
    # See `DeepResearchStatusResponse.research_mode`: the mode as sent by the API.
    research_mode: Optional[_OpenMode] = None
    name: Optional[str] = Field(default=None, description="Batch name")
    output_formats: Optional[
        List[Union[Literal["markdown", "pdf", "toon"], str, Dict[str, Any]]]
    ] = Field(default=None, description="Default output formats")
    research_output_formats: Optional[List[Union[str, Dict[str, Any]]]] = None
    search_params: Optional[Dict[str, Any]] = Field(
        default=None, description="Default search parameters"
    )
    counts: BatchCounts = Field(..., description="Task counts")
    cost: float = Field(..., description="Total cost (replaces usage object)")
    webhook_url: Optional[str] = Field(
        default=None, description="Webhook URL for notifications"
    )
    webhook_secret: Optional[str] = Field(default=None, description="Webhook secret")
    created_at: str = Field(
        ...,
        description="Creation timestamp (ISO 8601 string, e.g., '2025-01-15T10:30:00.000Z')",
    )
    completed_at: Optional[str] = Field(
        default=None,
        description="Completion timestamp (ISO 8601 string, e.g., '2025-01-15T10:35:00.000Z')",
    )
    metadata: Optional[Dict[str, Union[str, int, bool]]] = Field(
        default=None, description="Custom metadata"
    )
    warnings: Optional[List[str]] = None

    # Backward compatibility fields
    model: Optional[_OpenMode] = Field(
        default=None, description="Research mode (backward compatibility - use 'mode' instead)"
    )
    usage: Optional[BatchUsage] = Field(
        default=None,
        description="Aggregated usage (backward compatibility - use 'cost' instead)",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="Last update timestamp (backward compatibility - field removed from API, ISO 8601 string)",
    )

    def effective_mode(self) -> Optional[str]:
        """See `DeepResearchStatusResponse.effective_mode()`."""
        return self.research_mode or self.mode

    def effective_output_formats(self) -> Optional[List[Union[str, Dict[str, Any]]]]:
        """See `DeepResearchStatusResponse.effective_output_formats()`."""
        return self.research_output_formats or self.output_formats

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

    model_config = ConfigDict(extra="allow")

    success: bool
    batch_id: Optional[str] = None
    status: Optional[_OpenBatchStatus] = None
    mode: Optional[_OpenMode] = None
    research_mode: Optional[_OpenMode] = None
    name: Optional[str] = None
    output_formats: Optional[
        List[Union[Literal["markdown", "pdf", "toon"], str, Dict[str, Any]]]
    ] = None
    research_output_formats: Optional[List[Union[str, Dict[str, Any]]]] = None
    search_params: Optional[Dict[str, Any]] = None
    counts: Optional[BatchCounts] = None
    cost: Optional[float] = None
    created_at: Optional[str] = None
    webhook_secret: Optional[str] = None
    message: Optional[str] = None
    brand_collection_id: Optional[str] = None
    warnings: Optional[List[str]] = None
    ignored_fields: Optional[List[str]] = None
    error: Optional[str] = None
    rate_limit: Optional[RateLimitDetail] = Field(
        default=None,
        description="Structured detail when `error` is caused by HTTP 429 (rate limited). None otherwise.",
    )

    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Backward compatibility fields - populated by validator
    model: Optional[_OpenMode] = Field(
        default=None, description="Research mode (backward compatibility - use 'mode' instead)"
    )

    def effective_mode(self) -> Optional[str]:
        """See `DeepResearchStatusResponse.effective_mode()`."""
        return self.research_mode or self.mode or self.model

    def effective_output_formats(self) -> Optional[List[Union[str, Dict[str, Any]]]]:
        """See `DeepResearchStatusResponse.effective_output_formats()`."""
        return self.research_output_formats or self.output_formats

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
    rate_limit: Optional[RateLimitDetail] = Field(
        default=None,
        description="Structured detail when `error` is caused by HTTP 429 (rate limited). None otherwise.",
    )


class BatchStatusResponse(BaseModel):
    """Response from getting batch status."""

    success: bool
    batch: Optional[DeepResearchBatch] = None
    error: Optional[str] = None


class BatchTaskListItem(BaseModel):
    """Task info in batch list. Extended fields included when include_output=True."""

    model_config = ConfigDict(extra="allow")

    deepresearch_id: str
    task_id: Optional[str] = None
    query: str
    status: _OpenStatus
    created_at: str
    completed_at: Optional[str] = None
    # Included when include_output=True
    output_type: Optional[str] = None
    output: Optional[Any] = None
    sources: Optional[List[Any]] = None
    images: Optional[List[Any]] = None
    pdf_url: Optional[str] = None
    deliverables: Optional[Any] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    cost: Optional[float] = None


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
    status: Optional[_OpenBatchStatus] = None
    cancelled_count: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class BatchListResponse(BaseModel):
    """Response from listing batches."""

    success: bool
    batches: Optional[List[DeepResearchBatch]] = None
    error: Optional[str] = None


# `error_code` values worth an automatic retry: each names a condition that is transient or
# never billed, rather than a refusal of the request itself. Not exhaustive — treat an unlisted
# code as non-retryable. See docs/errors for the full catalogue.
RETRYABLE_ERROR_CODES: frozenset = frozenset(
    {
        "research.no_evidence",
        "research.query_failed",
        "credits.unavailable",
        "pricing.admissions_paused",
        "rate_limited",
    }
)


def is_retryable_error(error_code: Optional[str]) -> bool:
    """True when `error_code` (from a status, create or webhook body) is worth retrying."""
    return error_code is not None and error_code in RETRYABLE_ERROR_CODES


