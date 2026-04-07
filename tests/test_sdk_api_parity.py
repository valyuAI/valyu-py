"""Tests that internal fields are not exposed in public SDK models."""

from valyu.types.deepresearch import DeliverableResult


def test_deliverable_result_s3_key_not_exposed():
    """s3_key must not appear in DeliverableResult model fields."""
    assert "s3_key" not in DeliverableResult.model_fields


def test_deliverable_result_ignores_s3_key_from_api():
    """DeliverableResult constructed from API data that includes s3_key must not expose it."""
    data = {
        "id": "del_123",
        "request": "Generate a PDF report",
        "type": "pdf",
        "status": "completed",
        "title": "report.pdf",
        "url": "https://cdn.valyu.ai/reports/report.pdf?token=abc",
        "s3_key": "org/tasks/abc123/report.pdf",
        "created_at": 1712345678,
    }
    result = DeliverableResult(**data)
    assert not hasattr(result, "s3_key") or getattr(result, "s3_key", None) is None
    serialized = result.model_dump()
    assert "s3_key" not in serialized
