"""SDK API parity and security tests."""

import pytest


def test_kevin_20260401_002_py_internal_types():
    """Internal infrastructure fields must not be exposed in public SDK type definitions."""
    from valyu.types.deepresearch import DeliverableResult, DeepResearchBatch

    # s3_key is an internal storage reference - users should use the signed URL instead
    assert (
        "s3_key" not in DeliverableResult.model_fields
    ), "s3_key is an internal S3 storage key and must not be exposed in DeliverableResult"

    # api_key_id is an internal identifier - must not be exposed to SDK consumers
    assert (
        "api_key_id" not in DeepResearchBatch.model_fields
    ), "api_key_id is an internal field and must not be exposed in DeepResearchBatch"
