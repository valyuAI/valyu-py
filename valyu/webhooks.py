"""
Webhook signature verification for Valyu API.
"""

import hmac
import hashlib
from typing import Union


def verify_contents_webhook(
    payload: Union[bytes, str],
    signature: str,
    timestamp: str,
    secret: str,
) -> bool:
    """
    Verify the X-Webhook-Signature of a Contents API webhook request.

    Store the webhook_secret returned when creating a job with webhook_url,
    then use it to verify incoming webhook requests.

    Args:
        payload: Raw request body (bytes or str).
        signature: X-Webhook-Signature header value (format: sha256={hmac_hex}).
        timestamp: X-Webhook-Timestamp header value (Unix seconds).
        secret: webhook_secret from job creation.

    Returns:
        True if signature is valid.
    """
    body_str = payload.decode() if isinstance(payload, bytes) else payload
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{body_str}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
