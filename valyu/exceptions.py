"""
Public exception types for the Valyu SDK.
"""

from typing import Optional

from valyu.types.rate_limit import RateLimitDetail, RateLimitInfo


class RateLimitError(Exception):
    """
    Raised when a request hits the API's rate limit (HTTP 429).

    Most SDK methods never raise on an API error — they return a response
    model with ``success=False`` and ``error`` set instead (see the
    "Error Handling" section in the README), and expose the same detail
    below as a ``rate_limit`` field on that response. This exception is for
    the handful of call sites that already raise on an HTTP error rather
    than returning one (e.g. ``deepresearch.get_assets``), so a 429 there
    raises a typed error instead of a generic one.
    """

    def __init__(self, message: str, detail: RateLimitDetail):
        super().__init__(message)
        self.message = message
        self.retry_after: int = detail.retry_after
        self.plan: Optional[str] = detail.plan
        self.limit: Optional[RateLimitInfo] = detail.limit
        self.upgrade_url: Optional[str] = detail.upgrade_url
        self.contact_url: Optional[str] = detail.contact_url

    def __str__(self) -> str:
        return self.message


__all__ = ["RateLimitError"]
