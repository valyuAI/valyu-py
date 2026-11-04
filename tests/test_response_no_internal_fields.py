"""Tests that response models do not expose internal storage and routing fields."""

from valyu.types.deepresearch import (
    DeepResearchBatch,
    DeepResearchSource,
    DeliverableResult,
)


def test_batch_has_no_internal_billing_or_auth_fields():
    fields = set(DeepResearchBatch.model_fields)
    for name in ("api_key_id", "credit_id", "organisation_id"):
        assert name not in fields


def test_source_has_no_internal_routing_fields():
    fields = set(DeepResearchSource.model_fields)
    for name in ("org_id", "source_id", "doc_id"):
        assert name not in fields


def test_deliverable_has_no_storage_key():
    assert "s3_key" not in set(DeliverableResult.model_fields)


def test_extra_internal_keys_in_a_response_are_dropped():
    source = DeepResearchSource.model_validate(
        {"title": "t", "url": "https://example.test", "org_id": "o", "doc_id": 1, "source_id": 2}
    )
    assert not source.model_dump().keys() & {"org_id", "doc_id", "source_id"}

    deliverable = DeliverableResult.model_validate(
        {"id": "d", "request": "r", "type": "csv", "status": "completed", "title": "t", "s3_key": "k"}
    )
    assert "s3_key" not in deliverable.model_dump()

    batch = DeepResearchBatch.model_validate(
        {
            "batch_id": "b",
            "status": "processing",
            "mode": "standard",
            "counts": {"total": 1, "queued": 1, "running": 0, "completed": 0, "failed": 0, "cancelled": 0},
            "cost": 0.0,
            "created_at": "2026-01-01T00:00:00Z",
            "api_key_id": "a",
            "credit_id": "c",
            "organisation_id": "o",
        }
    )
    assert not batch.model_dump().keys() & {"api_key_id", "credit_id", "organisation_id"}
