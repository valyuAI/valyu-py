"""
Security regression tests for sensitive field exposure in SDK response types.
"""

from valyu.types.deepresearch import DeliverableResult, DeepResearchBatch


def test_kevin_20260401_002():
    """
    KEVIN-20260401-002: internal s3_key and api_key_id must not be exposed
    in Python SDK response types.

    DeliverableResult.s3_key and DeepResearchBatch.api_key_id are internal
    fields that should not appear in serialized output visible to SDK consumers.
    """
    # --- DeliverableResult.s3_key ---
    deliverable = DeliverableResult(
        id="del-123",
        request="Generate a report",
        type="pdf",
        status="completed",
        title="report.pdf",
        url="https://example.com/signed-url",
        s3_key="internal/bucket/path/report.pdf",
        created_at=1700000000,
    )

    dumped = deliverable.model_dump()
    assert (
        "s3_key" not in dumped
    ), "DeliverableResult.s3_key must not be exposed in serialized output"

    json_output = deliverable.model_dump_json()
    assert (
        "s3_key" not in json_output
    ), "DeliverableResult.s3_key must not appear in JSON output"

    # --- DeepResearchBatch.api_key_id ---
    batch = DeepResearchBatch(
        batch_id="batch-456",
        api_key_id="key-internal-789",
        status="open",
        mode="standard",
        counts={
            "total": 0,
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        },
        cost=0.0,
        created_at="2024-01-01T00:00:00.000Z",
    )

    dumped = batch.model_dump()
    assert (
        "api_key_id" not in dumped
    ), "DeepResearchBatch.api_key_id must not be exposed in serialized output"

    json_output = batch.model_dump_json()
    assert (
        "api_key_id" not in json_output
    ), "DeepResearchBatch.api_key_id must not appear in JSON output"
