"""
DeepResearch Client for Valyu SDK
"""

import time
import random
import requests
from typing import Optional, List, Literal, Union, Dict, Any, Callable
from valyu._errors import error_message as _error_message
from valyu.types.deepresearch import (
    AlertEmailConfig,
    DeepResearchMode,
    DeepResearchStatus,
    FileAttachment,
    MCPServerConfig,
    Deliverable,
    SearchConfig,
    HitlConfig,
    Interaction,
    DeepResearchTools,
    DeepResearchCreateResponse,
    DeepResearchStatusResponse,
    DeepResearchListResponse,
    DeepResearchUpdateResponse,
    DeepResearchCancelResponse,
    DeepResearchDeleteResponse,
    DeepResearchTogglePublicResponse,
    DeepResearchRespondResponse,
)


# Hard cap enforced by the create endpoint: the combined character length of
# research_strategy (or its legacy alias strategy) and report_format must not
# exceed this. The server rejects anything strictly greater with an HTTP 400,
# so exactly this value still passes.
MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH = 15000


# HTTP status codes that indicate a transient gateway/server/rate-limit
# condition rather than a definitive answer about the task. The status
# endpoint is idempotent and meant to be polled, so these are retried.
_TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class DeepResearchClient:
    """DeepResearch API client."""

    def __init__(self, parent):
        """Initialize with parent Valyu client."""
        self._parent = parent
        self._base_url = parent.base_url
        self._headers = parent.headers
        self._session = parent._session

    @staticmethod
    def _build_shared_fields(
        search=None,
        urls=None,
        files=None,
        deliverables=None,
        mcp_servers=None,
        previous_reports=None,
        webhook_url=None,
        alert_email=None,
        brand_collection_id=None,
        metadata=None,
        hitl=None,
        tools=None,
        code_execution=None,
    ) -> Dict[str, Any]:
        """
        Build the request fields that are valid for both freeform and workflow runs.

        Workflow templates supply the freeform fields (prompt, strategy, report
        format) but everything below is a per-run concern, so a workflow run
        accepts the same values a freeform run does. Request-body values win
        over the template server-side, except `tools`, which is merged.
        """
        fields: Dict[str, Any] = {}

        if tools is not None:
            fields["tools"] = (
                tools if isinstance(tools, dict) else tools.model_dump(exclude_none=True)
            )
        elif code_execution is not None:
            # Backward compatibility: top-level code_execution (deprecated)
            fields["code_execution"] = code_execution

        if search:
            fields["search"] = (
                search.model_dump(exclude_none=True)
                if isinstance(search, SearchConfig)
                else search
            )
        if urls:
            fields["urls"] = urls
        if files:
            fields["files"] = [
                (
                    f.model_dump(by_alias=True, exclude_none=True)
                    if isinstance(f, FileAttachment)
                    else f
                )
                for f in files
            ]
        if deliverables:
            fields["deliverables"] = [
                d.model_dump(exclude_none=True) if isinstance(d, Deliverable) else d
                for d in deliverables
            ]
        if mcp_servers:
            fields["mcp_servers"] = [
                s.model_dump(exclude_none=True) if isinstance(s, MCPServerConfig) else s
                for s in mcp_servers
            ]
        if previous_reports:
            fields["previous_reports"] = previous_reports
        if webhook_url:
            fields["webhook_url"] = webhook_url
        if alert_email is not None:
            if isinstance(alert_email, AlertEmailConfig):
                fields["alert_email"] = alert_email.model_dump(exclude_none=True)
            else:
                fields["alert_email"] = alert_email
        if brand_collection_id:
            fields["brand_collection_id"] = brand_collection_id
        if metadata:
            fields["metadata"] = metadata
        if hitl is not None:
            fields["hitl"] = (
                hitl.model_dump(exclude_none=True)
                if isinstance(hitl, HitlConfig)
                else hitl
            )

        return fields

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
        research_strategy: Optional[str] = None,
        report_format: Optional[str] = None,
        search: Optional[Union[SearchConfig, Dict[str, Any]]] = None,
        urls: Optional[List[str]] = None,
        files: Optional[List[Union[FileAttachment, Dict[str, Any]]]] = None,
        deliverables: Optional[List[Union[str, Deliverable, Dict[str, Any]]]] = None,
        mcp_servers: Optional[List[Union[MCPServerConfig, Dict[str, Any]]]] = None,
        code_execution: Optional[bool] = None,
        tools: Optional[Union["DeepResearchTools", Dict[str, Any]]] = None,
        previous_reports: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        alert_email: Optional[Union[str, "AlertEmailConfig", Dict[str, str]]] = None,
        brand_collection_id: Optional[str] = None,
        hitl: Optional[Union[HitlConfig, Dict[str, bool]]] = None,
        metadata: Optional[Dict[str, Union[str, int, bool]]] = None,
        workflow_id: Optional[str] = None,
        workflow_params: Optional[Dict[str, Any]] = None,
        workflow_version: Optional[int] = None,
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
            strategy: Natural language strategy for the research (deprecated, use research_strategy instead).
                Counts toward the combined research_strategy/report_format length cap below.
            research_strategy: Natural language strategy to guide the research phase (methodology, focus areas, depth).
                Combined character length of research_strategy (or its legacy alias strategy) and report_format
                must not exceed 15,000 characters; exceeding this returns a 400-equivalent error.
            report_format: Natural language instructions for the output format (structure, tone, length, style).
                Has highest priority — overrides default formatting.
                Combined character length of research_strategy (or its legacy alias strategy) and report_format
                must not exceed 15,000 characters; exceeding this returns a 400-equivalent error.
            search: Search configuration (type, sources, dates, category).
                   Can be a SearchConfig object or dict with search parameters:
                   - search_type: "all" (default), "web", or "proprietary"
                   - included_sources: List of source types to include ("web", "academic", "finance",
                     "patent", "transportation", "politics", "legal")
                   - excluded_sources: List of source types to exclude
                   - start_date: Start date filter in ISO format (YYYY-MM-DD), e.g., "2024-01-01"
                   - end_date: End date filter in ISO format (YYYY-MM-DD), e.g., "2024-12-31"
                   - historical_cache: When True and a date range is set, searches return the
                     newest cached snapshot inside the range instead of the latest crawl.
                     Locked for the whole research run — the agent cannot toggle it mid-research.
                   - category: Category filter for results
            urls: URLs to extract and analyze
            files: File attachments (PDFs, images)
            deliverables: Additional file outputs to generate (CSV, Excel, PowerPoint, Word, PDF). Max 10.
                         Can be simple strings or Deliverable objects with detailed configuration.
            mcp_servers: MCP server configurations for custom tools
            code_execution: Enable/disable code execution (deprecated, use tools parameter instead)
            tools: Tools configuration. Controls which optional tools the research agent can use.
                  Available tools: code_execution, screenshots, browser_use.
                  Each tool accepts a boolean or an object with `enabled` (bool) and `max_calls` (int).
                  max_calls can only lower the system default, not raise it.
                  System defaults: browser_use=5, screenshots=15, code_execution=10.
                  If both tools and code_execution are provided, tools takes precedence.
            previous_reports: Previous report IDs for context (max 3)
            webhook_url: HTTPS webhook URL for completion notification
            alert_email: Email for completion alerts. Can be a string (email address) or
                        a dict/AlertEmailConfig with 'email' and optional 'custom_url'.
                        custom_url must contain {id} which is replaced with the task ID.
            brand_collection_id: Brand collection to apply to all deliverables
            hitl: Human-in-the-loop configuration. Enable checkpoints that pause execution
                at key decision points. Available checkpoints:
                - planning_questions: Clarifying questions before research
                - plan_review: Review the research plan
                - source_review: Filter sources by domain after research
                - outline_review: Review the report outline
                Not available for batch requests.
            metadata: Custom metadata (key-value pairs)
            workflow_id: Slug of a workflow to run (see client.workflows.list()).
                        The workflow's template supplies the prompt, strategy,
                        report format, deliverables, and mode. Mutually exclusive
                        with query/input/research_strategy/report_format.
                        Every other parameter on this method still applies to a
                        workflow run, and a value passed here overrides the
                        template's — except tools, which is merged with it.
            workflow_params: Values for the workflow's variables. Keys must match
                        the workflow's declared variables; read them from
                        client.workflows.get(slug).workflow.variables, since they
                        differ per workflow.
            workflow_version: Specific workflow version to run (defaults to current)

        Returns:
            DeepResearchCreateResponse with task ID and status
        """
        try:
            # Client-side guard mirroring the server's hard cap so callers get
            # an identical error without a round-trip. The server reads
            # research_strategy ?? strategy, so mirror that precedence here and
            # reuse the API's exact 400 message.
            effective_strategy = (
                research_strategy if research_strategy is not None else strategy
            )
            combined_strategy_format_length = len(effective_strategy or "") + len(
                report_format or ""
            )
            if (
                combined_strategy_format_length
                > MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH
            ):
                return DeepResearchCreateResponse(
                    success=False,
                    error=f"research_strategy and report_format combined length ({combined_strategy_format_length}) exceeds 15,000 character limit",
                )

            # Determine which field to use (prefer query over input)
            research_query = query if query else input

            # Workflow runs: the template supplies the freeform fields
            if workflow_id:
                if research_query or strategy or research_strategy or report_format:
                    return DeepResearchCreateResponse(
                        success=False,
                        error="workflow_id is mutually exclusive with query/input/research_strategy/report_format - the workflow template supplies those fields",
                    )
                if files:
                    for i, f in enumerate(files):
                        ctx = (
                            f.context
                            if isinstance(f, FileAttachment)
                            else (f.get("context") if isinstance(f, dict) else None)
                        )
                        if ctx and len(ctx) > 10000:
                            return DeepResearchCreateResponse(
                                success=False,
                                error=f"files[{i}].context exceeds 10,000 character limit ({len(ctx)} characters)",
                            )

                payload: Dict[str, Any] = {"workflow_id": workflow_id}
                if workflow_params is not None:
                    payload["workflow_params"] = workflow_params
                if workflow_version is not None:
                    payload["workflow_version"] = workflow_version
                # Only send mode/output_formats when explicitly set so the
                # workflow's recommended defaults apply otherwise
                explicit_mode = mode if mode is not None else model
                if explicit_mode is not None:
                    payload["mode"] = (
                        "standard" if explicit_mode == "lite" else explicit_mode
                    )
                if output_formats:
                    payload["output_formats"] = output_formats

                # Per-run options are as valid on a workflow run as on a
                # freeform one — the template only supplies the freeform fields.
                payload.update(
                    self._build_shared_fields(
                        search=search,
                        urls=urls,
                        files=files,
                        deliverables=deliverables,
                        mcp_servers=mcp_servers,
                        previous_reports=previous_reports,
                        webhook_url=webhook_url,
                        alert_email=alert_email,
                        brand_collection_id=brand_collection_id,
                        metadata=metadata,
                        hitl=hitl,
                        tools=tools,
                        code_execution=code_execution,
                    )
                )

                response = self._session.post(
                    f"{self._base_url}/deepresearch/tasks",
                    json=payload,
                )
                data = response.json()

                if not response.ok:
                    return DeepResearchCreateResponse(
                        success=False,
                        error=_error_message(data, response.status_code),
                    )

                data.pop("success", None)
                return DeepResearchCreateResponse(success=True, **data)

            # Validation
            if not research_query or not research_query.strip():
                return DeepResearchCreateResponse(
                    success=False,
                    error="'query' is required and cannot be empty",
                )

            if len(research_query) > 25000:
                return DeepResearchCreateResponse(
                    success=False,
                    error=f"query exceeds 25,000 character limit ({len(research_query)} characters)",
                )

            if files:
                for i, f in enumerate(files):
                    ctx = f.context if isinstance(f, FileAttachment) else (f.get("context") if isinstance(f, dict) else None)
                    if ctx and len(ctx) > 10000:
                        return DeepResearchCreateResponse(
                            success=False,
                            error=f"files[{i}].context exceeds 10,000 character limit ({len(ctx)} characters)",
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
            }

            # Also send input if it was provided (for backward compatibility with older API versions)
            if input:
                payload["input"] = input
            # Also send model if it was explicitly provided (for backward compatibility)
            if model is not None:
                payload["model"] = model if model != "lite" else "standard"

            # Freeform-only fields — a workflow template supplies these instead
            if strategy:
                payload["strategy"] = strategy
            if research_strategy:
                payload["research_strategy"] = research_strategy
            if report_format:
                payload["report_format"] = report_format

            payload.update(
                self._build_shared_fields(
                    search=search,
                    urls=urls,
                    files=files,
                    deliverables=deliverables,
                    mcp_servers=mcp_servers,
                    previous_reports=previous_reports,
                    webhook_url=webhook_url,
                    alert_email=alert_email,
                    brand_collection_id=brand_collection_id,
                    metadata=metadata,
                    hitl=hitl,
                    tools=tools,
                    code_execution=code_execution,
                )
            )

            response = self._session.post(
                f"{self._base_url}/deepresearch/tasks",
                json=payload,
            )

            data = response.json()

            if not response.ok:
                return DeepResearchCreateResponse(
                    success=False,
                    error=_error_message(data, response.status_code),
                )

            data.pop("success", None)
            return DeepResearchCreateResponse(success=True, **data)

        except Exception as e:
            return DeepResearchCreateResponse(
                success=False,
                error=str(e),
            )

    def status(self, task_id: str, max_attempts: int = 5) -> DeepResearchStatusResponse:
        """
        Get the status of a deep research task.

        The status endpoint is idempotent and built to be polled, so transient
        failures are retried with exponential backoff + jitter instead of being
        reported as task failures. Treated as transient (and retried):
        connection errors and timeouts, HTTP 429/5xx (e.g. an ALB 502 gateway
        page), and non-JSON or empty response bodies. Only a definitive error
        response (a 4xx other than 429 carrying a JSON error) is returned as a
        failure.

        If the endpoint stays unreachable across every attempt, the result has
        ``success=False`` and ``unreachable=True`` — this means "couldn't read
        status", which is retryable and distinct from "the task failed". The
        completed report may still be retrievable.

        Args:
            task_id: Task ID to check
            max_attempts: Attempts before giving up as unreachable (default: 5)

        Returns:
            DeepResearchStatusResponse with current status
        """
        url = f"{self._base_url}/deepresearch/tasks/{task_id}/status"
        last_error = "status endpoint unreachable"

        for attempt in range(max_attempts):
            transient = True
            try:
                response = self._session.get(url)

                if response.status_code in _TRANSIENT_STATUS_CODES:
                    # Gateway/rate-limit/server blip — the task is unaffected.
                    last_error = f"HTTP {response.status_code}"
                else:
                    # An HTML 502 page or an empty body is a gateway artifact,
                    # not the task's real status. Guard before parsing so we
                    # never conflate a bad body with a failed task.
                    content_type = response.headers.get("content-type", "")
                    if (
                        "application/json" not in content_type.lower()
                        or not response.text.strip()
                    ):
                        last_error = (
                            f"non-JSON/empty status response (HTTP "
                            f"{response.status_code}, content-type: "
                            f"{content_type or 'none'})"
                        )
                    else:
                        data = response.json()
                        if not response.ok:
                            # Definitive error response (e.g. 4xx) — terminal.
                            return DeepResearchStatusResponse(
                                success=False,
                                error=data.get(
                                    "error", f"HTTP Error: {response.status_code}"
                                ),
                            )
                        data.pop("success", None)
                        return DeepResearchStatusResponse(success=True, **data)

            except (requests.exceptions.RequestException, ValueError) as e:
                # Connection errors, timeouts, and JSON decode errors are all
                # transient drops of a single poll.
                last_error = str(e) or e.__class__.__name__

            if transient and attempt < max_attempts - 1:
                # Exponential backoff capped at 30s, with jitter to avoid
                # synchronised retries hammering a recovering gateway.
                time.sleep(min(2 ** attempt, 30) + random.random())

        return DeepResearchStatusResponse(
            success=False,
            unreachable=True,
            error=(
                f"Status endpoint unreachable after {max_attempts} attempts: "
                f"{last_error}"
            ),
        )

    def wait(
        self,
        task_id: str,
        poll_interval: int = 5,
        max_wait_time: int = 7200,
        on_progress: Optional[Callable[[DeepResearchStatusResponse], None]] = None,
        on_interaction: Optional[Callable[[Interaction], Optional[Dict[str, Any]]]] = None,
    ) -> DeepResearchStatusResponse:
        """
        Wait for a task to complete with automatic polling.

        Args:
            task_id: Task ID to wait for
            poll_interval: Seconds between polls (default: 5)
            max_wait_time: Maximum wait time in seconds (default: 7200)
            on_progress: Callback for progress updates
            on_interaction: Callback for HITL checkpoints. Receives the Interaction
                object and should return a response dict to submit, or None to skip.
                When a response is returned, it is automatically submitted via respond()
                and polling continues.

        Returns:
            Final task status

        Raises:
            TimeoutError: If max_wait_time is exceeded (including while the
                status endpoint stays unreachable)
            ValueError: If task fails or is cancelled, or status returns a
                definitive (non-transient) error
        """
        start_time = time.time()

        while True:
            status = self.status(task_id)

            if not status.success:
                # A transiently unreachable status endpoint is not a task
                # failure — keep polling within max_wait_time, since the task
                # may well be running (or already completed) server-side.
                if status.unreachable:
                    elapsed = time.time() - start_time
                    if elapsed > max_wait_time:
                        raise TimeoutError(
                            f"Status endpoint unreachable for {max_wait_time} "
                            f"seconds: {status.error}"
                        )
                    time.sleep(poll_interval)
                    continue
                raise ValueError(f"Failed to get status: {status.error}")

            # Notify progress callback
            if on_progress:
                on_progress(status)

            # HITL checkpoint handling
            if status.status in (DeepResearchStatus.AWAITING_INPUT, DeepResearchStatus.PAUSED) and status.interaction:
                if on_interaction:
                    response = on_interaction(status.interaction)
                    if response:
                        self.respond(task_id, status.interaction.interaction_id, response)
                        continue

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

            response = self._session.get(
                f"{self._base_url}/deepresearch/list",
                params=params,
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

            response = self._session.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/update",
                json={"instruction": instruction},
            )

            data = response.json()

            if not response.ok:
                return DeepResearchUpdateResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            data.pop("success", None)
            return DeepResearchUpdateResponse(success=True, **data)

        except Exception as e:
            return DeepResearchUpdateResponse(
                success=False,
                error=str(e),
            )

    def respond(
        self, task_id: str, interaction_id: str, response: Dict[str, Any]
    ) -> DeepResearchRespondResponse:
        """
        Respond to a HITL checkpoint.

        When a task is in 'awaiting_input' or 'paused' status, call this method
        with the interaction_id from the task's interaction field and the appropriate
        response data for the checkpoint type.

        Args:
            task_id: Task ID to respond to
            interaction_id: The interaction_id from the task's interaction field
            response: Response data matching the checkpoint type:
                - planning_questions: {"answers": [{"question": str, "answer": str}]}
                - plan_review: {"approved": bool, "modifications": str (optional)}
                - source_review: {"included_domains": [str], "excluded_domains": [str]}
                - outline_review: {"approved": bool, "modifications": str (optional)}

        Returns:
            DeepResearchRespondResponse with updated status
        """
        try:
            payload = {
                "interaction_id": interaction_id,
                "response": response,
            }

            resp = self._session.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/respond",
                json=payload,
            )

            data = resp.json()

            if not resp.ok:
                return DeepResearchRespondResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {resp.status_code}"),
                )

            data.pop("success", None)
            return DeepResearchRespondResponse(success=True, **data)

        except Exception as e:
            return DeepResearchRespondResponse(
                success=False,
                error=str(e),
            )

    def respond_planning_questions(
        self,
        task_id: str,
        interaction_id: str,
        answers: List[tuple],
    ) -> DeepResearchRespondResponse:
        """
        Convenience method to respond to a planning_questions checkpoint.

        Args:
            task_id: Task ID
            interaction_id: The interaction_id from the checkpoint
            answers: List of (question, answer) tuples

        Returns:
            DeepResearchRespondResponse
        """
        return self.respond(task_id, interaction_id, {
            "answers": [{"question": q, "answer": a} for q, a in answers]
        })

    def approve_plan(
        self,
        task_id: str,
        interaction_id: str,
        modifications: Optional[str] = None,
    ) -> DeepResearchRespondResponse:
        """
        Convenience method to approve (or request modifications to) a plan_review checkpoint.

        Args:
            task_id: Task ID
            interaction_id: The interaction_id from the checkpoint
            modifications: Optional modification instructions (sets approved=False)

        Returns:
            DeepResearchRespondResponse
        """
        resp: Dict[str, Any] = {"approved": True}
        if modifications:
            resp["approved"] = False
            resp["modifications"] = modifications
        return self.respond(task_id, interaction_id, resp)

    def respond_source_review(
        self,
        task_id: str,
        interaction_id: str,
        included_domains: Optional[List[str]] = None,
        excluded_domains: Optional[List[str]] = None,
    ) -> DeepResearchRespondResponse:
        """
        Convenience method to respond to a source_review checkpoint.

        Args:
            task_id: Task ID
            interaction_id: The interaction_id from the checkpoint
            included_domains: Domains to include (empty list = accept AI recommendations)
            excluded_domains: Domains to exclude (empty list = accept AI recommendations)

        Returns:
            DeepResearchRespondResponse
        """
        return self.respond(task_id, interaction_id, {
            "included_domains": included_domains or [],
            "excluded_domains": excluded_domains or [],
        })

    def approve_outline(
        self,
        task_id: str,
        interaction_id: str,
        modifications: Optional[str] = None,
    ) -> DeepResearchRespondResponse:
        """
        Convenience method to approve (or request modifications to) an outline_review checkpoint.

        Args:
            task_id: Task ID
            interaction_id: The interaction_id from the checkpoint
            modifications: Optional modification instructions (sets approved=False)

        Returns:
            DeepResearchRespondResponse
        """
        resp: Dict[str, Any] = {"approved": True}
        if modifications:
            resp["approved"] = False
            resp["modifications"] = modifications
        return self.respond(task_id, interaction_id, resp)

    def cancel(self, task_id: str) -> DeepResearchCancelResponse:
        """
        Cancel a running task.

        Args:
            task_id: Task ID to cancel

        Returns:
            DeepResearchCancelResponse
        """
        try:
            response = self._session.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/cancel",
                json={},
            )

            data = response.json()

            if not response.ok:
                return DeepResearchCancelResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            data.pop("success", None)
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
            response = self._session.delete(
                f"{self._base_url}/deepresearch/tasks/{task_id}/delete",
            )

            data = response.json()

            if not response.ok:
                return DeepResearchDeleteResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            data.pop("success", None)
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

            if token:
                # Token is passed as query parameter; strip auth headers for this request
                sdk_headers = {
                    k: v
                    for k, v in self._headers.items()
                    if k.startswith("X-Valyu-") or k == "User-Agent"
                }
                url += f"?token={token}"
                response = self._session.get(url, headers=sdk_headers)
            else:
                response = self._session.get(url)

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
            response = self._session.post(
                f"{self._base_url}/deepresearch/tasks/{task_id}/public",
                json={"public": is_public},
            )

            data = response.json()

            if not response.ok:
                return DeepResearchTogglePublicResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            data.pop("success", None)
            return DeepResearchTogglePublicResponse(success=True, **data)

        except Exception as e:
            return DeepResearchTogglePublicResponse(
                success=False,
                error=str(e),
            )
