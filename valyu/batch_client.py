"""
Batch Client for Valyu SDK
"""

import time
import requests
from typing import Optional, List, Literal, Union, Dict, Any, Callable
from valyu.types.deepresearch import (
    DeepResearchMode,
    DeepResearchStatus,
    BatchStatus,
    BatchTaskInput,
    BatchCreateResponse,
    BatchAddTasksResponse,
    BatchStatusResponse,
    BatchTasksListResponse,
    BatchCancelResponse,
    BatchListResponse,
    SearchConfig,
)


class BatchClient:
    """Batch API client for managing bulk deep research tasks."""

    def __init__(self, parent):
        """Initialize with parent Valyu client."""
        self._parent = parent
        self._base_url = parent.base_url
        self._headers = parent.headers

    def create(
        self,
        name: Optional[str] = None,
        mode: Optional[Literal["lite", "standard", "heavy", "fast"]] = None,
        model: Optional[Literal["lite", "standard", "heavy", "fast"]] = None,
        output_formats: Optional[
            List[Union[Literal["markdown", "pdf", "toon"], Dict[str, Any]]]
        ] = None,
        search: Optional[Union[SearchConfig, Dict[str, Any]]] = None,
        webhook_url: Optional[str] = None,
        brand_collection_id: Optional[str] = None,
        metadata: Optional[Dict[str, Union[str, int, bool]]] = None,
    ) -> BatchCreateResponse:
        """
        Create a new batch for bulk deep research tasks.

        Args:
            name: Optional name for the batch
            mode: Research mode - "standard" (default, $0.50 per task), "heavy" (comprehensive, $1.50 per task),
                  "fast" (lower cost, faster completion), or "lite" (deprecated, use "fast" instead)
            model: Research mode (backward compatibility - use 'mode' instead) - "standard" (default), "heavy", "fast", or "lite"
            output_formats: Default output formats - ["markdown"], ["pdf"], ["toon"], or a JSON schema object.
                           When using a JSON schema, the output will be structured JSON instead of markdown.
                           Cannot mix JSON schema with "markdown"/"pdf". "toon" requires a JSON schema.
            search: Default search configuration (type, sources, dates, category).
                   Can be a SearchConfig object or dict with search parameters:
                   - search_type: "all" (default), "web", or "proprietary"
                   - included_sources: List of source types to include ("web", "academic", "finance",
                     "patent", "transportation", "politics", "legal")
                   - excluded_sources: List of source types to exclude
                   - start_date: Start date filter in ISO format (YYYY-MM-DD), e.g., "2024-01-01"
                   - end_date: End date filter in ISO format (YYYY-MM-DD), e.g., "2024-12-31"
                   - category: Category filter for results
            webhook_url: HTTPS webhook URL for completion notification
            brand_collection_id: Brand collection to apply to all deliverables
            metadata: Custom metadata (key-value pairs)

        Returns:
            BatchCreateResponse with batch ID and status
        """
        try:
            # Determine which field to use (prefer mode over model)
            research_mode = (
                mode
                if mode is not None
                else (model if model is not None else "standard")
            )

            # Build payload - prefer mode, but send model if only model was provided
            payload = {
                "mode": research_mode,  # Always send mode (preferred)
            }
            # Also send model if it was explicitly provided and mode was not (for backward compatibility)
            if model is not None and mode is None:
                payload["model"] = model

            # Add optional fields
            if name:
                payload["name"] = name
            if output_formats:
                payload["output_formats"] = output_formats
            if search:
                if isinstance(search, SearchConfig):
                    search_dict = search.dict(exclude_none=True)
                else:
                    search_dict = search
                payload["search"] = search_dict
            if webhook_url:
                payload["webhook_url"] = webhook_url
            if brand_collection_id:
                payload["brand_collection_id"] = brand_collection_id
            if metadata:
                payload["metadata"] = metadata

            response = requests.post(
                f"{self._base_url}/deepresearch/batches",
                json=payload,
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return BatchCreateResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return BatchCreateResponse(success=True, **data)

        except Exception as e:
            return BatchCreateResponse(
                success=False,
                error=str(e),
            )

    def add_tasks(
        self,
        batch_id: str,
        tasks: List[Union[BatchTaskInput, Dict[str, Any]]],
    ) -> BatchAddTasksResponse:
        """
        Add tasks to an existing batch.

        Args:
            batch_id: Batch ID to add tasks to
            tasks: List of task inputs (each with input, optional strategy, urls, metadata)

        Returns:
            BatchAddTasksResponse with number of tasks added
        """
        try:
            if not tasks:
                return BatchAddTasksResponse(
                    success=False,
                    error="tasks list cannot be empty",
                )

            # Convert tasks to dict format
            task_dicts = [
                t.dict(exclude_none=True) if isinstance(t, BatchTaskInput) else t
                for t in tasks
            ]

            payload = {"tasks": task_dicts}

            response = requests.post(
                f"{self._base_url}/deepresearch/batches/{batch_id}/tasks",
                json=payload,
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return BatchAddTasksResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return BatchAddTasksResponse(success=True, **data)

        except Exception as e:
            return BatchAddTasksResponse(
                success=False,
                error=str(e),
            )

    def status(self, batch_id: str) -> BatchStatusResponse:
        """
        Get the status of a batch.

        Args:
            batch_id: Batch ID to check

        Returns:
            BatchStatusResponse with current batch status and task counts
        """
        try:
            response = requests.get(
                f"{self._base_url}/deepresearch/batches/{batch_id}",
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                if isinstance(data, dict):
                    return BatchStatusResponse(
                        success=False,
                        error=data.get("error", f"HTTP Error: {response.status_code}"),
                    )
                else:
                    return BatchStatusResponse(
                        success=False,
                        error=f"HTTP Error: {response.status_code}",
                    )

            # API returns batch object directly, wrap it in the expected structure
            return BatchStatusResponse(success=True, batch=data)

        except Exception as e:
            return BatchStatusResponse(
                success=False,
                error=str(e),
            )

    def list_tasks(
        self,
        batch_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        last_key: Optional[str] = None,
    ) -> BatchTasksListResponse:
        """
        List all tasks in a batch with optional filtering and pagination.

        Args:
            batch_id: Batch ID to list tasks for
            status: Filter by status: "queued", "running", "completed", "failed", or "cancelled"
            limit: Maximum number of tasks to return
            last_key: Pagination token from previous response

        Returns:
            BatchTasksListResponse with list of tasks
        """
        try:
            # Build query parameters
            params = {}
            if status:
                params["status"] = status
            if limit is not None:
                params["limit"] = limit
            if last_key:
                params["last_key"] = last_key

            response = requests.get(
                f"{self._base_url}/deepresearch/batches/{batch_id}/tasks",
                headers=self._headers,
                params=params if params else None,
            )

            data = response.json()

            if not response.ok:
                return BatchTasksListResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return BatchTasksListResponse(success=True, **data)

        except Exception as e:
            return BatchTasksListResponse(
                success=False,
                error=str(e),
            )

    def cancel(self, batch_id: str) -> BatchCancelResponse:
        """
        Cancel a batch and all its pending/running tasks.

        Args:
            batch_id: Batch ID to cancel

        Returns:
            BatchCancelResponse
        """
        try:
            response = requests.post(
                f"{self._base_url}/deepresearch/batches/{batch_id}/cancel",
                json={},
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                return BatchCancelResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return BatchCancelResponse(success=True, **data)

        except Exception as e:
            return BatchCancelResponse(
                success=False,
                error=str(e),
            )

    def list(
        self,
        limit: Optional[int] = None,
    ) -> BatchListResponse:
        """
        List all batches.

        Args:
            limit: Maximum number of batches to return (optional, no limit if not specified)

        Returns:
            BatchListResponse with list of batches
        """
        try:
            # Build query parameters
            params = {}
            if limit is not None:
                params["limit"] = limit

            response = requests.get(
                f"{self._base_url}/deepresearch/batches",
                params=params if params else None,
                headers=self._headers,
            )

            data = response.json()

            if not response.ok:
                # Handle error response
                if isinstance(data, dict):
                    return BatchListResponse(
                        success=False,
                        error=data.get("error", f"HTTP Error: {response.status_code}"),
                    )
                else:
                    return BatchListResponse(
                        success=False,
                        error=f"HTTP Error: {response.status_code}",
                    )

            # Handle both dict with "batches" key and direct list response
            if isinstance(data, list):
                batches = data
            elif isinstance(data, dict):
                batches = data.get("batches", [])
            else:
                batches = []

            return BatchListResponse(success=True, batches=batches)

        except Exception as e:
            return BatchListResponse(
                success=False,
                error=str(e),
            )

    def wait_for_completion(
        self,
        batch_id: str,
        poll_interval: int = 10,
        max_wait_time: int = 14400,
        on_progress: Optional[Callable[[BatchStatusResponse], None]] = None,
    ) -> BatchStatusResponse:
        """
        Wait for a batch to complete with automatic polling.

        Args:
            batch_id: Batch ID to wait for
            poll_interval: Seconds between polls (default: 10)
            max_wait_time: Maximum wait time in seconds (default: 14400 = 4 hours)
            on_progress: Callback for progress updates

        Returns:
            Final batch status

        Raises:
            TimeoutError: If max_wait_time is exceeded
            ValueError: If batch fails or is cancelled
        """
        start_time = time.time()

        while True:
            status = self.status(batch_id)

            if not status.success:
                raise ValueError(f"Failed to get status: {status.error}")

            # Notify progress callback
            if on_progress:
                on_progress(status)

            # Terminal states
            if status.batch and status.batch.status in [
                BatchStatus.COMPLETED,
                BatchStatus.COMPLETED_WITH_ERRORS,
            ]:
                return status
            elif status.batch and status.batch.status == BatchStatus.CANCELLED:
                raise ValueError("Batch was cancelled")

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise TimeoutError(
                    f"Batch did not complete within {max_wait_time} seconds"
                )

            # Wait before next poll
            time.sleep(poll_interval)

    def create_and_run(
        self,
        tasks: List[Union[BatchTaskInput, Dict[str, Any]]],
        name: Optional[str] = None,
        mode: Optional[Literal["lite", "standard", "heavy", "fast"]] = None,
        model: Optional[Literal["lite", "standard", "heavy", "fast"]] = None,
        output_formats: Optional[
            List[Union[Literal["markdown", "pdf", "toon"], Dict[str, Any]]]
        ] = None,
        search: Optional[Union[SearchConfig, Dict[str, Any]]] = None,
        webhook_url: Optional[str] = None,
        brand_collection_id: Optional[str] = None,
        metadata: Optional[Dict[str, Union[str, int, bool]]] = None,
        wait: bool = False,
        poll_interval: int = 10,
        max_wait_time: int = 14400,
        on_progress: Optional[Callable[[BatchStatusResponse], None]] = None,
    ) -> BatchCreateResponse:
        """
        Convenience method to create a batch and add tasks in one call.

        Args:
            tasks: List of task inputs
            name: Optional name for the batch
            mode: Research mode - "standard" (default, $0.50 per task), "heavy" (comprehensive, $1.50 per task),
                  "fast" (lower cost, faster completion $0.10 per task), or "lite" (deprecated, use "fast" instead)
            model: Research mode (backward compatibility - use 'mode' instead) - "standard" (default), "heavy", "fast", or "lite"
            output_formats: Default output formats - ["markdown"], ["pdf"], ["toon"], or a JSON schema object.
                           When using a JSON schema, the output will be structured JSON instead of markdown.
                           Cannot mix JSON schema with "markdown"/"pdf". "toon" requires a JSON schema.
            search: Default search configuration (type, sources, dates, category).
                   Can be a SearchConfig object or dict with search parameters:
                   - search_type: "all" (default), "web", or "proprietary"
                   - included_sources: List of source types to include ("web", "academic", "finance",
                     "patent", "transportation", "politics", "legal")
                   - excluded_sources: List of source types to exclude
                   - start_date: Start date filter in ISO format (YYYY-MM-DD), e.g., "2024-01-01"
                   - end_date: End date filter in ISO format (YYYY-MM-DD), e.g., "2024-12-31"
                   - category: Category filter for results
            webhook_url: HTTPS webhook URL for completion notification
            brand_collection_id: Brand collection to apply to all deliverables
            metadata: Custom metadata (key-value pairs)
            wait: If True, wait for batch to complete before returning
            poll_interval: Seconds between polls when waiting
            max_wait_time: Maximum wait time in seconds
            on_progress: Callback for progress updates

        Returns:
            BatchCreateResponse with batch ID
        """
        # Create batch
        batch_response = self.create(
            name=name,
            mode=mode,
            model=model,
            output_formats=output_formats,
            search=search,
            webhook_url=webhook_url,
            brand_collection_id=brand_collection_id,
            metadata=metadata,
        )

        if not batch_response.success or not batch_response.batch_id:
            return batch_response

        # Add tasks
        add_response = self.add_tasks(batch_response.batch_id, tasks)

        if not add_response.success:
            # Return error but include batch_id
            return BatchCreateResponse(
                success=False,
                batch_id=batch_response.batch_id,
                error=f"Failed to add tasks: {add_response.error}",
            )

        # Wait if requested
        if wait:
            try:
                self.wait_for_completion(
                    batch_response.batch_id,
                    poll_interval=poll_interval,
                    max_wait_time=max_wait_time,
                    on_progress=on_progress,
                )
            except Exception as e:
                # Return error but include batch_id
                return BatchCreateResponse(
                    success=False,
                    batch_id=batch_response.batch_id,
                    error=f"Error while waiting: {str(e)}",
                )

        return batch_response
