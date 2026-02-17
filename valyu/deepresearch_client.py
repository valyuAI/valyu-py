"""
DeepResearch Client for Valyu SDK
"""

import time
import requests
from typing import Optional, List, Literal, Union, Dict, Any, Callable
from valyu.types.deepresearch import (
    AlertEmailConfig,
    DeepResearchMode,
    DeepResearchStatus,
    FileAttachment,
    MCPServerConfig,
    Deliverable,
    SearchConfig,
    DeepResearchCreateResponse,
    DeepResearchStatusResponse,
    DeepResearchListResponse,
    DeepResearchUpdateResponse,
    DeepResearchCancelResponse,
    DeepResearchDeleteResponse,
    DeepResearchTogglePublicResponse,
)


class DeepResearchClient:
    """DeepResearch API client."""

    def __init__(self, parent):
        """Initialize with parent Valyu client."""
        self._parent = parent
        self._base_url = parent.base_url
        self._headers = parent.headers

    def create(
        self,
        query: Optional[str] = None,
        input: Optional[str] = None,
        mode: Optional[DeepResearchMode] = None,
        model: Optional[DeepResearchMode] = None,
        output_formats: Optional[
            List[Union[Literal["markdown", "pdf", "toon"], Dict[str, Any]]]
        ] = None,
        strategy: Optional[str] = None,
        search: Optional[Union[SearchConfig, Dict[str, Any]]] = None,
        urls: Optional[List[str]] = None,
        files: Optional[List[Union[FileAttachment, Dict[str, Any]]]] = None,
        deliverables: Optional[List[Union[str, Deliverable, Dict[str, Any]]]] = None,
        mcp_servers: Optional[List[Union[MCPServerConfig, Dict[str, Any]]]] = None,
        code_execution: bool = True,
        previous_reports: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        alert_email: Optional[Union[str, "AlertEmailConfig", Dict[str, str]]] = None,
        brand_collection_id: Optional[str] = None,
        metadata: Optional[Dict[str, Union[str, int, bool]]] = None,
    ) -> DeepResearchCreateResponse:
        """
        Create a new deep research task.

        Args:
            query: Research query or task description (preferred)
            input: Research query or task description (deprecated, use query instead)
            mode: Research mode - "fast", "standard" (default), "heavy", or "max".
                  Preferred over model parameter.
            model: Research mode (backward compatibility - use 'mode' instead) - "standard" (default),
                  "heavy", "fast", "max", or "lite" (deprecated, maps to "standard")
            output_formats: Output formats - ["markdown"], ["markdown", "pdf"], or a JSON schema object.
                           When using a JSON schema, the output will be structured JSON instead of markdown.
                           Cannot mix JSON schema with markdown/pdf - use one or the other.
            strategy: Natural language strategy for the research
            search: Search configuration (type, sources, dates, category).
                   Can be a SearchConfig object or dict with search parameters:
                   - search_type: "all" (default), "web", or "proprietary"
                   - included_sources: List of source types to include ("web", "academic", "finance",
                     "patent", "transportation", "politics", "legal")
                   - excluded_sources: List of source types to exclude
                   - start_date: Start date filter in ISO format (YYYY-MM-DD), e.g., "2024-01-01"
                   - end_date: End date filter in ISO format (YYYY-MM-DD), e.g., "2024-12-31"
                   - category: Category filter for results
            urls: URLs to extract and analyze
            files: File attachments (PDFs, images)
            deliverables: Additional file outputs to generate (CSV, Excel, PowerPoint, Word, PDF). Max 10.
                         Can be simple strings or Deliverable objects with detailed configuration.
            mcp_servers: MCP server configurations for custom tools
            code_execution: Enable/disable code execution (default: True)
            previous_reports: Previous report IDs for context (max 3)
            webhook_url: HTTPS webhook URL for completion notification
            alert_email: Email for completion alerts. Can be a string (email address) or
                        a dict/AlertEmailConfig with 'email' and optional 'custom_url'.
                        custom_url must contain {id} which is replaced with the task ID.
            brand_collection_id: Brand collection to apply to all deliverables
            metadata: Custom metadata (key-value pairs)

        Returns:
            DeepResearchCreateResponse with task ID and status
        """
        try:
            # Determine which field to use (prefer query over input)
            research_query = query if query else input

            # Validation
            if not research_query or not research_query.strip():
                return DeepResearchCreateResponse(
                    success=False,
                    error="'query' is required and cannot be empty",
                )

            # Determine which mode to use (prefer mode over model)
            research_mode = (
                mode
                if mode is not None
                else (model if model is not None else "standard")
            )
            # Map "lite" to "standard" for backward compatibility
            if research_mode == "lite":
                research_mode = "standard"

            # Build payload - always send query (preferred), but also send input for backward compatibility
            # Infrastructure accepts both, but we prefer query
            payload = {
                "query": research_query,  # Always send query (preferred field)
                "mode": research_mode,  # Always send mode (preferred field)
                "output_formats": output_formats or ["markdown"],
                "code_execution": code_execution,
            }
            # Also send input if it was provided (for backward compatibility with older API versions)
            if input:
                payload["input"] = input
            # Also send model if it was explicitly provided (for backward compatibility)
            if model is not None:
                payload["model"] = model if model != "lite" else "standard"

            # Add optional fields
            if strategy:
                payload["strategy"] = strategy
            if search:
                if isinstance(search, SearchConfig):
                    search_dict = search.dict(exclude_none=True)
                else:
                    search_dict = search
                payload["search"] = search_dict
            if urls:
                payload["urls"] = urls
            if files:
                payload["files"] = [
                    (
                        f.model_dump(by_alias=True, exclude_none=True)
                        if isinstance(f, FileAttachment)
                        else f
                    )
                    for f in files
                ]
            if deliverables:
                payload["deliverables"] = [
                    d.dict(exclude_none=True) if isinstance(d, Deliverable) else d
                    for d in deliverables
                ]
            if mcp_servers:
                payload["mcp_servers"] = [
                    s.dict(exclude_none=True) if isinstance(s, MCPServerConfig) else s
                    for s in mcp_servers
                ]
            if previous_reports:
                payload["previous_reports"] = previous_reports
            if webhook_url:
                payload["webhook_url"] = webhook_url
            if alert_email is not None:
                if isinstance(alert_email, str):
                    payload["alert_email"] = alert_email
                elif isinstance(alert_email, AlertEmailConfig):
                    payload["alert_email"] = alert_email.model_dump(exclude_none=True)
                else:
                    payload["alert_email"] = alert_email
            if brand_collection_id:
                payload["brand_collection_id"] = brand_collection_id
            if metadata:
                payload["metadata"] = metadata

            response = requests.post(
                f"{self._base_url}/deepresearch/tasks",
                json=payload,
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchCreateResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchCreateResponse(success=True, **data)

        except Exception as e:
            return DeepResearchCreateResponse(
                success=False,
                error=str(e),
            )

    def status(self, task_id: str) -> DeepResearchStatusResponse:
        """
        Get the status of a deep research task.

        Args:
            task_id: Task ID to check

        Returns:
            DeepResearchStatusResponse with current status
        """
        try:
            response = requests.get(
                f"{self._base_url}/deepresearch/tasks/{task_id}/status",
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchStatusResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchStatusResponse(success=True, **data)

        except Exception as e:
            return DeepResearchStatusResponse(
                success=False,
                error=str(e),
            )

    def wait(
        self,
        task_id: str,
        poll_interval: int = 5,
        max_wait_time: int = 7200,
        on_progress: Optional[Callable[[DeepResearchStatusResponse], None]] = None,
    ) -> DeepResearchStatusResponse:
        """
        Wait for a task to complete with automatic polling.

        Args:
            task_id: Task ID to wait for
            poll_interval: Seconds between polls (default: 5)
            max_wait_time: Maximum wait time in seconds (default: 7200)
            on_progress: Callback for progress updates

        Returns:
            Final task status

        Raises:
            TimeoutError: If max_wait_time is exceeded
            ValueError: If task fails or is cancelled
        """
        start_time = time.time()

        while True:
            status = self.status(task_id)

            if not status.success:
                raise ValueError(f"Failed to get status: {status.error}")

            # Notify progress callback
            if on_progress:
                on_progress(status)

            # Terminal states
            if status.status == DeepResearchStatus.COMPLETED:
                return status
            elif status.status == DeepResearchStatus.FAILED:
                raise ValueError(f"Task failed: {status.error}")
            elif status.status == DeepResearchStatus.CANCELLED:
                raise ValueError("Task was cancelled")

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise TimeoutError(
                    f"Task did not complete within {max_wait_time} seconds"
                )

            # Wait before next poll
            time.sleep(poll_interval)

    def stream(
        self,
        task_id: str,
        on_message: Optional[Callable[[Any], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[DeepResearchStatusResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """
        Stream real-time updates for a task.

        Args:
            task_id: Task ID to stream
            on_message: Callback for new messages
            on_progress: Callback for progress updates (current, total)
            on_complete: Callback when task completes
            on_error: Callback for errors
        """
        last_message_count = 0

        while True:
            try:
                status = self.status(task_id)

                if not status.success:
                    if on_error:
                        on_error(ValueError(status.error))
                    return

                # Progress updates
                if status.progress and on_progress:
                    on_progress(
                        status.progress.current_step,
                        status.progress.total_steps,
                    )

                # New messages
                if status.messages and on_message:
                    new_messages = status.messages[last_message_count:]
                    for msg in new_messages:
                        on_message(msg)
                    last_message_count = len(status.messages)

                # Terminal states
                if status.status == DeepResearchStatus.COMPLETED:
                    if on_complete:
                        on_complete(status)
                    return
                elif status.status in [
                    DeepResearchStatus.FAILED,
                    DeepResearchStatus.CANCELLED,
                ]:
                    if on_error:
                        on_error(
                            ValueError(f"Task {status.status.value}: {status.error}")
                        )
                    return

                # Wait before next poll
                time.sleep(5)

            except Exception as e:
                if on_error:
                    on_error(e)
                raise

    def list(
        self,
        limit: Optional[int] = None,
    ) -> DeepResearchListResponse:
        """
        List all deep research tasks for the authenticated API key.

        Args:
            limit: Maximum number of tasks to return (1-100, default: all if not specified)

        Returns:
            DeepResearchListResponse with list of tasks
        """
        try:
            # Build query parameters
            params = {}
            if limit is not None:
                params["limit"] = limit

            response = requests.get(
                f"{self._base_url}/deepresearch/list",
                params=params,
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchListResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchListResponse(success=True, data=data)

        except Exception as e:
            return DeepResearchListResponse(
                success=False,
                error=str(e),
            )

    def update(self, task_id: str, instruction: str) -> DeepResearchUpdateResponse:
        """
        Add a follow-up instruction to a running task.

        Args:
            task_id: Task ID to update
            instruction: Follow-up instruction

        Returns:
            DeepResearchUpdateResponse
        """
        try:
            if not instruction or not instruction.strip():
                return DeepResearchUpdateResponse(
                    success=False,
                    error="instruction is required and cannot be empty",
                )

            response = requests.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/update",
                json={"instruction": instruction},
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchUpdateResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchUpdateResponse(success=True, **data)

        except Exception as e:
            return DeepResearchUpdateResponse(
                success=False,
                error=str(e),
            )

    def cancel(self, task_id: str) -> DeepResearchCancelResponse:
        """
        Cancel a running task.

        Args:
            task_id: Task ID to cancel

        Returns:
            DeepResearchCancelResponse
        """
        try:
            response = requests.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/cancel",
                json={},
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchCancelResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchCancelResponse(success=True, **data)

        except Exception as e:
            return DeepResearchCancelResponse(
                success=False,
                error=str(e),
            )

    def delete(self, task_id: str) -> DeepResearchDeleteResponse:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete

        Returns:
            DeepResearchDeleteResponse
        """
        try:
            response = requests.delete(
                f"{self._base_url}/deepresearch/tasks/{task_id}/delete",
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchDeleteResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchDeleteResponse(success=True, **data)

        except Exception as e:
            return DeepResearchDeleteResponse(
                success=False,
                error=str(e),
            )

    def get_assets(
        self, task_id: str, asset_id: str, token: Optional[str] = None
    ) -> bytes:
        """
        Get authenticated assets (images, charts, deliverables, PDFs) for a task.

        Args:
            task_id: The deepresearch_id of the task
            asset_id: The asset ID (image_id, deliverable id, or pdf_id)
            token: Optional asset access token (alternative to API key)

        Returns:
            Binary asset data (bytes)

        Raises:
            requests.HTTPError: If the request fails
            ValueError: If neither token nor API key is available
        """
        try:
            url = f"{self._base_url}/deepresearch/tasks/{task_id}/assets/{asset_id}"

            # Build headers - use API key if no token provided
            headers = {}
            if token:
                # Token is passed as query parameter, not header
                url += f"?token={token}"
            else:
                # Use API key from headers
                headers = self._headers.copy()

            response = requests.get(url, headers=headers)

            if not response.ok:
                error_data = (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )
                raise requests.HTTPError(
                    f"HTTP {response.status_code}: {error_data.get('error', response.text)}"
                )

            return response.content

        except requests.HTTPError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to get asset: {str(e)}")

    def toggle_public(
        self, task_id: str, is_public: bool
    ) -> DeepResearchTogglePublicResponse:
        """
        Toggle the public flag for a task.

        Args:
            task_id: Task ID
            is_public: Whether the task should be public

        Returns:
            DeepResearchTogglePublicResponse
        """
        try:
            response = requests.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/public",
                json={"public": is_public},
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchTogglePublicResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return DeepResearchTogglePublicResponse(success=True, **data)

        except Exception as e:
            return DeepResearchTogglePublicResponse(
                success=False,
                error=str(e),
            )
