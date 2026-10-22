"""
Structured detail carried by a 429 (rate-limited) response body.

The API's 429 body looks like::

    {
        "error": "rate_limited",
        "message": "Search rate limit reached: your plan allows 5 requests "
                    "per second. Retry after 2 seconds. Upgrade for 10 "
                    "requests per second: https://platform.valyu.ai/...",
        "retry_after": 2,
        "plan": "Pay-as-you-go",
        "limit": {"endpoint": "search", "requests_per_second": 5},
        "upgrade_url": "https://platform.valyu.ai/user/account/billing?tab=plan"
    }

An enterprise-tier plan that has no higher self-serve plan to offer gets a
``contact_url`` (a sales contact link) instead of ``upgrade_url``. An older
server may still answer with only the generic shape (``error``, ``message``,
``retry_after``) — ``plan``, ``limit``, ``upgrade_url``, and ``contact_url``
are simply absent then, and every field below stays ``None``.
"""

from typing import Optional

from pydantic import BaseModel


class RateLimitInfo(BaseModel):
    """Which endpoint was limited, and the rate its plan allows."""

    endpoint: Optional[str] = None
    requests_per_second: Optional[float] = None


class RateLimitDetail(BaseModel):
    """Structured detail from a 429 response, attached to the SDK's error responses."""

    retry_after: int
    plan: Optional[str] = None
    limit: Optional[RateLimitInfo] = None
    upgrade_url: Optional[str] = None
    contact_url: Optional[str] = None
