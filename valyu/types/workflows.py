"""
Workflow types for Valyu SDK

Workflows are templated DeepResearch starting points. A workflow defines a
prompt/strategy/report format with typed {variable} placeholders; running it
with workflow_params expands the template into a normal DeepResearch task.
"""

from pydantic import BaseModel
from typing import Optional, List, Literal


WorkflowMode = Literal["fast", "standard", "heavy", "max"]

WorkflowVariableType = Literal["text", "textarea", "number", "date", "enum"]


class WorkflowVariableValidation(BaseModel):
    """Validation rules for a workflow variable."""

    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[str]] = None


class WorkflowVariable(BaseModel):
    """A typed {variable} placeholder in a workflow template."""

    key: str
    label: Optional[str] = None
    type: Optional[WorkflowVariableType] = None
    required: Optional[bool] = None
    placeholder: Optional[str] = None
    help: Optional[str] = None
    examples: Optional[List[str]] = None
    validation: Optional[WorkflowVariableValidation] = None


class WorkflowDeliverable(BaseModel):
    """A file deliverable the workflow generates (CSV, Excel, PowerPoint, ...)."""

    type: str
    description: Optional[str] = None


class WorkflowTools(BaseModel):
    """Optional tools the workflow enables for the research agent."""

    code_execution: Optional[bool] = None
    screenshots: Optional[bool] = None
    browser_use: Optional[bool] = None
    charts: Optional[bool] = None


class Workflow(BaseModel):
    """A workflow as returned by list/get endpoints."""

    slug: str
    version: Optional[int] = None
    vertical: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    popular: Optional[bool] = None
    recommended_mode: Optional[WorkflowMode] = None
    estimated_time: Optional[str] = None
    is_valyu: Optional[bool] = None
    owner_org_id: Optional[str] = None
    variables: Optional[List[WorkflowVariable]] = None
    deliverables: Optional[List[WorkflowDeliverable]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Template fields — present on detail responses and list with expand=True
    prompt: Optional[str] = None
    strategy: Optional[str] = None
    report_format: Optional[str] = None
    tools: Optional[WorkflowTools] = None
    changelog: Optional[str] = None


class WorkflowVersionSummary(BaseModel):
    """A single entry in a workflow's version history."""

    version: int
    recommended_mode: Optional[WorkflowMode] = None
    estimated_time: Optional[str] = None
    changelog: Optional[str] = None
    created_at: Optional[str] = None
    is_current: Optional[bool] = None


class WorkflowRunInfo(BaseModel):
    """Workflow attribution on a DeepResearch task created from a workflow."""

    slug: Optional[str] = None
    version: Optional[int] = None


class ResolvedWorkflowTemplate(BaseModel):
    """The expanded template returned by preview."""

    input: Optional[str] = None
    research_strategy: Optional[str] = None
    report_format: Optional[str] = None
    deliverables: Optional[List[WorkflowDeliverable]] = None
    mode: Optional[WorkflowMode] = None
    tools: Optional[WorkflowTools] = None


class WorkflowsListResponse(BaseModel):
    """Response from listing workflows."""

    success: bool
    workflows: Optional[List[Workflow]] = None
    total: Optional[int] = None
    next_cursor: Optional[str] = None
    verticals: Optional[List[str]] = None
    error: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Response from getting, creating, or updating a workflow."""

    success: bool
    workflow: Optional[Workflow] = None
    error: Optional[str] = None


class WorkflowVersionsResponse(BaseModel):
    """Response from listing a workflow's version history."""

    success: bool
    slug: Optional[str] = None
    versions: Optional[List[WorkflowVersionSummary]] = None
    error: Optional[str] = None


class WorkflowPreviewResponse(BaseModel):
    """Response from previewing a workflow with params (no task created)."""

    success: bool
    workflow: Optional[WorkflowRunInfo] = None
    resolved: Optional[ResolvedWorkflowTemplate] = None
    estimated_credits: Optional[float] = None
    error: Optional[str] = None


class WorkflowDeleteResponse(BaseModel):
    """Response from deleting a workflow."""

    success: bool
    slug: Optional[str] = None
    deleted_at: Optional[str] = None
    error: Optional[str] = None
