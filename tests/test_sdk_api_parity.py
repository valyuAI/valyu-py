"""Tests that SDK response handling does not expose internal API fields to callers."""

from unittest.mock import MagicMock, patch

from valyu import Valyu


def test_py_sdk_data_leak():
    """SDK must not expose internal API fields to callers via SearchResult.metadata.

    The search API may return internal data (cost IDs, routing keys, secrets)
    in the 'metadata' field of each result. The SDK must strip these before
    returning results to callers.
    """
    internal_metadata = {
        "_internal_cost_id": "cost-abc-123",
        "_routing_key": "us-east-1:bucket:key",
        "_provider_secret": "secret-value",
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "tx_id": "tx-test-123",
        "query": "test query",
        "results": [
            {
                "title": "Test Result",
                "url": "https://example.com/test",
                "content": "Test content here",
                "source": "web",
                "price": 0.001,
                "length": 17,
                "metadata": internal_metadata,
            }
        ],
        "results_by_source": {"web": 1, "proprietary": 0},
        "total_deduction_dollars": 0.001,
        "total_characters": 17,
    }

    client = Valyu(api_key="test-key")
    with patch.object(client._session, "post", return_value=mock_response):
        response = client.search("test query")

    assert response is not None
    assert response.success is True
    assert len(response.results) == 1
    result = response.results[0]

    # Internal API data must not be accessible via the SDK response
    exposed_metadata = getattr(result, "metadata", None)
    assert (
        exposed_metadata is None
    ), f"SearchResult.metadata exposes internal API data to callers: {exposed_metadata}"
