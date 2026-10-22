"""
Shared HTTP 429 (rate-limit) handling: the structured detail built from a
429 response, and the retry helper every create-style call reuses.
"""

import asyncio
import time
from typing import Any, Awaitable, Callable, Mapping, Optional, Protocol, TypeVar

from valyu.types.rate_limit import RateLimitDetail, RateLimitInfo

# Used only when a 429 body carries neither `retry_after` nor a `Retry-After`
# header — a conservative wait so a caller still backs off instead of
# retrying immediately.
_DEFAULT_RETRY_AFTER_SECONDS = 1

# Every wait is capped at this many seconds, however long the server's own
# `retry_after`/`Retry-After` asks for, so a single rate-limited call can
# never stall a caller for an unreasonable amount of time.
MAX_RATE_LIMIT_WAIT_SECONDS = 60


class _Response(Protocol):
    """The subset of ``requests.Response``/``httpx.Response`` this module needs."""

    status_code: int
    headers: Mapping[str, str]

    def json(self) -> Any: ...


T = TypeVar("T", bound=_Response)


def _retry_after_from_header(headers: Optional[Mapping[str, str]]) -> Optional[int]:
    """Parse the Retry-After response header (delta-seconds) into whole seconds."""
    if not headers:
        return None
    value = headers.get("Retry-After")
    if value is None:
        return None
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return None


def rate_limit_detail_from_response(
    data: Any, headers: Optional[Mapping[str, str]] = None
) -> RateLimitDetail:
    """
    Build the structured rate-limit detail for a 429 response.

    Call this only once the response status is known to be 429. The body's
    `retry_after` wins; the `Retry-After` HTTP header is the fallback, then a
    1-second default when neither is present. `plan`, `limit`, `upgrade_url`,
    and `contact_url` come only from the richer body shape — an older server
    sending just the generic "Too many requests" message leaves them `None`
    rather than failing.
    """
    if not isinstance(data, dict):
        data = {}

    retry_after = data.get("retry_after")
    if not isinstance(retry_after, (int, float)) or isinstance(retry_after, bool):
        retry_after = _retry_after_from_header(headers)
    if retry_after is None:
        retry_after = _DEFAULT_RETRY_AFTER_SECONDS

    limit_data = data.get("limit")
    limit = RateLimitInfo(**limit_data) if isinstance(limit_data, dict) else None

    return RateLimitDetail(
        retry_after=max(0, int(retry_after)),
        plan=data.get("plan"),
        limit=limit,
        upgrade_url=data.get("upgrade_url"),
        contact_url=data.get("contact_url"),
    )


def _retry_after_seconds(response: Any) -> int:
    """The number of seconds a 429 response asks a caller to wait."""
    try:
        body = response.json()
    except Exception:
        body = None
    return rate_limit_detail_from_response(body, response.headers).retry_after


def send_with_rate_limit_retry(
    send: Callable[[], T],
    max_retries: int,
    sleep: Optional[Callable[[float], None]] = None,
) -> T:
    """
    Call ``send()``, retrying while it answers HTTP 429, up to ``max_retries`` times.

    A 429 means the request was never accepted — nothing was created or
    billed — so retrying it is always safe, unlike retrying after a timeout,
    where whether the request landed server-side is unknown. Each wait
    honours the response's retry hint (its body's `retry_after`, else the
    `Retry-After` header, else a 1-second default), capped at
    `MAX_RATE_LIMIT_WAIT_SECONDS`. ``max_retries=0`` disables retrying
    entirely — the first response is always returned as-is.

    Returns the first non-429 response, or the last 429 response once
    `max_retries` attempts have been used up.
    """
    wait = sleep if sleep is not None else time.sleep
    attempt = 0
    while True:
        response = send()
        if response.status_code != 429 or attempt >= max_retries:
            return response
        wait(min(_retry_after_seconds(response), MAX_RATE_LIMIT_WAIT_SECONDS))
        attempt += 1


async def async_send_with_rate_limit_retry(
    send: Callable[[], Awaitable[T]],
    max_retries: int,
    sleep: Optional[Callable[[float], Awaitable[None]]] = None,
) -> T:
    """Async counterpart of :func:`send_with_rate_limit_retry`. See its docstring."""
    wait = sleep if sleep is not None else asyncio.sleep
    attempt = 0
    while True:
        response = await send()
        if response.status_code != 429 or attempt >= max_retries:
            return response
        await wait(min(_retry_after_seconds(response), MAX_RATE_LIMIT_WAIT_SECONDS))
        attempt += 1
