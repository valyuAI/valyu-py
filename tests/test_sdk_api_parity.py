"""
Tests that SDK response types do not expose internal routing metadata to end users.
"""

from valyu.types.deepresearch import DeepResearchBatch, DeepResearchSource
from valyu.types.response import SearchResult


def test_py_response_no_internal_leak():
    """Ensure SDK response models strip internal routing metadata before returning to users."""
    # DeepResearchBatch must not expose internal billing/auth routing fields
    batch_fields = set(DeepResearchBatch.model_fields)
    assert (
        "api_key_id" not in batch_fields
    ), "api_key_id is internal and must not be exposed"
    assert (
        "credit_id" not in batch_fields
    ), "credit_id is internal and must not be exposed"
    assert (
        "organisation_id" not in batch_fields
    ), "organisation_id is internal and must not be exposed"

    # DeepResearchSource must not expose internal routing identifiers
    source_fields = set(DeepResearchSource.model_fields)
    assert "org_id" not in source_fields, "org_id is internal and must not be exposed"
    assert (
        "source_id" not in source_fields
    ), "source_id is internal and must not be exposed"
    assert "doc_id" not in source_fields, "doc_id is internal and must not be exposed"

    # SearchResult must not expose catch-all internal metadata dict
    result_fields = set(SearchResult.model_fields)
    assert (
        "metadata" not in result_fields
    ), "metadata catch-all dict must not be exposed"
