"""
Workflows Client for Valyu SDK

Workflows are templated DeepResearch starting points — Valyu-curated or
created by your org — with typed {variable} placeholders and version history.
Run one by passing workflow_id (the slug) to deepresearch.create().
"""

from typing import Optional, List, Dict, Any, Literal
from valyu._errors import error_message
from valyu.types.workflows import (
    Workflow,
    WorkflowDeleteResponse,
    WorkflowPreviewResponse,
    WorkflowResponse,
    WorkflowsListResponse,
    WorkflowVersionsResponse,
)


class WorkflowsClient:
    """Workflows API client."""

    def __init__(self, parent):
        """Initialize with parent Valyu client."""
        self._parent = parent
        self._base_url = parent.base_url
        self._headers = parent.headers
        self._session = parent._session

    @staticmethod
    def _error_message(data: Dict[str, Any], status_code: int) -> str:
        return error_message(data, status_code)

    def list(
        self,
        vertical: Optional[str] = None,
        scope: Optional[Literal["valyu", "org", "all"]] = None,
        q: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        expand: Optional[bool] = None,
    ) -> WorkflowsListResponse:
        """
        List workflows available to your org.

        Args:
            vertical: Filter by vertical (e.g. "finance")
            scope: "valyu" for curated workflows only, "org" for your org's
                   workflows only, "all" for both (default)
            q: Free-text search over title/description
            tags: Filter by tags
            limit: Max results (default 50, max 100)
            expand: Include full template fields (prompt, strategy, report_format, tools)

        Returns:
            WorkflowsListResponse with workflows, total, and available verticals
        """
        try:
            params: Dict[str, Any] = {}
            if vertical:
                params["vertical"] = vertical
            if scope:
                params["scope"] = scope
            if q:
                params["q"] = q
            if tags:
                params["tags"] = ",".join(tags)
            if limit is not None:
                params["limit"] = limit
            if expand:
                params["expand"] = "true"

            response = self._session.get(
                f"{self._base_url}/workflows",
                params=params,
            )
            data = response.json()

            if not response.ok:
                return WorkflowsListResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowsListResponse(success=True, **data)

        except Exception as e:
            return WorkflowsListResponse(success=False, error=str(e))

    def get(
        self,
        slug: str,
        version: Optional[int] = None,
    ) -> WorkflowResponse:
        """
        Get a workflow's full detail, including its template.

        Args:
            slug: Workflow slug
            version: Specific version to fetch (defaults to the current version)

        Returns:
            WorkflowResponse with the full workflow detail
        """
        try:
            params: Dict[str, Any] = {}
            if version is not None:
                params["version"] = version

            response = self._session.get(
                f"{self._base_url}/workflows/{slug}",
                params=params,
            )
            data = response.json()

            if not response.ok:
                return WorkflowResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowResponse(success=True, workflow=Workflow(**data))

        except Exception as e:
            return WorkflowResponse(success=False, error=str(e))

    def versions(self, slug: str) -> WorkflowVersionsResponse:
        """
        List a workflow's version history.

        Args:
            slug: Workflow slug

        Returns:
            WorkflowVersionsResponse with version summaries (newest first)
        """
        try:
            response = self._session.get(
                f"{self._base_url}/workflows/{slug}/versions",
            )
            data = response.json()

            if not response.ok:
                return WorkflowVersionsResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowVersionsResponse(success=True, **data)

        except Exception as e:
            return WorkflowVersionsResponse(success=False, error=str(e))

    def preview(
        self,
        slug: str,
        workflow_params: Optional[Dict[str, Any]] = None,
        workflow_version: Optional[int] = None,
    ) -> WorkflowPreviewResponse:
        """
        Resolve a workflow's template with params without creating a task.

        Useful for showing the exact prompt/strategy a run would use.

        Args:
            slug: Workflow slug
            workflow_params: Values for the workflow's variables
            workflow_version: Specific version to resolve (defaults to current)

        Returns:
            WorkflowPreviewResponse with the resolved template
        """
        try:
            payload: Dict[str, Any] = {}
            if workflow_params is not None:
                payload["workflow_params"] = workflow_params
            if workflow_version is not None:
                payload["workflow_version"] = workflow_version

            response = self._session.post(
                f"{self._base_url}/workflows/{slug}/preview",
                json=payload,
            )
            data = response.json()

            if not response.ok:
                return WorkflowPreviewResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowPreviewResponse(success=True, **data)

        except Exception as e:
            return WorkflowPreviewResponse(success=False, error=str(e))

    def create(
        self,
        slug: str,
        title: str,
        version: Dict[str, Any],
        subtitle: Optional[str] = None,
        description: Optional[str] = None,
        vertical: Optional[str] = None,
        tags: Optional[List[str]] = None,
        icon: Optional[str] = None,
    ) -> WorkflowResponse:
        """
        Create a new workflow for your org.

        Args:
            slug: URL-safe identifier (lowercase letters, digits, hyphens)
            title: Display title
            version: Template body. Required: prompt, strategy, report_format.
                     Optional: variables, deliverables, tools, recommended_mode,
                     estimated_time, changelog. Template fields may reference
                     {variables} declared in variables[].
            subtitle: Short subtitle
            description: Longer description
            vertical: Vertical grouping (e.g. "finance")
            tags: Tags for filtering
            icon: Icon identifier

        Returns:
            WorkflowResponse with the created workflow detail
        """
        try:
            payload: Dict[str, Any] = {
                "slug": slug,
                "title": title,
                "version": version,
            }
            if subtitle is not None:
                payload["subtitle"] = subtitle
            if description is not None:
                payload["description"] = description
            if vertical is not None:
                payload["vertical"] = vertical
            if tags is not None:
                payload["tags"] = tags
            if icon is not None:
                payload["icon"] = icon

            response = self._session.post(
                f"{self._base_url}/workflows",
                json=payload,
            )
            data = response.json()

            if not response.ok:
                return WorkflowResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowResponse(success=True, workflow=Workflow(**data))

        except Exception as e:
            return WorkflowResponse(success=False, error=str(e))

    def update(
        self,
        slug: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        description: Optional[str] = None,
        vertical: Optional[str] = None,
        tags: Optional[List[str]] = None,
        icon: Optional[str] = None,
        version: Optional[Dict[str, Any]] = None,
        set_current: Optional[bool] = None,
    ) -> WorkflowResponse:
        """
        Update a workflow's metadata and/or publish a new template version.

        Only workflows owned by your org can be updated; Valyu-curated
        workflows are read-only. Versions are append-only — passing a version
        body creates the next version (changelog required).

        Args:
            slug: Workflow slug
            title: New title
            subtitle: New subtitle
            description: New description
            vertical: New vertical
            tags: Replacement tags
            icon: New icon
            version: New template body (same shape as create; changelog required)
            set_current: Whether the new version becomes current (default True)

        Returns:
            WorkflowResponse with the updated workflow detail
        """
        try:
            payload: Dict[str, Any] = {}
            if title is not None:
                payload["title"] = title
            if subtitle is not None:
                payload["subtitle"] = subtitle
            if description is not None:
                payload["description"] = description
            if vertical is not None:
                payload["vertical"] = vertical
            if tags is not None:
                payload["tags"] = tags
            if icon is not None:
                payload["icon"] = icon
            if version is not None:
                payload["version"] = version
            if set_current is not None:
                payload["set_current"] = set_current

            response = self._session.patch(
                f"{self._base_url}/workflows/{slug}",
                json=payload,
            )
            data = response.json()

            if not response.ok:
                return WorkflowResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowResponse(success=True, workflow=Workflow(**data))

        except Exception as e:
            return WorkflowResponse(success=False, error=str(e))

    def delete(self, slug: str) -> WorkflowDeleteResponse:
        """
        Delete a workflow owned by your org (soft delete).

        Args:
            slug: Workflow slug

        Returns:
            WorkflowDeleteResponse with the deletion timestamp
        """
        try:
            response = self._session.delete(
                f"{self._base_url}/workflows/{slug}",
            )
            data = response.json()

            if not response.ok:
                return WorkflowDeleteResponse(
                    success=False,
                    error=self._error_message(data, response.status_code),
                )

            return WorkflowDeleteResponse(success=True, **data)

        except Exception as e:
            return WorkflowDeleteResponse(success=False, error=str(e))
