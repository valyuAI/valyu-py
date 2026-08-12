"""
Async Valyu client for high-concurrency applications.

Built on ``httpx.AsyncClient`` so many calls can be in flight concurrently
inside a single event loop without thread overhead or per-request TLS
handshakes. Currently exposes ``search`` and ``contents`` (plus the two
``contents`` job helpers); other endpoints remain on the sync client for
now.

Typical usage::

    import asyncio
    from valyu import AsyncValyu

    async def main():
        async with AsyncValyu() as valyu:
            response = await valyu.search(
                "Real options valuation binomial Monte Carlo",
                included_sources=["wiley/wiley-finance-papers"],
                max_num_results=10,
            )
            print(response)

    asyncio.run(main())
"""
import asyncio
import os
import platform
import time
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Type, Union

import httpx

from valyu import __version__
from valyu._request_builders import (
    build_contents_payload,
    build_search_payload,
    validate_contents_inputs,
    validate_search_inputs,
)
from valyu.types.contents import (
    ContentsJobCreateResponse,
    ContentsJobStatus,
    ContentsResponse,
    ContentsResponseLength,
    ExtractEffort,
)
from valyu.types.response import ResultsBySource, SearchResponse, SearchType


def _format_exception(exc: BaseException) -> str:
    """Return a non-empty human-readable description of an exception.

    Some exception classes (notably ``httpx.TimeoutException``) have an empty
    ``str`` representation, so fall back to the class name when that happens.
    """
    message = str(exc).strip()
    if message:
        return message
    return type(exc).__name__


class AsyncValyu:
    """Async Valyu client backed by ``httpx.AsyncClient``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.valyu.ai/v1",
        max_connections: int = 100,
        max_keepalive_connections: Optional[int] = None,
        timeout: float = 600.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize the async Valyu client.

        Args:
            api_key (Optional[str]): API key. Falls back to ``VALYU_API_KEY``
                env var.
            base_url (str): Base URL of the Valyu API.
            max_connections (int): Maximum simultaneous connections the
                underlying HTTP pool will open. Only used when
                ``http_client`` is not provided. Defaults to 100.
            max_keepalive_connections (Optional[int]): Number of idle
                connections kept alive for reuse. Defaults to
                ``max(20, max_connections // 5)``.
            timeout (float): Per-request timeout in seconds. Applies to
                the default client; ignored when ``http_client`` is passed.
            http_client (Optional[httpx.AsyncClient]): Pre-configured
                ``httpx.AsyncClient`` to use. When provided, the client is
                used as-is and is NOT closed by ``aclose()`` — ownership
                stays with the caller.
        """
        if api_key is None:
            api_key = os.getenv("VALYU_API_KEY")
            if not api_key:
                raise ValueError("VALYU_API_KEY is not set")

        # Normalise base_url so joining with a leading-slash path never
        # produces "//" in the URL.
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "User-Agent": f"valyu-py/{__version__} python/{platform.python_version()}",
            "X-Valyu-SDK": "valyu-py-async",
            "X-Valyu-SDK-Version": __version__,
        }

        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            if max_keepalive_connections is None:
                max_keepalive_connections = max(20, max_connections // 5)
            limits = httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            )
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers,
                limits=limits,
                timeout=timeout,
            )
            self._owns_client = True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        """Close the underlying HTTP client, if this instance owns it."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncValyu":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    # Internal request helpers
    # ------------------------------------------------------------------

    async def _post(self, path: str, payload: Dict[str, Any]) -> httpx.Response:
        if self._owns_client:
            return await self._client.post(path, json=payload)
        # External client: base_url may not be set on it, so send full URL.
        return await self._client.post(
            f"{self.base_url}{path}", json=payload, headers=self._headers
        )

    async def _get(self, path: str) -> httpx.Response:
        if self._owns_client:
            return await self._client.get(path)
        return await self._client.get(f"{self.base_url}{path}", headers=self._headers)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        search_type: SearchType = "all",
        max_num_results: int = 10,
        is_tool_call: Optional[bool] = True,
        relevance_threshold: Optional[float] = 0.5,
        max_price: Optional[int] = None,
        included_sources: Optional[List[str]] = None,
        excluded_sources: Optional[List[str]] = None,
        country_code: Optional[str] = None,
        response_length: Optional[ContentsResponseLength] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fast_mode: bool = False,
        url_only: bool = False,
        source_biases: Optional[Dict[str, int]] = None,
        instructions: Optional[str] = None,
        historical_cache: Optional[bool] = None,
        include_abstracts: bool = False,
    ) -> Optional[SearchResponse]:
        """
        Async version of ``Valyu.search``. See :py:meth:`Valyu.search`
        for full parameter documentation — arguments and semantics are
        identical.
        """
        try:
            invalid = validate_search_inputs(
                query=query,
                included_sources=included_sources,
                excluded_sources=excluded_sources,
                country_code=country_code,
            )
            if invalid is not None:
                return invalid

            payload = build_search_payload(
                query=query,
                search_type=search_type,
                max_num_results=max_num_results,
                is_tool_call=is_tool_call,
                relevance_threshold=relevance_threshold,
                max_price=max_price,
                included_sources=included_sources,
                excluded_sources=excluded_sources,
                country_code=country_code,
                response_length=response_length,
                category=category,
                start_date=start_date,
                end_date=end_date,
                fast_mode=fast_mode,
                url_only=url_only,
                source_biases=source_biases,
                instructions=instructions,
                historical_cache=historical_cache,
                include_abstracts=include_abstracts,
            )

            response = await self._post("/search", payload)
            data = response.json()

            if not (200 <= response.status_code < 400):
                return SearchResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                    tx_id=data.get("tx_id", f"error-{response.status_code}"),
                    query=query,
                    results=[],
                    results_by_source=ResultsBySource(web=0, proprietary=0),
                    total_deduction_dollars=0.0,
                    total_characters=0,
                )

            if not data.get("results") and data.get("error"):
                return SearchResponse(
                    success=True,
                    error=data.get("error"),
                    tx_id=data.get("tx_id", "0x0"),
                    query=data.get("query", query),
                    results=[],
                    results_by_source=data.get(
                        "results_by_source",
                        ResultsBySource(web=0, proprietary=0),
                    ),
                    total_deduction_dollars=data.get("total_deduction_dollars", 0.0),
                    total_characters=data.get("total_characters", 0),
                )

            return SearchResponse(**data)
        except Exception as exc:
            message = _format_exception(exc)
            return SearchResponse(
                success=False,
                error=message,
                tx_id="exception-" + str(hash(message))[:8],
                query=query,
                results=[],
                results_by_source=ResultsBySource(web=0, proprietary=0),
                total_deduction_dollars=0.0,
                total_characters=0,
            )

    # ------------------------------------------------------------------
    # Contents
    # ------------------------------------------------------------------

    async def contents(
        self,
        urls: List[str],
        summary: Optional[Union[bool, str, Dict[str, Any]]] = None,
        extract_effort: Optional[ExtractEffort] = None,
        response_length: Optional[ContentsResponseLength] = None,
        max_price_dollars: Optional[float] = None,
        screenshot: bool = False,
        async_mode: bool = False,
        webhook_url: Optional[str] = None,
        wait: bool = False,
        poll_interval: int = 5,
        max_wait_time: int = 3600,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        historical_cache: Optional[bool] = None,
    ) -> Optional[Union[ContentsResponse, ContentsJobCreateResponse, ContentsJobStatus]]:
        """
        Async version of ``Valyu.contents``. Arguments and semantics
        identical to :py:meth:`Valyu.contents`.
        """
        try:
            ok, err = validate_contents_inputs(urls, async_mode)
            if not ok:
                return ContentsResponse(
                    success=False,
                    error=err,
                    tx_id="error-max-urls" if len(urls) > 50 else "error-async-required",
                    urls_requested=len(urls),
                    urls_processed=0,
                    urls_failed=len(urls),
                    results=[],
                    total_cost_dollars=0.0,
                    total_characters=0,
                )

            payload = build_contents_payload(
                urls=urls,
                summary=summary,
                extract_effort=extract_effort,
                response_length=response_length,
                max_price_dollars=max_price_dollars,
                screenshot=screenshot,
                async_mode=async_mode,
                webhook_url=webhook_url,
                start_date=start_date,
                end_date=end_date,
                historical_cache=historical_cache,
            )

            response = await self._post("/contents", payload)
            data = response.json()

            if not (200 <= response.status_code < 400):
                return ContentsResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                    tx_id=data.get("tx_id", f"error-{response.status_code}"),
                    urls_requested=len(urls),
                    urls_processed=0,
                    urls_failed=len(urls),
                    results=[],
                    total_cost_dollars=0.0,
                    total_characters=0,
                )

            if response.status_code == 202:
                job = ContentsJobCreateResponse(**data)
                if wait and job.success:
                    return await self.wait_for_contents_job(
                        job.job_id,
                        poll_interval=poll_interval,
                        max_wait_time=max_wait_time,
                    )
                return job

            return ContentsResponse(**data)
        except Exception as exc:
            message = _format_exception(exc)
            return ContentsResponse(
                success=False,
                error=message,
                tx_id="exception-" + str(hash(message))[:8],
                urls_requested=len(urls),
                urls_processed=0,
                urls_failed=len(urls),
                results=[],
                total_cost_dollars=0.0,
                total_characters=0,
            )

    async def get_contents_job(self, job_id: str) -> ContentsJobStatus:
        """Async version of :py:meth:`Valyu.get_contents_job`."""
        try:
            response = await self._get(f"/contents/jobs/{job_id}")
            data = response.json()

            if not (200 <= response.status_code < 400):
                return ContentsJobStatus(
                    success=False,
                    job_id=job_id,
                    status="failed",
                    urls_total=0,
                    urls_processed=0,
                    urls_failed=0,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                )

            return ContentsJobStatus(**data)
        except Exception as exc:
            return ContentsJobStatus(
                success=False,
                job_id=job_id,
                status="failed",
                urls_total=0,
                urls_processed=0,
                urls_failed=0,
                error=_format_exception(exc),
            )

    async def wait_for_contents_job(
        self,
        job_id: str,
        poll_interval: int = 5,
        max_wait_time: int = 3600,
        on_progress: Optional[Callable[[ContentsJobStatus], None]] = None,
    ) -> ContentsJobStatus:
        """Async version of :py:meth:`Valyu.wait_for_contents_job`."""
        start_time = time.time()
        terminal = ("completed", "partial", "failed")

        while True:
            status = await self.get_contents_job(job_id)

            if not status.success:
                raise ValueError(f"Failed to get job status: {status.error}")

            if on_progress is not None:
                on_progress(status)

            if status.status in terminal:
                return status

            if time.time() - start_time > max_wait_time:
                raise TimeoutError(
                    f"Job did not complete within {max_wait_time} seconds"
                )

            await asyncio.sleep(poll_interval)
