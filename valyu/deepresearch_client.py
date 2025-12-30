"""
DeepResearch Client for Valyu SDK
"""
import time
import requests
from typing import Optional, List, Literal, Union, Dict, Any, Callable
from valyu.types.deepresearch import (
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
        input: str,
        model: Literal["lite", "heavy"] = "lite",
        output_formats: Optional[List[Union[Literal["markdown", "pdf"], Dict[str, Any]]]] = None,
        strategy: Optional[str] = None,
        search: Optional[Union[SearchConfig, Dict[str, Any]]] = None,
        urls: Optional[List[str]] = None,
        files: Optional[List[Union[FileAttachment, Dict[str, Any]]]] = None,
        deliverables: Optional[List[Union[str, Deliverable, Dict[str, Any]]]] = None,
        mcp_servers: Optional[List[Union[MCPServerConfig, Dict[str, Any]]]] = None,
        code_execution: bool = True,
        previous_reports: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Union[str, int, bool]]] = None,
    ) -> DeepResearchCreateResponse:
        """
        Create a new deep research task.

        Args:
            input: Research query or task description
            model: Research model - "lite" (fast, Haiku) or "heavy" (thorough, Sonnet)
            output_formats: Output formats - ["markdown"], ["markdown", "pdf"], or a JSON schema object.
                           When using a JSON schema, the output will be structured JSON instead of markdown.
                           Cannot mix JSON schema with markdown/pdf - use one or the other.
            strategy: Natural language strategy for the research
            search: Search configuration (type, sources)
            urls: URLs to extract and analyze
            files: File attachments (PDFs, images)
            deliverables: Additional file outputs to generate (CSV, Excel, PowerPoint, Word, PDF). Max 10.
                         Can be simple strings or Deliverable objects with detailed configuration.
            mcp_servers: MCP server configurations for custom tools
            code_execution: Enable/disable code execution (default: True)
            previous_reports: Previous report IDs for context (max 3)
            webhook_url: HTTPS webhook URL for completion notification
            metadata: Custom metadata (key-value pairs)

        Returns:
            DeepResearchCreateResponse with task ID and status
        """
        try:
            # Validation
            if not input or not input.strip():
                return DeepResearchCreateResponse(
                    success=False,
                    error="input is required and cannot be empty",
                )

            # Build payload
            payload = {
                "input": input,
                "model": model,
                "output_formats": output_formats or ["markdown"],
                "code_execution": code_execution,
            }

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
                    f.dict() if isinstance(f, FileAttachment) else f for f in files
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
        api_key_id: str,
        limit: int = 10,
    ) -> DeepResearchListResponse:
        """
        List all deep research tasks.

        Args:
            api_key_id: API key ID for filtering tasks
            limit: Maximum number of tasks to return (default: 10, max: 100)

        Returns:
            DeepResearchListResponse with list of tasks
        """
        try:
            response = requests.get(
                f"{self._base_url}/deepresearch/list?api_key_id={api_key_id}&limit={limit}",
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
